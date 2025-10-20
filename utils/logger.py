"""
日誌系統模塊
提供統一的日誌記錄功能
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class AppLogger:
    """應用程式日誌管理器"""
    
    _instance: Optional['AppLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is not None:
            return
            
        self._logger = logging.getLogger('ProjectYLT')
        self._logger.setLevel(logging.DEBUG)
        
        # 創建logs目錄
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # 文件處理器
        log_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加處理器
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        
        self.callbacks = []  # GUI回調列表
    
    def add_gui_callback(self, callback):
        """添加GUI日誌回調函數"""
        self.callbacks.append(callback)
    
    def _notify_gui(self, level: str, message: str):
        """通知GUI更新日誌"""
        for callback in self.callbacks:
            try:
                callback(level, message)
            except Exception as e:
                self._logger.error(f"GUI回調錯誤: {e}")
    
    def debug(self, message: str):
        """Debug級別日誌"""
        self._logger.debug(message)
        self._notify_gui('DEBUG', message)
    
    def info(self, message: str):
        """Info級別日誌"""
        self._logger.info(message)
        self._notify_gui('INFO', message)
    
    def warning(self, message: str):
        """Warning級別日誌"""
        self._logger.warning(message)
        self._notify_gui('WARNING', message)
    
    def error(self, message: str):
        """Error級別日誌"""
        self._logger.error(message)
        self._notify_gui('ERROR', message)
    
    def critical(self, message: str):
        """Critical級別日誌"""
        self._logger.critical(message)
        self._notify_gui('CRITICAL', message)


# 全局日誌實例
logger = AppLogger()

