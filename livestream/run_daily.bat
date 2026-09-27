@echo off
rem 毎日 21:50 にタスクスケジューラから起動される。アプリを立ち上げて server.py が 22:00〜23:00 を回す。
chcp 65001 > nul
cd /d %~dp0

rem ↓ 自分のPCのインストール先に合わせて書き換える
set VOICEVOX_EXE=%LOCALAPPDATA%\Programs\VOICEVOX\vv-engine\run.exe
set OBS_DIR=C:\Program Files\obs-studio\bin\64bit
set ONECOMME_EXE=%LOCALAPPDATA%\Programs\OneComme\OneComme.exe

start "" "%VOICEVOX_EXE%"
start "" /d "%OBS_DIR%" obs64.exe --minimize-to-tray --disable-shutdown-check
start "" "steam://rungameid/1325860"
start "" "%ONECOMME_EXE%"

rem アプリの起動待ち
timeout /t 60 /nobreak > nul

if not exist logs mkdir logs
python server.py >> logs\console.log 2>&1
