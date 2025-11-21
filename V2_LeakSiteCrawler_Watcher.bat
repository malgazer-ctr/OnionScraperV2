@echo off
chcp 932 > nul
cd /d %~dp0
:: MonitorMainV2_Watcher.pyを起動
start python MonitorMainV2_Watcher.py
:: ClearTempDir.pyも並列で起動
start python ClearTempDir.py
echo 両方のプログラムをバックグラウンドで実行しています。
echo このウィンドウを閉じても実行は継続されます。
pause