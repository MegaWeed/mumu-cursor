@echo off
chcp 936 >nul
cd /d "%~dp0"
taskkill /IM "MUMU光标.exe" /F >nul 2>&1
"MUMU光标.exe" --restore
echo 已恢复系统光标
timeout /t 2 >nul
