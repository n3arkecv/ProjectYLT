# 快速啟動指南

## 5分鐘快速開始

### 步驟 1: 檢查環境

確保你已安裝：
- Python 3.10 或更高版本
- NVIDIA GPU 驅動（用於 GPU 加速）

檢查 Python 版本：
```bash
python --version
```

### 步驟 2: 安裝依賴

在專案目錄下執行：
```bash
pip install -r requirements.txt
```

### 步驟 3: 下載 LLM 模型

1. 前往 https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF
2. 下載 `qwen2.5-7b-instruct-q4_k_m.gguf` (約 4.4GB)
3. 將文件放入 `models/` 目錄

驗證模型位置：
```
ProjectYLT/
└── models/
    └── qwen2.5-7b-instruct-q4_k_m.gguf  ← 確保文件在這裡
```

### 步驟 4: 啟動應用程式

雙擊 `launcher.bat` 或執行：
```bash
pythonw main.pyw
```

### 步驟 5: 開始使用

1. **等待模型載入** - 首次啟動會下載 Whisper 模型（約 1.5GB）
2. **選擇音訊設備** - 預設會使用系統音訊
3. **調整 Overlay** - 可以拖曳到合適位置
4. **點擊開始** - 開始即時翻譯！

## 常見首次啟動問題

### ❌ "模型文件不存在"

**解決方法**:
- 確認 LLM 模型已下載到 `models/` 目錄
- 檢查文件名是否正確

### ❌ "套件未安裝: xxx"

**解決方法**:
```bash
pip install -r requirements.txt --upgrade
```

### ❌ "CUDA out of memory"

**解決方法**:
1. 關閉其他使用 GPU 的程式
2. 或使用較小的模型（Qwen 3B 或 1.5B）
3. 或減少 GPU 層數：
   編輯 `config.json`:
   ```json
   "llm_n_gpu_layers": 20  // 從 35 減少到 20
   ```

### ❌ "無法捕獲音訊"

**解決方法**:
1. 確認 Windows 音訊正在播放
2. 在主 GUI 中選擇正確的音訊設備
3. 嘗試重新整理設備列表

## GPU 加速設置（可選）

如需 GPU 加速，安裝支援 CUDA 的版本：

```bash
# 卸載 CPU 版本
pip uninstall llama-cpp-python -y

# 安裝 CUDA 12.x 版本
pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122
```

驗證 GPU 可用：
- 啟動應用後查看日誌
- 應該會顯示 "檢測到 NVIDIA GPU: ..."

## 基本配置

### 調整 Overlay

在主 GUI 中：
- **透明度**: 滑動滑桿調整
- **文字背景**: 勾選/取消勾選
- **大小**: 選擇小/中/大

### 選擇音訊設備

1. 點擊「重新整理」按鈕
2. 在下拉選單中選擇設備
3. 預設選項會捕獲所有系統音訊

## 效能調整

### 如果翻譯太慢

1. **確認 GPU 正在使用**
   - 查看日誌中的 GPU 信息

2. **使用更小的模型**
   - 下載 Qwen 3B 或 1.5B
   - 修改 `config.json` 中的模型路徑

3. **減少 Whisper 模型大小**
   - 編輯 `config.json`:
   ```json
   "whisper_model": "small"  // 從 medium 改為 small
   ```

### 如果原文識別不準確

1. **使用更大的 Whisper 模型**
   ```json
   "whisper_model": "large"
   ```

2. **調整音訊塊大小**
   ```json
   "chunk_duration": 3.0  // 從 2.0 增加到 3.0
   ```

## 進階使用

### 修改配置文件

編輯 `config.json` 可以調整所有參數。修改後重啟應用程式生效。

主要參數：
```json
{
  "overlay": {
    "opacity": 0.9,        // 透明度
    "size": "medium"       // 大小
  },
  "models": {
    "whisper_model": "medium",              // STT 模型
    "llm_model": "models/...",              // LLM 模型路徑
    "llm_n_gpu_layers": 35                  // GPU 層數
  },
  "translation": {
    "context_window_size": 5,               // 上下文視窗
    "update_context_interval": 3            // 更新間隔
  }
}
```

### 查看詳細日誌

日誌文件位於 `logs/` 目錄，按時間命名。

查看最新日誌：
```bash
# Windows
type logs\app_*.log | more

# 或使用文本編輯器打開
```

## 需要幫助？

1. 查看完整文檔：`README.md`
2. 查看開發指南：`DEVELOPMENT.md`
3. 檢查系統日誌：`logs/` 目錄
4. 提交 Issue（如果是 bug）

## 下一步

- 🎨 自訂 Overlay 外觀
- 🎯 調整翻譯參數
- 📝 查看進階功能文檔

祝使用愉快！🎉

