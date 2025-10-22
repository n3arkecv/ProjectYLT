@echo off
REM ProjectYLT - 自動模型下載工具
REM 自動安裝 Hugging Face CLI 並下載模型

chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   ProjectYLT 模型下載工具
echo ========================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未檢測到 Python！
    echo 請先安裝 Python 3.10 或更高版本。
    echo.
    pause
    exit /b 1
)

echo [成功] Python 已安裝
python --version
echo.

REM 安裝 Hugging Face CLI 和相關依賴
echo ========================================
echo 步驟 1: 安裝 Hugging Face CLI 和依賴
echo ========================================
echo.
echo 正在安裝 huggingface_hub[cli]...
echo.

pip install -U "huggingface_hub[cli]" --quiet

if errorlevel 1 (
    echo [錯誤] 安裝 Hugging Face CLI 失敗！
    echo.
    pause
    exit /b 1
)

echo [成功] Hugging Face CLI 已安裝
echo.

echo 正在安裝 hf_xet ^(處理大文件所需^)...
echo.

pip install -U "huggingface_hub[hf_xet]" --quiet

if errorlevel 1 (
    echo [警告] 安裝 hf_xet 失敗，將繼續嘗試下載
    echo.
) else (
    echo [成功] hf_xet 已安裝
    echo.
)

echo 所有依賴安裝完成
echo.

REM 顯示模型選項
echo ========================================
echo 步驟 2: 選擇要下載的模型
echo ========================================
echo.
echo 請選擇您想下載的 Qwen2.5 模型:
echo.
echo   1^) Qwen2.5-7B-Instruct ^(Q4_K_M^)
echo      檔案大小: 約 4.4 GB
echo      顯存需求: 約 5-6 GB
echo      翻譯品質: 最佳
echo      適合: RTX 4070 8GB ^(推薦^)
echo.
echo   2^) Qwen2.5-3B-Instruct ^(Q4_K_M^)
echo      檔案大小: 約 2.0 GB
echo      顯存需求: 約 2-3 GB
echo      翻譯品質: 良好
echo      適合: 顯存不足或追求速度
echo.
echo   3^) Qwen2.5-1.5B-Instruct ^(Q4_K_M^)
echo      檔案大小: 約 1.0 GB
echo      顯存需求: 約 1-2 GB
echo      翻譯品質: 尚可
echo      適合: 低顯存或快速測試
echo.
echo   0^) 取消
echo.

set /p CHOICE="請輸入選項 (1-3, 0=取消): "

if "%CHOICE%"=="0" (
    echo.
    echo 操作已取消。
    echo.
    pause
    exit /b 0
)

if "%CHOICE%"=="1" (
    set MODEL_REPO=Qwen/Qwen2.5-7B-Instruct-GGUF
    set MODEL_PATTERN=*q4_k_m*.gguf
    set MODEL_SIZE=4.4 GB
    set MODEL_NAME=Qwen2.5-7B-Instruct
) else if "%CHOICE%"=="2" (
    set MODEL_REPO=Qwen/Qwen2.5-3B-Instruct-GGUF
    set MODEL_PATTERN=*q4_k_m*.gguf
    set MODEL_SIZE=2.0 GB
    set MODEL_NAME=Qwen2.5-3B-Instruct
) else if "%CHOICE%"=="3" (
    set MODEL_REPO=Qwen/Qwen2.5-1.5B-Instruct-GGUF
    set MODEL_PATTERN=*q4_k_m*.gguf
    set MODEL_SIZE=1.0 GB
    set MODEL_NAME=Qwen2.5-1.5B-Instruct
) else (
    echo.
    echo [錯誤] 無效的選項！
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 您選擇了: %MODEL_NAME%
echo 檔案模式: %MODEL_PATTERN%
echo 檔案大小: %MODEL_SIZE%
echo ========================================
echo.

REM 確認下載
set /p CONFIRM="確認下載此模型? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo 下載已取消。
    echo.
    pause
    exit /b 0
)

echo.
echo ========================================
echo 步驟 3: 下載模型
echo ========================================
echo.
echo 正在從 Hugging Face 下載...
echo 這可能需要一些時間，請耐心等待...
echo.

REM 檢查並刪除舊文件
if exist "*.gguf" (
    echo 檢測到舊的模型文件，正在清理...
    for %%f in (*.gguf) do (
        echo 刪除: %%f
        del "%%f" 2>nul
    )
    echo.
)

REM 執行下載
echo 使用 Hugging Face CLI 下載模型...
echo.

REM 使用新的 hf download 命令（避免警告）
hf download %MODEL_REPO% --include "%MODEL_PATTERN%" --local-dir .

if errorlevel 1 (
    echo.
    echo [錯誤] 下載失敗！
    echo.
    echo 可能的原因:
    echo   - 網絡連接問題
    echo   - Hugging Face 服務暫時不可用
    echo   - 磁碟空間不足
    echo.
    pause
    exit /b 1
)

echo.
echo [成功] 模型下載完成！
echo.

REM 驗證文件
echo.
echo 檢查下載的文件...
echo.

REM 尋找下載的 GGUF 文件
set FOUND_FILE=
for %%F in (*.gguf) do (
    set FOUND_FILE=%%F
    echo 找到文件: %%F
)

if "%FOUND_FILE%"=="" (
    echo [警告] 找不到下載的模型文件！
    echo 請檢查網絡連接後重試。
    echo.
    pause
    exit /b 1
)

REM 顯示文件資訊
for %%A in ("%FOUND_FILE%") do set SIZE=%%~zA
set /a SIZE_MB=%SIZE% / 1048576
set /a SIZE_GB=%SIZE% / 1073741824

echo.
echo 下載的文件:
echo   路徑: %CD%\%FOUND_FILE%
echo   大小: %SIZE_MB% MB ^(約 %SIZE_GB% GB^)
echo.

REM 檢查是否為分割文件
set IS_SPLIT=0
echo %FOUND_FILE% | findstr /C:"-00001-of-" >nul
if not errorlevel 1 (
    set IS_SPLIT=1
)

if !IS_SPLIT!==1 (
    echo.
    echo 檢測到分割文件: %FOUND_FILE%
    echo 需要使用 llama-gguf-split 工具合併...
    echo.
    
    REM 檢查 llama-gguf-split 是否可用
    where llama-gguf-split >nul 2>&1
    if errorlevel 1 (
        echo [警告] 未找到 llama-gguf-split 工具
        echo.
        echo 分割文件已下載，但需要手動合併。
        echo 請執行: merge_with_llama_tool.bat
        echo.
        echo 或安裝 llama.cpp:
        echo   https://github.com/ggerganov/llama.cpp/releases
        echo.
        set CONFIG_FILE_PATH=%FOUND_FILE%
        goto :skip_merge
    )
    
    REM 設置合併後的文件名
    set MERGED_FILE=!FOUND_FILE:-00001-of-00002=!
    
    echo 正在合併文件...
    echo 輸出: !MERGED_FILE!
    echo.
    
    llama-gguf-split --merge "%FOUND_FILE%" "!MERGED_FILE!"
    
    if errorlevel 1 (
        echo [警告] 合併失敗
        echo 請手動執行: merge_with_llama_tool.bat
        echo.
        set CONFIG_FILE_PATH=%FOUND_FILE%
    ) else (
        echo [成功] 文件合併完成！
        echo.
        set FOUND_FILE=!MERGED_FILE!
        set CONFIG_FILE_PATH=!MERGED_FILE!
        
        REM 詢問是否刪除分割文件
        set /p DEL_SPLIT="是否刪除分割文件以節省空間? (Y/N): "
        if /i "!DEL_SPLIT!"=="Y" (
            echo 正在刪除分割文件...
            del *-00001-of-*.gguf 2>nul
            del *-00002-of-*.gguf 2>nul
            echo [成功] 分割文件已刪除
            echo.
        )
    )
) else (
    echo 文件名稱: %FOUND_FILE%
    set CONFIG_FILE_PATH=%FOUND_FILE%
    echo.
)

:skip_merge
echo.

REM 更新 config.json
echo ========================================
echo 步驟 4: 更新配置文件
echo ========================================
echo.

set CONFIG_FILE=..\config.json

if exist "%CONFIG_FILE%" (
    echo 正在更新 config.json...
    echo 模型路徑: %CONFIG_FILE_PATH%
    echo.
    
    REM 創建 Python 腳本來更新 JSON
    (
        echo import json
        echo import sys
        echo try:
        echo     with open^('../config.json', 'r', encoding='utf-8'^) as f:
        echo         config = json.load^(f^)
        echo     config['models']['llm_model'] = 'models/%CONFIG_FILE_PATH%'
        echo     with open^('../config.json', 'w', encoding='utf-8'^) as f:
        echo         json.dump^(config, f, indent=2, ensure_ascii=False^)
        echo     print^('[成功] config.json 已更新'^)
        echo     print^('模型路徑: models/%CONFIG_FILE_PATH%'^)
        echo except Exception as e:
        echo     print^(f'[錯誤] 更新 config.json 失敗: {e}'^)
        echo     sys.exit^(1^)
    ) > update_config.py
    
    python update_config.py
    
    REM 清理臨時文件
    del update_config.py 2>nul
    
    echo.
) else (
    echo [警告] 找不到 config.json
    echo 請手動設置模型路徑: models/%FOUND_FILE%
    echo.
)

echo ========================================
echo   下載完成！
echo ========================================
echo.
echo 模型已成功下載並配置。
echo.
echo 您現在可以:
echo   1. 關閉此視窗
echo   2. 啟動 ProjectYLT 應用程式 ^(雙擊 launcher.bat^)
echo   3. 開始使用即時翻譯功能！
echo.
echo 注意: 首次運行時 Whisper 模型也會自動下載 ^(約 1.5GB^)
echo.

pause
