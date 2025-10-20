"""
配置管理模塊
處理應用程式配置的讀取和保存
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from utils.logger import logger


class ConfigManager:
    """配置管理器"""
    
    DEFAULT_CONFIG = {
        "overlay": {
            "opacity": 0.9,
            "show_background": True,
            "size": "medium",
            "position_x": 100,
            "position_y": 100
        },
        "audio": {
            "device_index": 0,
            "sample_rate": 16000,
            "chunk_duration": 2.0
        },
        "models": {
            "whisper_model": "medium",
            "whisper_device": "cpu",
            "whisper_compute_type": "int8",
            "llm_model": "models/qwen2.5-7b-instruct-q4_k_m.gguf",
            "llm_n_gpu_layers": 35,
            "llm_n_ctx": 2048
        },
        "system_check": {
            "skip_check": False
        },
        "translation": {
            "source_language": "ja",
            "target_language": "zh-TW",
            "context_window_size": 5,
            "update_context_interval": 3
        }
    }
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """從文件載入配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合併預設配置和載入的配置
                    self.config = self._merge_configs(self.DEFAULT_CONFIG.copy(), loaded_config)
                    logger.info(f"配置已載入: {self.config_path}")
            except Exception as e:
                logger.error(f"載入配置失敗: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            logger.info("配置文件不存在，使用預設配置")
            self.config = self.DEFAULT_CONFIG.copy()
            self.save_config()
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置失敗: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        獲取配置值
        key_path格式: "section.subsection.key"
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> None:
        """
        設置配置值
        key_path格式: "section.subsection.key"
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        logger.debug(f"配置已更新: {key_path} = {value}")
    
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """遞歸合併兩個配置字典"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result


# 全局配置實例
config = ConfigManager()

