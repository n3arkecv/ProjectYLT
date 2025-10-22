# 快速啟動指南

## 5分鐘快速開始

### 步驟 1: 檢查環境

確保你已安裝：
- Python 3.10 或更高版本
- NVIDIA GPU 驅動（用於 GPU 加速）
- **Visual Studio Build Tools 2022**（重要！）

檢查 Python 版本：
```bash
python --version
```

### 步驟 1.5: 安裝 Visual Studio Build Tools 2022

⚠️ **這是必需的！** llama-cpp-python 需要 C++ 編譯器。

**快速安裝：**
1. 下載: https://visualstudio.microsoft.com/zh-hant/downloads/
2. 選擇「Build Tools for Visual Studio 2022」
3. 安裝時勾選「Desktop development with C++」
4. 重新啟動電腦

詳細說明請參閱 README.md。

### 步驟 2: 安裝依賴

在專案目錄下執行：
```bash
pip install -r requirements.txt
```

### 步驟 3: 下載 LLM 模型

⭐ **推薦方法：使用自動下載工具**

只需雙擊 `models/download_model.bat`，腳本會自動：
- ✅ 安裝 Hugging Face CLI
- ✅ 讓您選擇模型（7B / 3B / 1.5B）
- ✅ 自動下載模型（正確處理分割文件）
- ✅ 自動更新 config.json

**操作步驟：**
1. 雙擊 `models/download_model.bat`
2. 按照提示選擇模型（建議選擇 1 = 7B 模型）
3. 確認下載
4. 等待完成（會顯示進度）

**模型選項說明：**

| 選項 | 模型 | 大小 | 顯存 | 品質 | 適用場景 |
|------|------|------|------|------|----------|
| **1** | **Qwen2.5-7B** | 4.4GB | 5-6GB | 最佳 | **RTX 4070 8GB（推薦）** |
| 2 | Qwen2.5-3B | 2.0GB | 2-3GB | 良好 | 顯存不足或追求速度 |
| 3 | Qwen2.5-1.5B | 1.0GB | 1-2GB | 尚可 | 低顯存或快速測試 |

---

<details>
<summary>📌 手動下載方法（點擊展開，不推薦）</summary>

**使用 Hugging Face CLI：**

```bash
# 安裝 CLI
pip install -U "huggingface_hub[cli]"

# 下載 7B 模型
huggingface-cli download Qwen/Qwen2.5-7B-Instruct-GGUF qwen2.5-7b-instruct-q4_k_m.gguf --local-dir models --local-dir-use-symlinks False

# 或下載 3B 模型
huggingface-cli download Qwen/Qwen2.5-3B-Instruct-GGUF qwen2.5-3b-instruct-q4_k_m.gguf --local-dir models --local-dir-use-symlinks False
```

**從網頁下載（不推薦，會遇到分割文件問題）：**

不建議手動從網頁下載，因為會遇到文件分割和合併的問題。請使用自動下載工具。

</details>

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

### ❌ "模型文件不存在" 或 載入模型錯誤

**最佳解決方法**:
1. **雙擊 `models/download_model.bat`** 使用自動下載工具
2. 選擇模型（建議選擇 1 = 7B 模型）
3. 等待下載完成
4. 重新啟動應用程式

**正確的合併方法**（根據[官方文檔](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)）:
- 需要使用 `llama-gguf-split --merge` 工具
- 這是 llama.cpp 的官方合併工具
- Windows 的 `copy /b` 命令**無法**正確合併 GGUF 文件
- 自動下載工具會處理合併（如果已安裝 llama.cpp）

### ❌ "套件未安裝: xxx"

**解決方法**:
```bash
pip install -r requirements.txt --upgrade
```

### ❌ "未檢測到 Visual Studio Build Tools 2022"

**解決方法**:
1. 下載並安裝 Visual Studio Build Tools 2022
2. 確保選擇「Desktop development with C++」工作負載
3. 重新啟動電腦
4. 重新運行應用程式

### ❌ llama-cpp-python 編譯錯誤

**解決方法**:
1. 確認 Visual Studio Build Tools 已安裝
2. 重新啟動電腦
3. 使用預編譯版本：
   ```bash
   pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cu122
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

