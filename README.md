# EO-IC100 FM Radio (Python PoC)
삼성 EO-IC100 USB-C 이어폰에 내장된 FM 라디오 기능을 파이썬으로 제어할 수 있음을 검증한 개념 증명(Proof of Concept) 프로젝트입니다.
갤럭시 Note10 프레임워크를 디컴파일하여 분석한 제어 로직을 기반으로 작성되었습니다.

## 주요 기능
- 라디오 전원 제어: FM 라디오 On / Off
- 주파수 튜닝: 원하는 FM 주파수 수신 및 조정
- 음량 제어: 볼륨 조절 및 음소거(Mute) 설정
- RDS 데이터 수신: 수신 중인 방송의 RDS(Radio Data System) 정보 조회
- GUI 애플리케이션 및 오디오 출력 지원: ic100_radio_gui.py를 통해 GUI 환경에서 제어할 수 있으며, 수신되는 오디오 신호를 시스템의 녹음 장치(Audio Input Device/Line-in)로 전송하여 타 프로그램에서 캡처 및 출력이 가능하도록 합니다(녹음 파일로 저장하는 기능은 아닙니다).

## 시스템 요구사항 및 라이브러리
- 지원 기기: 삼성 EO-IC100 (EO-IC100BBEGKR 한국 출시 모델)
- 펌웨어 버전: 0.56_050401_aa
- Python 3.8 이상
- USB Type-C 포트가 내장된 PC 또는 C-to-A 젠더 연결 환경
- OS 권한: USB 디바이스 Direct I/O 제어를 위한 관리자/root 권한 필요할 수 있음
- 필수 파이썬 라이브러리 설치
```
pip install pyusb pyserial sounddevice numpy
```
(참고: 사용 중인 OS에 따라 libusb 바이너리 설치가 필요할 수 있습니다.)

## 주의 사항 (Warning)
동작 중 간헐적으로 큰 팝 소리(Loud pop sound)가 발생할 수 있으니, 귀에 착용한 상태에서 테스트할 때에는 음량에 주의하시기 바랍니다.

## 파일 구조
- ic100_radio.py: EO-IC100 라디오 제어를 위한 핵심 Python 파이썬 로직
- ic100_radio_gui.py: GUI 기반의 라디오 제어 및 오디오 수신 장치 전달 프로그램
- ic100_rds.py: RDS 데이터 파싱 관련 모듈
- besfm.py: 라디오 제어 관련 보조 스크립트

## 사용 방법
EO-IC100 이어폰을 PC의 USB-C 포트에 연결합니다.
```
python ic100_radio_gui.py
```
