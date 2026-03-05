#!/bin/bash
# BWS Invest Agent - 서버 배포 스크립트
# AWS Bitnami 서버 (3.38.232.134) 에 Agent B + W를 배포합니다
# 
# 사용법: bash deploy.sh
# 사전 조건: SSHkey.pem 파일이 C:\Users\SKTelecom\Desktop\ 에 있어야 함

# SERVER_IP, SERVER_USER, SSH_KEY 환경 변수가 설정되어 있어야 합니다.
# 예: export SERVER_IP="x.x.x.x"
SERVER_IP=${SERVER_IP:-"YOUR_SERVER_IP"}
SERVER_USER=${SERVER_USER:-"YOUR_SERVER_USER"}
SSH_KEY=${SSH_KEY:-"PATH_TO_YOUR_SSH_KEY"}
REMOTE_DIR="/home/bitnami/bws-invest"

echo "======================================"
echo " BWS Invest Agent - Server Deployment"
echo "======================================"
echo ""
echo "서버: $SERVER_USER@$SERVER_IP"
echo "배포 경로: $REMOTE_DIR"
echo ""

# 1. 서버에 디렉토리 생성
echo "[1/4] 서버 디렉토리 생성..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_IP "mkdir -p $REMOTE_DIR/output/reports $REMOTE_DIR/logs $REMOTE_DIR/data"

# 2. 필요한 파일만 서버로 복사 (Agent B, W, main, scheduler)
echo "[2/4] 파일 업로드..."
scp -i "$SSH_KEY" \
    agent_b.py \
    agent_w.py \
    main.py \
    scheduler.py \
    config.json \
    $SERVER_USER@$SERVER_IP:$REMOTE_DIR/

# 3. 서버에 Python 패키지 설치
echo "[3/4] Python 패키지 설치..."
ssh -i "$SSH_KEY" $SERVER_USER@$SERVER_IP "
    cd $REMOTE_DIR
    pip3 install google-generativeai requests youtube-transcript-api --quiet
    echo 'Python 패키지 설치 완료'
"

# 4. Apache 심볼릭 링크 설정 (로컬 체크용)
echo "[4/5] Apache 심볼릭 링크 설정..."
ssh -i "$SSH_KEY" $SERVER_USER@$SERVER_IP "
    sudo mkdir -p /opt/bitnami/apache/htdocs/bws_reports
    sudo ln -sf $REMOTE_DIR/output/reports/*.md /opt/bitnami/apache/htdocs/bws_reports/ 2>/dev/null || true
    sudo ln -sfn $REMOTE_DIR/output/reports /opt/bitnami/apache/htdocs/bws_reports 2>/dev/null || true
    echo '심볼릭 링크 설정 완료'
"

# 5. cron 등록 (서버는 UTC 기준이므로 KST 시간에 맞춰 변환)
# KST 08:35 -> UTC 23:35 (전날) / 월-금 KST -> 일-목 UTC (0-4)
# KST 17:35 -> UTC 08:35 (당일) / 월-금 KST -> 월-금 UTC (1-5)
echo "[5/5] Cron 스케줄 등록 (UTC 기준)..."
ssh -i "$SSH_KEY" $SERVER_USER@$SERVER_IP "
    # 기존 bws 관련 cron 삭제 후 재등록
    (crontab -l 2>/dev/null | grep -v 'bws-invest'; \
     echo '35 23 * * 0-4 cd $REMOTE_DIR && PYTHONIOENCODING=utf-8 python3 main.py AM --skip-agent-s >> $REMOTE_DIR/logs/cron.log 2>&1'; \
     echo '35 8 * * 1-5 cd $REMOTE_DIR && PYTHONIOENCODING=utf-8 python3 main.py PM --skip-agent-s >> $REMOTE_DIR/logs/cron.log 2>&1') | crontab -
    echo 'Cron 등록 완료 (UTC 23:35 / 08:35):'
    crontab -l | grep bws
"

echo ""
echo "======================================"
echo " 배포 완료!"
echo " PC가 꺼져 있어도 서버에서 자동 실행됩니다"
echo " Agent S(NotebookLM)는 로컬에서 별도 실행하세요"
echo "======================================"
