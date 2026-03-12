# BWS Invest Agent - Windows 로컬 자동화 설정 스크립트
# 100% 로컬 PC에서 실행되도록 설정합니다.

$ScriptPath = Join-Path $PSScriptRoot "main.py"
$PythonPath = "C:\Program Files\Python312\python.exe" # 절대 경로 사용

# 1. AM Task (09:20)
$AM_Action = New-ScheduledTaskAction -Execute $PythonPath -Argument """$ScriptPath"" AM" -WorkingDirectory $PSScriptRoot
$AM_Trigger = New-ScheduledTaskTrigger -At 09:20 -Daily

# 2. PM Task (18:20)
$PM_Action = New-ScheduledTaskAction -Execute $PythonPath -Argument """$ScriptPath"" PM" -WorkingDirectory $PSScriptRoot
$PM_Trigger = New-ScheduledTaskTrigger -At 18:20 -Daily

# 기존 테스크 삭제
Unregister-ScheduledTask -TaskName "BWS_Invest_AM" -Confirm:$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "BWS_Invest_PM" -Confirm:$false -ErrorAction SilentlyContinue

# 테스크 설정 (지연된 작업 실행 허용 등)
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -StartWhenAvailable

# 관리자 권한으로 실행되도록 설정
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

# 테스크 등록
Register-ScheduledTask -TaskName "BWS_Invest_AM" -Action $AM_Action -Trigger $AM_Trigger -Principal $Principal -Settings $Settings -Description "BWS Invest AM Pipeline"
Register-ScheduledTask -TaskName "BWS_Invest_PM" -Action $PM_Action -Trigger $PM_Trigger -Principal $Principal -Settings $Settings -Description "BWS Invest PM Pipeline"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host " 로컬 작업 스케줄러 등록 완료!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "1. 오전 스케줄: 매일 09:20"
Write-Host "2. 오후 스케줄: 매일 18:20"
Write-Host ""
Write-Host "※ 주의: PC가 절전 모드이거나 꺼져 있으면 실행되지 않습니다."
Write-Host "※ 관리자 권한으로 실행해야 테스크 등록이 가능할 수 있습니다."
