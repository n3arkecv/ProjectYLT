# 開發者指引

## 專案架構

### 模塊化設計

ProjectYLT 採用模塊化設計，每個模塊負責特定功能：

#### 核心模塊 (`modules/`)

1. **audio_capture.py** - 音訊捕獲
   - 使用 PyAudioWPatch 的 WASAPI loopback
   - 獨立線程運行，使用 Queue 傳遞數據
   - 自動重採樣到 16kHz 單聲道

2. **stt_module.py** - 語音轉文字
   - 封裝 faster-whisper
   - CPU 執行，使用 int8 量化
   - 支援逐字串流輸出

3. **llm_module.py** - LLM翻譯
   - 使用 llama-cpp-python
   - GPU 加速（可配置層數）
   - 支援串流輸出

4. **context_manager.py** - 情境上下文管理
   - 維護滾動視窗的對話歷史
   - 自動生成情境摘要
   - 為 LLM 提供上下文

5. **pipeline.py** - 數據流管道
   - 協調所有模塊
   - 管理三個處理線程
   - 實現背壓機制

6. **overlay_window.py** - Overlay字幕
   - PyQt6 無邊框視窗
   - 可拖曳、調整透明度
   - 三行顯示：原文/譯文/上下文

7. **gui_window.py** - 主GUI
   - 控制面板
   - 參數設置
   - 事件日誌顯示

8. **system_check.py** - 系統檢查
   - 檢查 Python 版本
   - 檢查依賴套件
   - 檢查模型文件

#### 工具模塊 (`utils/`)

1. **logger.py** - 日誌系統
   - 統一的日誌管理
   - 支援 GUI 回調
   - 自動寫入文件

2. **config.py** - 配置管理
   - JSON 配置讀寫
   - 支援嵌套配置
   - 預設值處理

### 數據流程

```
[音訊設備]
    ↓
[AudioCapture]
    ↓ (Queue)
[STTProcessor]
    ↓ (Queue)
[LLMProcessor + ContextManager]
    ↓ (Queue)
[OverlayController]
    ↓
[OverlayWindow]
```

### 線程模型

- **主線程**: PyQt6 事件循環
- **音訊捕獲線程**: 持續讀取音訊
- **STT 處理線程**: 轉錄音訊
- **LLM 處理線程**: 翻譯文本
- **協調線程** (3個):
  - Audio → STT
  - STT → LLM
  - LLM → Display

## 開發環境設置

### 安裝依賴

```bash
pip install -r requirements.txt
```

### GPU 支援 (可選)

```bash
# CUDA 12.x
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122
```

### 下載模型

參見 `models/README.md`

## 添加新功能

### 添加新的翻譯語言

1. 修改 `config.json`:
   ```json
   "translation": {
     "source_language": "新語言代碼",
     "target_language": "zh-TW"
   }
   ```

2. 更新 `llm_module.py` 的 prompt 模板

### 添加新的 STT 模型

1. 在 `stt_module.py` 中創建新類
2. 實現相同的介面：`load_model()`, `transcribe()`, `warm_up()`
3. 在 `pipeline.py` 中替換實例

### 添加新的 LLM 模型

1. 在 `llm_module.py` 中修改模型載入邏輯
2. 調整 `n_gpu_layers` 參數以適應顯存
3. 更新 prompt 模板

## 調試技巧

### 啟用詳細日誌

修改 `utils/logger.py`:
```python
self._logger.setLevel(logging.DEBUG)
console_handler.setLevel(logging.DEBUG)
```

### 單獨測試模塊

每個模塊都可以獨立測試：

```python
# 測試 STT
from modules.stt_module import STTModule
import numpy as np

stt = STTModule()
stt.load_model()
audio = np.zeros(16000, dtype=np.float32)
text, segments = stt.transcribe(audio)
print(text)
```

### 檢查隊列狀態

在 pipeline 模塊中添加：
```python
logger.debug(f"Audio queue size: {self.audio_queue.qsize()}")
```

## 效能優化

### CPU 優化

1. **減少 Whisper 模型大小**: `small` 比 `medium` 快約 2 倍
2. **調整 VAD 參數**: 更快檢測句子結束
3. **增加 CPU 線程數**: 在支援的平台上

### GPU 優化

1. **調整 GPU 層數**: 根據顯存調整 `n_gpu_layers`
2. **減少批次大小**: 如果顯存不足
3. **使用更小的模型**: Qwen 3B 或 1.5B

### 延遲優化

1. **減少音訊塊大小**: `chunk_duration` 從 2.0 降到 1.5
2. **預測性處理**: 在檢測到語音時立即開始處理
3. **並行處理**: 確保所有線程都在運行

## 常見問題

### ImportError: No module named 'xxx'

確保已安裝所有依賴：
```bash
pip install -r requirements.txt
```

### CUDA out of memory

1. 減少 `llm_n_gpu_layers`
2. 使用更小的模型
3. 關閉其他使用 GPU 的程式

### 音訊捕獲失敗

1. 確認 Windows 音訊服務正在運行
2. 檢查音訊設備是否正在播放
3. 嘗試使用不同的設備索引

### 翻譯品質不佳

1. 調整 LLM 的 temperature 參數
2. 改進 prompt 設計
3. 增加上下文視窗大小

## 貢獻指南

### 代碼風格

- 遵循 PEP 8
- 使用類型提示
- 添加文檔字串

### 提交流程

1. 創建功能分支
2. 實現功能並測試
3. 確保沒有 linter 錯誤
4. 提交 Pull Request

### 測試

目前尚未實現自動化測試，但計劃添加：
- 單元測試
- 整合測試
- 效能測試

## 打包發布

### 使用 PyInstaller

```bash
pip install pyinstaller

pyinstaller --name ProjectYLT ^
    --windowed ^
    --icon=icon.ico ^
    --add-data "models;models" ^
    --add-data "config.json;." ^
    main.pyw
```

### 注意事項

- 模型文件需要單獨分發（太大）
- 提供模型下載腳本
- 包含 Visual C++ Redistributable

## 路線圖

### v1.1
- [ ] 支援英文翻譯
- [ ] 錄製功能
- [ ] 效能監控

### v1.2
- [ ] 自動更新
- [ ] 翻譯記憶庫
- [ ] 自訂快捷鍵

### v2.0
- [ ] 多語言支援
- [ ] API 服務模式
- [ ] 插件系統

## 授權

本專案為個人開發項目。

