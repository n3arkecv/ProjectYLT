"""
系統檢查模塊
檢查運行環境和必要的依賴
"""

import sys
import platform
from pathlib import Path
from typing import List, Tuple, Optional
from utils.logger import logger


class SystemCheck:
    """系統檢查器"""
    
    def __init__(self):
        """初始化系統檢查器"""
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
    
    def check_all(self, skip_check: bool = False) -> Tuple[bool, List[str]]:
        """
        執行所有檢查
        
        Args:
            skip_check: 是否跳過檢查
            
        Returns:
            (是否通過, 錯誤/警告消息列表)
        """
        if skip_check:
            logger.info("已跳過系統檢查")
            return True, []
        
        logger.info("開始系統檢查...")
        
        self.checks_passed = []
        self.checks_failed = []
        self.warnings = []
        
        # 執行各項檢查
        self._check_python_version()
        self._check_platform()
        self._check_packages()
        self._check_gpu()
        self._check_models()
        
        # 生成報告
        messages = []
        
        if self.checks_failed:
            messages.append("=== 檢查失敗項目 ===")
            messages.extend(self.checks_failed)
            messages.append("")
        
        if self.warnings:
            messages.append("=== 警告 ===")
            messages.extend(self.warnings)
            messages.append("")
        
        if self.checks_passed:
            messages.append("=== 檢查通過項目 ===")
            messages.extend(self.checks_passed)
        
        # 判斷是否通過
        all_passed = len(self.checks_failed) == 0
        
        if all_passed:
            logger.info("系統檢查全部通過")
        else:
            logger.error(f"系統檢查失敗: {len(self.checks_failed)}項")
        
        return all_passed, messages
    
    def _check_python_version(self) -> None:
        """檢查Python版本"""
        try:
            version = sys.version_info
            version_str = f"{version.major}.{version.minor}.{version.micro}"
            
            if version.major == 3 and version.minor >= 10:
                self.checks_passed.append(f"✓ Python版本: {version_str}")
                logger.debug(f"Python版本檢查通過: {version_str}")
            else:
                self.checks_failed.append(f"✗ Python版本不符: {version_str} (需要 3.10+)")
                logger.error(f"Python版本不符: {version_str}")
        except Exception as e:
            self.checks_failed.append(f"✗ 無法檢查Python版本: {e}")
    
    def _check_platform(self) -> None:
        """檢查操作系統平台"""
        try:
            system = platform.system()
            release = platform.release()
            
            self.checks_passed.append(f"✓ 操作系統: {system} {release}")
            logger.debug(f"操作系統: {system} {release}")
            
            if system != "Windows":
                self.warnings.append(f"⚠ 本應用主要在Windows上測試，當前系統: {system}")
        except Exception as e:
            self.warnings.append(f"⚠ 無法檢查操作系統: {e}")
    
    def _check_packages(self) -> None:
        """檢查必要的Python套件"""
        required_packages = [
            ("PyQt6", "PyQt6"),
            ("pyaudiowpatch", "pyaudiowpatch"),
            ("faster_whisper", "faster-whisper"),
            ("llama_cpp", "llama-cpp-python"),
            ("numpy", "numpy")
        ]
        
        for import_name, package_name in required_packages:
            try:
                __import__(import_name)
                self.checks_passed.append(f"✓ 套件已安裝: {package_name}")
                logger.debug(f"套件檢查通過: {package_name}")
            except ImportError:
                self.checks_failed.append(f"✗ 套件未安裝: {package_name}")
                logger.error(f"套件未安裝: {package_name}")
    
    def _check_gpu(self) -> None:
        """檢查GPU和CUDA"""
        try:
            # 嘗試導入llama_cpp並檢查GPU
            try:
                from llama_cpp import Llama
                
                # 檢查是否有CUDA支持
                # 這裡我們只做基本檢查，實際CUDA可用性在載入模型時才能確定
                self.checks_passed.append("✓ llama-cpp-python已安裝（GPU支持需在模型載入時驗證）")
                logger.debug("llama-cpp-python可用")
            except Exception as e:
                self.warnings.append(f"⚠ llama-cpp-python載入警告: {e}")
            
            # 嘗試檢查NVIDIA GPU
            try:
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    gpu_info = result.stdout.strip()
                    self.checks_passed.append(f"✓ 檢測到NVIDIA GPU: {gpu_info}")
                    logger.info(f"GPU檢測: {gpu_info}")
                else:
                    self.warnings.append("⚠ 未檢測到NVIDIA GPU，LLM將運行在CPU上")
            except FileNotFoundError:
                self.warnings.append("⚠ nvidia-smi未找到，無法檢測GPU")
            except Exception as e:
                self.warnings.append(f"⚠ GPU檢測錯誤: {e}")
                
        except Exception as e:
            self.warnings.append(f"⚠ GPU檢查錯誤: {e}")
    
    def _check_models(self) -> None:
        """檢查模型文件"""
        # 檢查models目錄
        models_dir = Path("models")
        
        if not models_dir.exists():
            self.checks_failed.append("✗ models目錄不存在")
            logger.error("models目錄不存在")
            return
        
        # 檢查LLM模型
        llm_model_path = models_dir / "qwen2.5-7b-instruct-q4_k_m.gguf"
        
        if llm_model_path.exists():
            size_mb = llm_model_path.stat().st_size / (1024 * 1024)
            self.checks_passed.append(f"✓ LLM模型已存在: {llm_model_path.name} ({size_mb:.1f}MB)")
            logger.info(f"LLM模型已找到: {size_mb:.1f}MB")
        else:
            self.checks_failed.append(f"✗ LLM模型不存在: {llm_model_path}")
            logger.error(f"LLM模型不存在: {llm_model_path}")
            
            # 提供下載指引
            self.warnings.append("")
            self.warnings.append("請下載LLM模型:")
            self.warnings.append("1. 前往: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF")
            self.warnings.append("2. 下載: qwen2.5-7b-instruct-q4_k_m.gguf")
            self.warnings.append(f"3. 放置到: {llm_model_path.absolute()}")
            self.warnings.append("")
        
        # Whisper模型會自動下載，只需提示
        whisper_dir = models_dir / "whisper"
        if whisper_dir.exists() and any(whisper_dir.iterdir()):
            self.checks_passed.append("✓ Whisper模型已下載")
            logger.debug("Whisper模型已存在")
        else:
            self.warnings.append("⚠ Whisper模型將在首次運行時自動下載")
    
    def get_model_download_instructions(self) -> str:
        """
        獲取模型下載說明
        
        Returns:
            下載說明文本
        """
        instructions = """
=== 模型下載指引 ===

LLM模型 (必需):
  名稱: Qwen2.5-7B-Instruct (GGUF 4-bit)
  下載: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF
  文件: qwen2.5-7b-instruct-q4_k_m.gguf
  大小: 約 4.4GB
  放置: ProjectYLT/models/qwen2.5-7b-instruct-q4_k_m.gguf

Whisper模型 (自動下載):
  名稱: faster-whisper medium
  說明: 首次運行時會自動下載
  大小: 約 1.5GB
  
如果顯存不足 (RTX 4070 8GB)，可使用較小的模型:
  - Qwen2.5-3B-Instruct (Q4_K_M): ~2GB 顯存
  - Qwen2.5-1.5B-Instruct (Q4_K_M): ~1GB 顯存

下載完成後，請重新啟動應用程式。
"""
        return instructions


def show_check_results(results: List[str]) -> None:
    """
    顯示檢查結果（控制台）
    
    Args:
        results: 結果消息列表
    """
    print("\n" + "=" * 60)
    print("系統檢查結果")
    print("=" * 60)
    
    for msg in results:
        print(msg)
    
    print("=" * 60 + "\n")


def create_check_dialog(parent, results: List[str], passed: bool):
    """
    創建檢查結果對話框
    
    Args:
        parent: 父視窗
        results: 結果消息列表
        passed: 是否通過檢查
    """
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
    from PyQt6.QtCore import Qt
    
    dialog = QDialog(parent)
    dialog.setWindowTitle("系統檢查結果")
    dialog.setModal(True)
    dialog.resize(600, 400)
    
    layout = QVBoxLayout()
    
    # 狀態標籤
    if passed:
        status_label = QLabel("✓ 系統檢查通過")
        status_label.setStyleSheet("color: #4CAF50; font-size: 16px; font-weight: bold;")
    else:
        status_label = QLabel("✗ 系統檢查未通過")
        status_label.setStyleSheet("color: #f44336; font-size: 16px; font-weight: bold;")
    
    status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(status_label)
    
    # 結果文本
    result_text = QTextEdit()
    result_text.setReadOnly(True)
    result_text.setPlainText("\n".join(results))
    layout.addWidget(result_text)
    
    # 確定按鈕
    ok_button = QPushButton("確定")
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(ok_button)
    
    dialog.setLayout(layout)
    
    return dialog

