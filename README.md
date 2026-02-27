# BWS Invest Agent

BWS 투자 정보 자동화 파이프라인. **Agent B(분석) → Agent W(전송) → Agent S(제작)** 오전/오후 자동 실행.

## 주요 기능

- **Agent B**: YouTube 영상 분석 → 투자 보고서 생성 (`output/reports/`)
- **Agent W**: 보고서를 텔레그램 채널로 발송
- **Agent S**: 보고서를 NotebookLM 업로드 → 영상 기획 스크립트 생성 (`output/scripts/`)

## 설치 및 설정

`config.json`에 입력:
- `GOOGLE_API_KEY`: [Google AI Studio](https://aistudio.google.com/)에서 발급
- `TELEGRAM_BOT_TOKEN`: @BotFather 봇 토큰
- `TELEGRAM_CHAT_ID`: 수신 채널 ID

NotebookLM 인증 (Agent S):
```bash
python antigravity-awesome-skills/skills/notebooklm/scripts/auth_manager.py setup
```

## 실행 방법

```bash
# 수동 실행
python main.py AM   # 또는 PM

# 로컬 스케줄러 (08:50 / 17:50 자동)
python scheduler.py
```

## 서버 배포 (Agent B + W, PC 꺼도 동작)

```bash
# deploy.sh 실행으로 서버에 자동 배포
bash deploy.sh
```

서버 cron (평일 자동 실행):
```
50 8  * * 1-5  cd /home/bitnami/bws-invest && python3 main.py AM
50 17 * * 1-5  cd /home/bitnami/bws-invest && python3 main.py PM
```

> **Agent S**는 브라우저 기반(NotebookLM)이므로 **로컬에서 별도 실행** 권장

## 폴더 구조

```
output/
├── reports/    ← Agent B 분석보고서
└── scripts/    ← Agent S 영상기획 스크립트
logs/           ← 시스템 로그
data/           ← 중복 전송 방지 기록
```
