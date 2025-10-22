# 模型文件目錄

此目錄用於存放AI模型文件。

## 所需模型

### 1. Whisper STT 模型
- **說明**: faster-whisper會在首次運行時自動下載
- **模型大小**: medium (~1.5GB)
- **無需手動下載**

### 2. Qwen2.5 LLM 模型
- **模型名稱**: Qwen2.5-7B-Instruct (GGUF 4-bit量化)
- **下載來源**: [Hugging Face](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)
- **所需文件**: `qwen2.5-7b-instruct-q4_k_m.gguf`
- **文件大小**: 約 4.4GB（分割為兩個文件）
- **顯存需求**: 約 5-6GB

### 下載步驟

#### 🌟 推薦方法：使用自動下載工具

**最簡單的方式：** 直接雙擊本目錄下的 `download_model.bat`

這個工具會自動：
1. ✅ 安裝 Hugging Face CLI
2. ✅ 讓您選擇模型（7B / 3B / 1.5B）
3. ✅ 自動下載模型（正確處理分割文件）
4. ✅ 自動更新 config.json

**模型選擇建議：**

| 模型 | 大小 | 顯存 | 品質 | 適用場景 |
|------|------|------|------|----------|
| **Qwen2.5-7B** | 4.4GB | 5-6GB | 最佳 | **RTX 4070 8GB（推薦）** |
| Qwen2.5-3B | 2.0GB | 2-3GB | 良好 | 顯存不足或追求速度 |
| Qwen2.5-1.5B | 1.0GB | 1-2GB | 尚可 | 低顯存或快速測試 |

#### 📦 手動下載方法（進階用戶）

**方法 1：使用 Hugging Face CLI（推薦）**

```bash
# 安裝 CLI
pip install -U "huggingface_hub[cli]"

# 下載 7B 模型
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_k_m.gguf --local-dir . --local-dir-use-symlinks False

# 或下載 3B 模型
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf --local-dir . --local-dir-use-symlinks False

# 或下載 1.5B 模型
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct-GGUF qwen2.5-1.5b-instruct-q4_k_m.gguf --local-dir . --local-dir-use-symlinks False
```

**方法 2：手動合併分割文件**

如果下載了分割文件，需要使用 `llama-gguf-split` 工具合併：

```bash
# 使用 llama-gguf-split 合併（官方方法）
llama-gguf-split --merge qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf qwen2.5-7b-instruct-q4_k_m.gguf
```

或直接執行提供的批次文件：
```
雙擊 models/merge_with_llama_tool.bat
```

**獲取 llama-gguf-split 工具：**
- 從 [llama.cpp releases](https://github.com/ggerganov/llama.cpp/releases) 下載
- 或安裝：`pip install llama-cpp-python`（包含此工具）

### 替代模型（如果顯存不足）

如果 RTX 4070 8GB 顯存不足，可以使用更小的模型：

- **Qwen2.5-3B-Instruct** (Q4_K_M): ~2GB 顯存
- **Qwen2.5-1.5B-Instruct** (Q4_K_M): ~1GB 顯存

## 目錄結構

```
models/
├── README.md                              # 本文件
├── qwen2.5-7b-instruct-q4_k_m.gguf       # LLM模型（需下載）
└── .gitkeep
```

注意：模型文件較大，不應提交到Git倉庫。

