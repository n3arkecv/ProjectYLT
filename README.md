# ProjectYLT

YouTube直播即時翻譯應用程式

## 功能特點

- 🎯 **即時翻譯**: 日文→繁體中文即時翻譯
- 🎤 **語音識別**: 使用faster-whisper進行高品質STT（CPU執行）
- 🤖 **AI翻譯**: 本地LLM翻譯，保護隱私
- 🎨 **浮動字幕**: 可自訂的Overlay顯示
- 📝 **情境上下文**: 智能管理對話上下文，提升翻譯準確度
- ⚡ **低延遲**: 0.5-1.5秒內完成從語音到翻譯的全流程

## 系統需求

### 硬體需求
- **CPU**: Intel i7-14700HX 或同等性能
- **GPU**: NVIDIA RTX 4070 8GB 或更高
- **記憶體**: 16GB RAM
- **儲存空間**: 至少 10GB 可用空間（含模型）

### 軟體需求
- **作業系統**: Windows 10/11
- **Python**: 3.10 或更高版本
- **CUDA**: 建議安裝最新版本（用於GPU加速）
- **Visual Studio Build Tools 2022**: 編譯 llama-cpp-python 所需（見下方安裝說明）

## 安裝步驟

### 0. 安裝 Visual Studio Build Tools 2022（重要！）

**為什麼需要？** llama-cpp-python 需要 C++ 編譯器才能正確安裝和運行。

**安裝步驟：**

1. 下載 Visual Studio Build Tools 2022:
   - 前往: https://visualstudio.microsoft.com/zh-hant/downloads/
   - 滾動到「所有下載」→「Tools for Visual Studio」
   - 下載「Build Tools for Visual Studio 2022」

2. 運行安裝程式，選擇以下工作負載：
   - ✅ **Desktop development with C++**（使用 C++ 的桌面開發）
   
3. 在右側「安裝詳細資料」中，確保勾選：
   - ✅ MSVC v143 - VS 2022 C++ x64/x86 build tools
   - ✅ Windows 10/11 SDK
   - ✅ C++ CMake tools for Windows

4. 點擊「安裝」並等待完成（可能需要 5-10GB 空間）

5. 安裝完成後，**重新啟動電腦**

**已經安裝 Visual Studio 2022？** 如果你已經安裝了完整版的 Visual Studio 2022，且包含 C++ 開發工具，則無需另外安裝 Build Tools。

### 1. 安裝Python依賴

**步驟 1**: 安裝基礎依賴
```bash
pip install -r requirements.txt
```

**步驟 2**: 安裝 llama-cpp-python（GPU 加速版本）

⚠️ **重要**: 請先確認已安裝 Visual Studio Build Tools 2022（見上方步驟 0）

根據你的 CUDA 版本選擇安裝命令：

# 卸載CPU版本
pip uninstall llama-cpp-python -y

```bash
# 檢查 CUDA 版本
nvidia-smi

# CUDA 12.x 或 13.x（推薦）
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122

# CUDA 11.x
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu118
```

**注意**: 
- CUDA 13.0 用戶請使用 CUDA 12.x 版本（向後兼容）
- 如果安裝過程中出現編譯錯誤，請確認 Visual Studio Build Tools 已正確安裝

### 2. 下載模型

#### Whisper模型（自動下載）
首次運行時會自動下載，無需手動操作。

#### LLM模型下載

**推薦方法：使用自動下載工具** ⭐

雙擊 `models/download_model.bat`，腳本會：
- 自動安裝 Hugging Face CLI
- 讓您選擇模型（7B / 3B / 1.5B）
- 自動下載並正確處理分割文件
- 自動更新配置

**模型選擇建議：**
- **Qwen2.5-7B** (4.4GB): 最佳翻譯品質，適合 RTX 4070 8GB
- **Qwen2.5-3B** (2.0GB): 良好品質，更快速度
- **Qwen2.5-1.5B** (1.0GB): 基本品質，最快速度

**手動下載方法：**

如果自動工具無法使用，請使用 Hugging Face CLI：

```bash
# 安裝 CLI
pip install -U "huggingface_hub[cli]"

# 下載 7B 模型（推薦）
hf download Qwen/Qwen2.5-7B-Instruct-GGUF --include "*q4_k_m*.gguf" --local-dir models

# 或 3B 模型
hf download Qwen/Qwen2.5-3B-Instruct-GGUF --include "*q4_k_m*.gguf" --local-dir models
```

**如果下載了分割文件，需要合併：**

根據 [官方文檔](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)，使用 `llama-gguf-split` 工具：

```bash
# 進入 models 目錄
cd models

# 使用 llama-gguf-split 合併
llama-gguf-split --merge qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf qwen2.5-7b-instruct-q4_k_m.gguf

# 或使用提供的批次文件
# 雙擊 models/merge_with_llama_tool.bat
```

詳細說明請參閱 `models/README.md`

## 使用方法

### 啟動應用程式

**方法1**: 雙擊 `launcher.bat`

**方法2**: 使用Python直接運行
```bash
pythonw main.pyw
```

### 使用流程

1. **啟動應用程式**
   - 主GUI視窗和Overlay視窗會自動顯示
   - 等待模型載入完成

2. **設置音訊來源**
   - 在主GUI中選擇要捕獲的音訊設備
   - 預設會捕獲系統音訊（WASAPI loopback）

3. **調整Overlay設置**
   - 透明度：調整Overlay的透明程度
   - 文字背景：開關文字背景顯示
   - Overlay大小：選擇小/中/大

4. **開始翻譯**
   - 點擊「開始」按鈕
   - Overlay會顯示：
     - 第一行：日文原文（逐字顯示）
     - 第二行：中文譯文（句子完成後顯示）
     - 第三行：情境上下文（小字體）

5. **停止翻譯**
   - 點擊「停止」按鈕

## 專案結構

```
ProjectYLT/
├── main.pyw                    # 主入口文件
├── launcher.bat                # 啟動器
├── requirements.txt            # Python依賴
├── config.json                 # 配置文件
├── README.md                   # 本文件
├── modules/                    # 核心模塊
│   ├── audio_capture.py       # WASAPI音訊捕獲
│   ├── stt_module.py          # STT語音識別
│   ├── llm_module.py          # LLM翻譯
│   ├── context_manager.py     # 情境上下文管理
│   ├── pipeline.py            # 數據流管道
│   ├── overlay_window.py      # Overlay字幕視窗
│   ├── gui_window.py          # 主GUI視窗
│   └── system_check.py        # 系統檢查
├── utils/                      # 工具模塊
│   ├── logger.py              # 日誌系統
│   └── config.py              # 配置管理
├── models/                     # 模型目錄
│   └── README.md              # 模型下載指引
└── logs/                       # 日誌文件（自動創建）
```

## 配置說明

配置文件 `config.json` 包含以下設置：

### Overlay設置
- `opacity`: 透明度 (0.0-1.0)
- `show_background`: 是否顯示文字背景
- `size`: 大小 (small/medium/large)
- `position_x`, `position_y`: 位置

### 音訊設置
- `device_index`: 音訊設備索引
- `sample_rate`: 採樣率 (預設16000)
- `chunk_duration`: 音訊塊時長（秒）

### 模型設置
- `whisper_model`: Whisper模型大小 (tiny/base/small/medium/large)
- `whisper_device`: 運行設備 (cpu/cuda)
- `whisper_compute_type`: 計算類型 (float32/float16/int8)
- `llm_model`: LLM模型路徑
- `llm_n_gpu_layers`: GPU層數
- `llm_n_ctx`: 上下文長度

### 翻譯設置
- `source_language`: 源語言 (ja)
- `target_language`: 目標語言 (zh-TW)
- `context_window_size`: 上下文視窗大小
- `update_context_interval`: 更新上下文的間隔

## 效能優化

### CPU優化
- Whisper使用int8量化，減少CPU負載
- 如果仍然卡頓，可以將模型改為 `small`

### GPU優化
- LLM使用4-bit量化，節省顯存
- 調整 `llm_n_gpu_layers` 參數（預設35層）
- 如果顯存不足，可以減少GPU層數或使用更小的模型

### 延遲優化
- 調整 `chunk_duration` 參數（預設2秒）
- 較小的值可以降低延遲，但可能影響識別準確度

## 常見問題

### Q: 無法捕獲音訊
**A**: 請確認：
- 已安裝 pyaudiowpatch
- 音訊設備正在播放聲音
- Windows音訊設備設置正確

### Q: 模型載入失敗
**A**: 請檢查：
- LLM模型文件是否存在於 `models/` 目錄
- 文件名是否正確
- 顯存是否足夠

### Q: GPU未被使用
**A**: 請確認：
- 已安裝CUDA版本的llama-cpp-python
- NVIDIA驅動程式已正確安裝
- 檢查日誌中的GPU檢測信息

### Q: 翻譯速度太慢
**A**: 可以嘗試：
- 使用更小的LLM模型
- 調整 `llm_n_gpu_layers` 參數
- 確保GPU正在使用中

### Q: Overlay無法拖曳
**A**: 請確認：
- Overlay視窗已顯示
- 沒有其他程式覆蓋在上方
- 使用滑鼠左鍵拖曳

## 技術細節

### 數據流程

```
音訊捕獲 (WASAPI) 
    ↓
語音緩衝 (2秒塊)
    ↓
STT處理 (faster-whisper, CPU)
    ↓
文本隊列
    ↓
LLM翻譯 (Qwen2.5, GPU) + 上下文管理
    ↓
顯示隊列
    ↓
Overlay更新
```

### 模塊化設計

- **獨立模塊**: 每個功能都是獨立的Python模塊
- **異步處理**: 使用多線程避免阻塞
- **隊列通信**: 模塊間使用Queue進行數據傳遞
- **易於維護**: 清晰的模塊邊界便於debug和擴展

## 開發計劃

- [ ] 支援更多語言對
- [ ] 錄製和回放功能
- [ ] 翻譯記憶庫
- [ ] 打包為獨立.exe
- [ ] 性能監控面板
- [ ] 自動更新功能

## 授權

本專案為個人開發項目。

## 致謝

- [faster-whisper](https://github.com/guillaumekln/faster-whisper) - STT引擎
- [llama.cpp](https://github.com/ggerganov/llama.cpp) - LLM推理引擎
- [Qwen](https://github.com/QwenLM/Qwen) - 翻譯模型
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI框架
- [PyAudioWPatch](https://github.com/s0d3s/PyAudioWPatch) - 音訊捕獲

## 聯絡方式

如有問題或建議，請提交Issue。

---

**ProjectYLT** - 讓語言不再是障礙 🌐
