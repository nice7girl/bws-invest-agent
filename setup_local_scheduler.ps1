# BWS Invest Agent - Windows 로컬 자동화 설정 스크립트
# 서버 연결 불가 시 PC를 켜두면 자동으로 에이전트가 실행되도록 설정합니다.

$ScriptPath = Join-Path $PSScriptRoot "main.py"
$PythonPath = "python.exe" # 시스템 PATH에 python이 등록되어 있어야 합니다.

# 1. AM Task (08:35)
$AM_Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ScriptPath AM"
$AM_Trigger = New-ScheduledTaskTrigger -At 08:35 -Daily
# 평일(월-금)만 실행하도록 설정 (고급 설정은 UI에서 추가 가능)

# 2. PM Task (17:35)
$PM_Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "$ScriptPath PM"
$PM_Trigger = New-ScheduledTaskTrigger -At 17:35 -Daily

# 기존 테스크 삭제 (재설정용)
Unregister-ScheduledTask -TaskName "BWS_Invest_AM" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "BWS_Invest_PM" -Confirm:$false -ErrorAction SilentlyContinue

# 테스크 등록
Register-ScheduledTask -TaskName "BWS_Invest_AM" -Action $AM_Action -Trigger $AM_Trigger -Description "BWS Invest AM Pipeline"
Register-ScheduledTask -TaskName "BWS_Invest_PM" -Action $PM_Action -Trigger $PM_Trigger -Description "BWS Invest PM Pipeline"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " 로컬 작업 스케줄러 등록 완료!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "1. 오전 스케줄: 매일 08:35"
Write-Host "2. 오후 스케줄: 매일 17:35"
Write-Host ""
Write-Host "※ 주의: PC가 절전 모드이거나 꺼져 있으면 실행되지 않습니다."
Write-Host "※ 관리자 권한으로 실행해야 테스크 등록이 가능할 수 있습니다."
