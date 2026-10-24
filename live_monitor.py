'''
Record 모드의 라디오 오디오(USB 입력)를 맥 출력으로 실시간 전달하는 모듈.
소프트웨어 게인(dB)으로 볼륨을 키울 수 있다.

필요 패키지: pip install sounddevice numpy
'''

import tkinter as tk
from tkinter import ttk

import numpy as np
import sounddevice as sd

# 이어폰 입력 장치를 고를 때 기본 선택에 쓰는 이름 힌트 (소문자)
INPUT_HINTS = ('ic100', 'akg', 'samsung', 'usb-c', 'usb c')


def _device_choices(kind):
    key = 'max_input_channels' if kind == 'input' else 'max_output_channels'
    return [(i, d['name']) for i, d in enumerate(sd.query_devices()) if d[key] > 0]


class LiveMonitor:
    """입력 장치의 소리를 출력 장치로 내보내며 게인을 적용한다."""

    def __init__(self):
        self._stream = None
        self.gain_db = 0.0
        self.xruns = 0        # 시작 직후를 제외한 입력 오버플로/출력 언더플로 횟수
        self._warmup = 0      # 시작 직후 무시할 프레임 수

    @property
    def running(self):
        return self._stream is not None

    def _callback(self, indata, outdata, frames, time, status):
        # 오디오 스레드에서 print는 지연의 원인이 되므로 횟수만 센다.
        if self._warmup > 0:
            self._warmup -= frames
        elif status:
            self.xruns += 1
        gain = 10 ** (self.gain_db / 20)
        in_ch = indata.shape[1]
        out_ch = outdata.shape[1]
        if in_ch == 1:
            # 모노 입력은 모든 출력 채널에 복사
            outdata[:] = np.clip(indata * gain, -1.0, 1.0)
        else:
            outdata.fill(0)
            n = min(in_ch, out_ch)
            outdata[:, :n] = np.clip(indata[:, :n] * gain, -1.0, 1.0)

    def start(self, in_dev, out_dev):
        if self._stream is not None:
            return
        in_info = sd.query_devices(in_dev)
        out_info = sd.query_devices(out_dev)
        self.xruns = 0
        self._warmup = int(in_info['default_samplerate'] * 0.5)
        stream = sd.Stream(
            device=(in_dev, out_dev),
            samplerate=in_info['default_samplerate'],
            channels=(min(2, in_info['max_input_channels']),
                      min(2, out_info['max_output_channels'])),
            dtype='float32',
            latency='high',
            callback=self._callback,
        )
        try:
            stream.start()
        except Exception:
            stream.close()
            raise
        self._stream = stream

    def stop(self):
        stream, self._stream = self._stream, None
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception as e:
                print(f"Failed to stop stream: {e}")


class LiveFrame(tk.Frame):
    """메인 창에 grid로 붙이는 라이브 청취 제어부.

    is_record_mode()가 참일 때만 시작할 수 있다.
    """

    def __init__(self, master, is_record_mode):
        super().__init__(master)
        self._is_record_mode = is_record_mode
        self._monitor = LiveMonitor()
        self._poll_id = None
        inputs = _device_choices('input')
        outputs = _device_choices('output')
        in_names = [f"{i}: {n}" for i, n in inputs]
        out_names = [f"{i}: {n}" for i, n in outputs]

        self._in_var = tk.StringVar(self)
        self._out_var = tk.StringVar(self)
        self._gain_var = tk.DoubleVar(self, value=0.0)
        self._status_var = tk.StringVar(self, value="Record 후 Listen")

        # 기본 선택: 입력은 이름 힌트가 맞는 장치, 출력은 시스템 기본 출력
        for text, (i, n) in zip(in_names, inputs):
            if any(h in n.lower() for h in INPUT_HINTS):
                self._in_var.set(text)
                break
        default_out = sd.default.device[1]
        for text, (i, n) in zip(out_names, outputs):
            if i == default_out:
                self._out_var.set(text)
                break

        self._btn = tk.Button(self, text="Listen", command=self._toggle)
        self._btn.grid(row=0, column=0, sticky="ew")
        tk.Scale(self, from_=0, to=30, orient='horizontal', resolution=1,
                 variable=self._gain_var, command=self._on_gain,
                 label="Gain (dB)").grid(row=0, column=1, sticky="ew")
        tk.Label(self, textvariable=self._status_var, width=18,
                 anchor='w').grid(row=0, column=2, sticky="ew", padx=4)

        ttk.Combobox(self, textvariable=self._in_var, values=in_names,
                     state='readonly').grid(row=1, column=0, columnspan=3,
                                            sticky="ew", pady=(4, 0))
        ttk.Combobox(self, textvariable=self._out_var, values=out_names,
                     state='readonly').grid(row=2, column=0, columnspan=3,
                                            sticky="ew", pady=(2, 0))
        self.columnconfigure(1, weight=1)

    def _alive(self):
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _set_status(self, text):
        if self._alive():
            self._status_var.set(text)

    @staticmethod
    def _parse(text):
        if not text:
            raise ValueError("장치를 선택하세요")
        return int(text.split(':', 1)[0])

    def _on_gain(self, value):
        self._monitor.gain_db = float(value)

    def _toggle(self):
        if self._monitor.running:
            self.stop()
            return
        if not self._is_record_mode():
            # Record 모드가 아니면 입력이 이어폰 마이크라 하울링이 날 수 있다.
            self._set_status("Record 모드에서만 가능")
            return
        try:
            in_dev = self._parse(self._in_var.get())
            out_dev = self._parse(self._out_var.get())
            self._monitor.gain_db = float(self._gain_var.get())
            self._monitor.start(in_dev, out_dev)
        except Exception as e:
            self._set_status(f"시작 실패: {e}")
            print(f"Live listen failed: {e}")
            return
        self._btn['text'] = "Stop"
        self._set_status("재생 중")
        self._schedule_poll()

    def _schedule_poll(self):
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
        self._poll_id = self.after(1000, self._poll)

    def _poll(self):
        self._poll_id = None
        if not self._monitor.running or not self._alive():
            return
        n = self._monitor.xruns
        self._status_var.set("재생 중" if n == 0 else f"재생 중 (끊김 {n})")
        self._schedule_poll()

    def stop(self):
        # 실행 중일 때만 정지하고 표시를 되돌린다(다른 상태 메시지는 건드리지 않음).
        if not self._monitor.running:
            return
        if self._poll_id is not None:
            self.after_cancel(self._poll_id)
            self._poll_id = None
        self._monitor.stop()
        if self._alive():
            self._btn['text'] = "Listen"
            self._status_var.set("정지됨")
