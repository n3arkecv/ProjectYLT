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
- **文件大小**: 約 4.4GB
- **顯存需求**: 約 5-6GB

### 下載步驟

1. 前往 Hugging Face 模型頁面:
   ```
   https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF
   ```

2. 下載文件 `qwen2.5-7b-instruct-q4_k_m.gguf`

3. 將下載的文件放置在此目錄下:
   ```
   ProjectYLT/models/qwen2.5-7b-instruct-q4_k_m.gguf
   ```

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

