# 1回だけ実行：毎日 21:50 に run_daily.bat を起動するタスクを登録する
# PowerShell を開いて:  powershell -ExecutionPolicy Bypass -File setup_task.ps1
$bat = Join-Path $PSScriptRoot "run_daily.bat"
$action  = New-ScheduledTaskAction -Execute $bat -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -Daily -At 21:50
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName "AI配信_毎日22時" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "登録しました。タスクスケジューラ > AI配信_毎日22時 で確認できます。"
