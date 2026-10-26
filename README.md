# EO-IC100 FM Radio (Python PoC)

이 프로젝트는 [@kjy00302/eo-ic100_radio](https://github.com/kjy00302/eo_ic100_radio_mac) 의 작업을 기반으로 일부를 수정하여 정리한 EO-IC100 FM 라디오 제어 실험 코드입니다. 핵심 동작은 동일하게 삼성 이어폰의 FM 라디오 기능을 USB 제어로 켜고, 주파수를 맞추고, 음량과 RDS를 다루는 것입니다. Swift로 작성된 맥 네이티브 앱은 [@darkbrow/eo_ic100_radio_mac](https://github.com/darkbrow/eo_ic100_radio_mac) 저장소에 있습니다.

## 프로젝트 목적

- Samsung EO-IC100 이어폰에 내장된 FM 라디오 기능을 제어
- Python 기반으로 기본 기능 검증
- 라디오 전원, 주파수, 음량, RDS, 녹음 모드 제어
- macOS 환경에 맞는 제어 방식과 종료 처리 보완

## 기반 코드와 수정 내용

기본 구조는 [@kjy00302/eo-ic100_radio](https://github.com/kjy00302/eo_ic100_radio_mac) 의 `besfm.py`, `ic100_radio.py`, `live_monitor.py`를 따라가며, 아래와 같은 변경을 반영했습니다.

### 1. USB 접근 방식 정리
기존 코드에서 `BesFM.__init__`는 USB 디바이스를 분리하거나 커널 드라이버를 떼어내는 처리와 notify endpoint 사용을 전제로 하고 있습니다.

수정 버전에서는 다음과 같이 바뀌었습니다.

- `self._notify_ep = None`로 두어 notify endpoint를 사용하지 않음
- "분리/클레임 없이 control transfer만 사용"이라는 주석 추가
- 커널 드라이버 분리 로직을 비활성화
- sudo로 실행할 필요없음

즉, 원본 코드가 "USB 인터페이스를 직접 잡고 관리하는 방식"에 더 가깝다면, 수정 버전은 제어 전송 중심의 단순화된 방식으로 바뀌었습니다.

### 2. 녹음 모드 오디오를 macOS 출력으로 전달하는 로직 유지
`live_monitor.py`는 Record 모드에서 라디오 오디오를 macOS 출력으로 전달하는 기능을 담고 있습니다.

- 입력 장치 선택
- 출력 장치 선택
- gain(dB) 조절
- start/stop 제어
- xrun(끊김) 계수

이 부분은 원본 PoC의 핵심 기능을 그대로 유지하면서, macOS 환경에서 직접 청취할 수 있도록 연결한 구조입니다.

### 3. 종료 처리 보강
`ic100_radio.py`는 창 닫기와 macOS 종료 시점에 라디오 전원을 끄는 로직을 추가했습니다.

- `master.protocol("WM_DELETE_WINDOW", self.on_close)`
- `master.createcommand('::tk::mac::Quit', self.on_close)`
- `shutdown()`에서 라디오 전원/녹음 모드 정리

이 변경은 단순 실행이 아니라, GUI 프로그램으로 종료 시 안전하게 정리하는 데 초점이 있습니다.

### 4. README 설명 보강
기본 README는 기능 범위가 좁고 요약적이었지만, 수정 버전에서는 다음 정보를 더 자세히 설명하도록 보강했습니다.

- EO-IC100 FM 라디오의 동작 목적
- 기능 목록
- 시스템 요구사항
- USB 제어 방식과 제한
- 녹음 모드에서 오디오 출력을 전달하는 구조
- 경고 사항

## 주요 기능

- 라디오 전원 제어: On / Off
- 주파수 튜닝
- 볼륨 제어
- 음소거(Mute)
- RDS 데이터 수신
- GUI 기반 제어
- Record 모드에서 오디오 출력 전달
- macOS 종료 시 정리 처리

## 시스템 요구사항

- Samsung EO-IC100 이어폰
- Python 3.8 이상
- USB Type-C 포트가 있는 PC 또는 C-to-A 어댑터 환경
- 필요 라이브러리:
  - 일부 OS의 경우 libusb가 필요할 수 있음.
  - pyusb
  - pyserial
  - sounddevice
  - numpy

## 주의 사항

- 라디오 전환 시 큰 팝 소리가 발생할 수 있습니다.
- 녹음 모드에서 출력 장치로 오디오를 재생할 때는 장치 선택과 볼륨 조절에 주의해야 합니다.
- macOS 환경에서는 USB 장치 접근 방식이 원본 코드보다 더 단순화된 control transfer 중심으로 동작합니다.

## 파일 구성

- `besfm.py`: EO-IC100 FM 칩 제어용 핵심 로직
- `ic100_radio.py`: GUI 기반 라디오 제어 프로그램
- `ic100_radio_gui.py`: GUI 구성 요소
- `ic100_rds.py`: RDS 관련 파싱 모듈
- `live_monitor.py`: Record 모드 오디오를 출력으로 전달하는 모듈
- `README.md`: 프로젝트 설명

## 핵심 제어 로직

`besfm.py`는 다음 명령을 중심으로 동작합니다.

- 전원 제어
- 녹음 모드 제어
- 대역 선택
- 음소거/볼륨
- 채널 설정
- RDS 상태 조회
- seek/tune 상태 조회

대표 메서드에는 다음이 있습니다.

- `set_power()`
- `set_recording()`
- `set_channel()`
- `set_volume()`
- `set_mute()`
- `set_rds()`
- `get_status()`

## 실행

```bash
python3 ic100_radio.py
```
