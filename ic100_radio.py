#!/usr/bin/env python

import ic100_radio_gui
import tkinter as tk
import besfm
import time
import usb.core

try:
    from live_monitor import LiveFrame
except (ImportError, OSError) as e:  # sounddevice/numpy/PortAudio 문제 시 라이브 청취 없이 동작
    LiveFrame = None
    print(f"Live listen disabled: {e}")

'''
GUI FM radio control program
'''

class MainApp(ic100_radio_gui.MainApp):
    def __init__(self, master):
        super().__init__(master)
        dev = usb.core.find(
            idVendor=0x04e8,
            custom_match=lambda x: x.idProduct in [0xa054, 0xa059, 0xa05b]
        )
        if dev is None:
            print("Device not found. Quitting.")
            quit()
        self.fm = besfm.BesFM(dev)
        self.update_power()
        self.volume = tk.IntVar(master, value=6)
        self.freq = 9150
        self.vol_slider['variable'] = self.volume
        self.btn_freq_up_1m['text'] = "+1M"
        self.btn_freq_down_1m['text'] = "-1M"
        self.btn_freq_up_500k['text'] = "+500K"
        self.btn_freq_down_500k['text'] = "-500K"
        self.btn_freq_up_100k['text'] = "+100K"
        self.btn_freq_down_100k['text'] = "-100K"
        self.btn_record['text'] = "Record"
        if self.power or self.record:
            self.update_frequency()
            self.update_volume()
            self.update_mute()

        # 종료 시 라디오 전원 끄기 (창 닫기 / macOS Cmd+Q)
        self._tk_root = master
        self._shut_down = False
        master.protocol("WM_DELETE_WINDOW", self.on_close)
        try:
            master.createcommand('::tk::mac::Quit', self.on_close)
        except tk.TclError:
            pass

        # Record 모드의 라디오 오디오를 맥 출력으로 듣는 제어부 (메인 창 3~5행)
        self._live = None
        if LiveFrame is not None:
            try:
                self._live = LiveFrame(master, lambda: self.record)
                self._live.grid(row=3, column=0, columnspan=6,
                                sticky="ew", padx=4, pady=4)
            except Exception as e:
                print(f"Live listen disabled: {e}")

    def shutdown(self):
        # 라디오가 켜져 있으면 끈다. 여러 번 호출해도 한 번만 실행된다.
        if self._shut_down:
            return
        self._shut_down = True
        if getattr(self, '_live', None) is not None:
            self._live.stop()
        try:
            if self.fm.get_power():
                self.fm.set_power(False)
            elif self.fm.get_recording():
                self.fm.set_recording(False)
        except Exception as e:
            print(f"Failed to power off: {e}")

    def on_close(self):
        self.shutdown()
        self._tk_root.destroy()

    def cb_power(self):
        if self.power:
            self.fm.set_power(False)
        elif self.record:
            self.fm.set_recording(False)
        else:
            self.fm.set_power(True)
            time.sleep(0.2)
            self.fm.set_volume(6)
            self.reset()
        self.update_power()

    def cb_record(self):
        self.fm.set_recording(True)
        time.sleep(0.2)
        self.fm.set_volume(15)
        self.reset()
        self.update_power()

    def cb_vol_slider(self, n):
        self.fm.set_volume(int(n))

    def cb_freq_up(self, n):
        self.freq += n
        self.freq = min(self.freq, 10700)
        self.set_freq(self.freq)

    def cb_freq_down(self, n):
        self.freq -= n
        self.freq = max(self.freq, 7600)
        self.set_freq(self.freq)

    def cb_mute(self):
        if self.mute:
            self.fm.set_mute(False)
        else:
            self.fm.set_mute(True)
        self.update_mute()

    def reset(self):
        self.set_freq(self.freq)
        self.update_volume()
        self.mute = False
        self.btn_vol_mute['text'] = "Mute"

    def set_freq(self, f):
        self.fm.set_channel(f/100)
        self.update_frequency()

    def update_frequency(self):
        res = self.fm.get_channel()
        self.freq = int(res*100)
        self.label_freq['text'] = f'{res:.2f}MHz'
        if res <= 76:
            self.btn_freq_down_1m['state'] = 'disabled'
            self.btn_freq_down_500k['state'] = 'disabled'
            self.btn_freq_down_100k['state'] = 'disabled'
        else:
            self.btn_freq_down_1m['state'] = 'normal'
            self.btn_freq_down_500k['state'] = 'normal'
            self.btn_freq_down_100k['state'] = 'normal'
        
        if res >= 107:
            self.btn_freq_up_1m['state'] = 'disabled'
            self.btn_freq_up_500k['state'] = 'disabled'
            self.btn_freq_up_100k['state'] = 'disabled'
        else:
            self.btn_freq_up_1m['state'] = 'normal'
            self.btn_freq_up_500k['state'] = 'normal'
            self.btn_freq_up_100k['state'] = 'normal'
        

    def update_mute(self):
        self.mute = self.fm.get_mute()
        if self.mute:
            self.btn_vol_mute['text'] = "Unmute"
        else:
            self.btn_vol_mute['text'] = "Mute"

    def update_volume(self):
        self.volume.set(self.fm.get_volume())

    def update_power(self):
        self.power = self.fm.get_power()
        self.record = self.fm.get_recording()

        if self.power or self.record:
            self.btn_power_on['text'] = "Power off"
            self.btn_record['state'] = 'disabled'
            self.vol_slider['state'] = 'normal'
            self.btn_vol_mute['state'] = 'normal'
        else:
            self.btn_power_on['text'] = "Power on"
            self.btn_record['state'] = 'normal'
            self.label_freq['text'] = f'---.--MHz'
            self.btn_freq_up_1m['state'] = 'disabled'
            self.btn_freq_up_500k['state'] = 'disabled'
            self.btn_freq_up_100k['state'] = 'disabled'
            self.btn_freq_down_1m['state'] = 'disabled'
            self.btn_freq_down_500k['state'] = 'disabled'
            self.btn_freq_down_100k['state'] = 'disabled'
            self.vol_slider['state'] = 'disabled'
            self.btn_vol_mute['state'] = 'disabled'

        if self.record:
            self.btn_record['relief'] = 'sunken'
        else:
            self.btn_record['relief'] = 'raised'

        # Record 모드가 아니면 입력이 이어폰 마이크라서 라이브 청취를 멈춘다.
        live = getattr(self, '_live', None)
        if live is not None and not self.record:
            live.stop()


if __name__ == '__main__':
    root = tk.Tk()
    app = MainApp(root)
    try:
        root.mainloop()
    finally:
        # 예외나 Ctrl+C로 종료되는 경우에도 전원 끄기를 시도한다.
        app.shutdown()
