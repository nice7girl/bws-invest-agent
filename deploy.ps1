# BWS Invest Agent - Windows PowerShell 서버 배포 스크립트
# AWS Bitnami (3.38.232.134) 에 Agent B + W를 배포합니다
#
# 사용법: powershell -ExecutionPolicy Bypass -File deploy.ps1
# 사전 조건: OpenSSH 설치 필요 (Windows 10+ 기본 포함)

$SERVER_IP = "3.38.232.134"
$SERVER_USER = "bitnami"
$SSH_KEY = "C:\Users\SKTelecom\Desktop\SSHkey.pem"
$REMOTE_DIR = "/home/bitnami/bws-invest"
$LOCAL_DIR = $PSScriptRoot   # 이 스크립트가 있는 폴더

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " BWS Invest Agent - Server Deployment" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "서버: $SERVER_USER@$SERVER_IP"
Write-Host "배포 경로: $REMOTE_DIR"
Write-Host ""

# 1. 서버에 디렉토리 생성
Write-Host "[1/4] 서버 디렉토리 생성..." -ForegroundColor Yellow
ssh -i $SSH_KEY -o StrictHostKeyChecking=no `
    "${SERVER_USER}@${SERVER_IP}" `
    "mkdir -p $REMOTE_DIR/output/reports $REMOTE_DIR/logs $REMOTE_DIR/data"

# 2. 필요한 파일만 서버로 복사 (Agent B, W, 공통 파일)
Write-Host "[2/4] 파일 업로드..." -ForegroundColor Yellow
$files = @("agent_b.py", "agent_w.py", "main.py", "scheduler.py", "config.json")
foreach ($file in $files) {
    $localPath = Join-Path $LOCAL_DIR $file
    if (Test-Path $localPath) {
        scp -i $SSH_KEY $localPath "${SERVER_USER}@${SERVER_IP}:$REMOTE_DIR/"
        Write-Host "  ✓ $file" -ForegroundColor Green
    }
    else {
        Write-Host "  ✗ $file (없음, 건너뜀)" -ForegroundColor Red
    }
}

# 3. Python 패키지 설치
Write-Host "[3/4] Python 패키지 설치..." -ForegroundColor Yellow
ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_IP}" @"
    pip3 install google-generativeai requests youtube-transcript-api --quiet
    echo 'Python 패키지 설치 완료'
"@

# 4. cron 등록 (평일 08:50 AM / 17:50 PM, 한국 시간)
# Bitnami 서버 기본 타임존은 UTC → 한국 시간(KST=UTC+9) 기준으로 -9시간
# 08:50 KST = 23:50 UTC(전날)  / 17:50 KST = 08:50 UTC
Write-Host "[4/4] Cron 스케줄 등록 (UTC 기준)..." -ForegroundColor Yellow
ssh -i $SSH_KEY "${SERVER_USER}@${SERVER_IP}" @"
    # 타임존 확인
    echo "현재 서버 타임존:"
    date +%Z

    # cron 등록 (기존 bws 관련 항목 제거 후 재등록)
    (crontab -l 2>/dev/null | grep -v 'bws-invest') | crontab -
    
    # UTC 기준: 08:50 KST = 전날 23:50 UTC / 17:50 KST = 08:50 UTC
    (crontab -l; \
     echo '50 23 * * 0-4 cd $REMOTE_DIR && PYTHONIOENCODING=utf-8 python3 main.py AM --skip-agent-s >> $REMOTE_DIR/logs/cron.log 2>&1  # 08:50 KST'; \
     echo '50 8  * * 1-5 cd $REMOTE_DIR && PYTHONIOENCODING=utf-8 python3 main.py PM --skip-agent-s >> $REMOTE_DIR/logs/cron.log 2>&1  # 17:50 KST') | crontab -
    
    echo 'Cron 등록 완료:'
    crontab -l | grep bws
"@

Write-Host "" 
Write-Host "======================================" -ForegroundColor Cyan
Write-Host " 배포 완료!" -ForegroundColor Green
Write-Host " PC가 꺼져 있어도 서버에서 자동 실행됩니다" -ForegroundColor Green
Write-Host "" -ForegroundColor Green
Write-Host " [주의] Agent S (NotebookLM)는" -ForegroundColor Yellow
Write-Host " 브라우저 자동화 특성상 로컬에서 실행하세요:" -ForegroundColor Yellow
Write-Host "   python agent_s.py AM" -ForegroundColor White
Write-Host "======================================" -ForegroundColor Cyan
