@echo off
REM ProjectYLT Launcher
REM 啟動YouTube直播即時翻譯應用程式

echo Starting ProjectYLT...
echo.

REM 使用pythonw來避免顯示控制台視窗
pythonw main.pyw

REM 如果pythonw不可用，嘗試使用python
if errorlevel 1 (
    echo pythonw not found, trying python...
    python main.pyw
)

if errorlevel 1 (
    echo.
    echo Error: Failed to start the application.
    echo Please make sure Python is installed and in your PATH.
    pause
)

