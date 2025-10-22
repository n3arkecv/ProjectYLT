@echo off
REM 使用 llama-gguf-split 工具合併 GGUF 分割文件
REM 根據官方文檔: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF

chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   GGUF 分割文件合併工具
echo   使用 llama-gguf-split
echo ========================================
echo.

cd /d "%~dp0"

REM 設置文件名
set PART1=qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf
set PART2=qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf
set OUTPUT=qwen2.5-7b-instruct-q4_k_m.gguf

REM 檢查分割文件是否存在
echo 檢查分割文件...
echo.

if not exist "%PART1%" (
    echo [錯誤] 找不到文件: %PART1%
    echo 請先下載兩個分割文件。
    echo.
    pause
    exit /b 1
)

if not exist "%PART2%" (
    echo [錯誤] 找不到文件: %PART2%
    echo 請先下載兩個分割文件。
    echo.
    pause
    exit /b 1
)

echo [成功] 找到分割文件:
echo   - %PART1%
echo   - %PART2%
echo.

REM 檢查 llama-gguf-split 是否可用
where llama-gguf-split >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 找不到 llama-gguf-split 工具！
    echo.
    echo 此工具是 llama.cpp 的一部分。
    echo.
    echo 安裝方法:
    echo 1. 前往: https://github.com/ggerganov/llama.cpp/releases
    echo 2. 下載最新的 Windows 版本 ^(llama-*-bin-win-*.zip^)
    echo 3. 解壓縮後將 llama-gguf-split.exe 放入此目錄或添加到 PATH
    echo.
    echo 或者使用 Python 安裝:
    echo    pip install llama-cpp-python
    echo.
    pause
    exit /b 1
)

echo [成功] 找到 llama-gguf-split 工具
echo.

REM 檢查輸出文件是否已存在
if exist "%OUTPUT%" (
    echo [警告] 合併後的文件已存在: %OUTPUT%
    echo.
    set /p OVERWRITE="是否要覆蓋現有文件? (Y/N): "
    if /i not "!OVERWRITE!"=="Y" (
        echo.
        echo 操作已取消。
        echo.
        pause
        exit /b 0
    )
    echo.
    echo 正在刪除舊文件...
    del "%OUTPUT%"
)

REM 開始合併
echo ========================================
echo 開始合併文件...
echo 這可能需要幾分鐘，請稍候...
echo ========================================
echo.

echo 執行命令:
echo llama-gguf-split --merge %PART1% %OUTPUT%
echo.

llama-gguf-split --merge "%PART1%" "%OUTPUT%"

if errorlevel 1 (
    echo.
    echo [錯誤] 合併失敗！
    echo 請檢查 llama-gguf-split 工具是否正確安裝。
    echo.
    pause
    exit /b 1
)

echo.
echo [成功] 文件合併完成！
echo.

REM 驗證合併後的文件
if not exist "%OUTPUT%" (
    echo [錯誤] 找不到合併後的文件！
    echo.
    pause
    exit /b 1
)

REM 顯示文件大小
for %%A in ("%OUTPUT%") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE% / 1048576
set /a SIZE_GB=%SIZE% / 1073741824

echo 合併後的文件:
echo   路徑: %CD%\%OUTPUT%
echo   大小: %SIZE_MB% MB ^(約 %SIZE_GB% GB^)
echo.

REM 檢查文件大小是否合理
if %SIZE_MB% LSS 4000 (
    echo [警告] 文件大小似乎不正確！
    echo 預期大小約為 4400 MB，但實際為 %SIZE_MB% MB
    echo.
) else (
    echo [成功] 文件大小正確！
    echo.
)

echo ========================================
echo   合併完成！
echo ========================================
echo.
echo 您現在可以:
echo   1. 啟動 ProjectYLT 應用程式
echo   2. ^(可選^) 刪除分割文件以節省空間
echo.

set /p DELETE="是否要刪除原始分割文件以節省空間? (Y/N): "
if /i "!DELETE!"=="Y" (
    echo.
    echo 正在刪除分割文件...
    del "%PART1%"
    del "%PART2%"
    echo [成功] 分割文件已刪除
    echo.
)

echo.
echo 按任意鍵關閉此視窗...
pause >nul

