"""
數據流管道協調器
協調音訊捕獲、STT、LLM翻譯的整體流程
"""

import threading
import queue
import time
from typing import Optional, Callable
from modules.audio_capture import AudioCapture
from modules.stt_module import STTProcessor, STTModule
from modules.llm_module import LLMProcessor, LLMModule
from modules.context_manager import ContextManager
from utils.logger import logger


class TranslationPipeline:
    """翻譯管道"""
    
    def __init__(
        self,
        audio_capture: AudioCapture,
        stt_processor: STTProcessor,
        llm_processor: LLMProcessor,
        context_manager: ContextManager
    ):
        """
        初始化翻譯管道
        
        Args:
            audio_capture: 音訊捕獲器
            stt_processor: STT處理器
            llm_processor: LLM處理器
            context_manager: 上下文管理器
        """
        self.audio_capture = audio_capture
        self.stt_processor = stt_processor
        self.llm_processor = llm_processor
        self.context_manager = context_manager
        
        self.is_running = False
        
        # 回調函數
        self.on_partial_text: Optional[Callable[[str], None]] = None
        self.on_translation: Optional[Callable[[str, str, str], None]] = None
        
        logger.info("翻譯管道初始化完成")
    
    def set_callbacks(
        self,
        on_partial: Optional[Callable[[str], None]] = None,
        on_translation: Optional[Callable[[str, str, str], None]] = None
    ) -> None:
        """
        設置回調函數
        
        Args:
            on_partial: 部分文本回調 (text)
            on_translation: 翻譯完成回調 (original, translation, context)
        """
        self.on_partial_text = on_partial
        self.on_translation = on_translation
    
    def start(self, device_index: int = 0) -> bool:
        """
        啟動管道
        
        Args:
            device_index: 音訊設備索引
            
        Returns:
            是否啟動成功
        """
        if self.is_running:
            logger.warning("翻譯管道已在運行中")
            return False
        
        try:
            logger.info("正在啟動翻譯管道...")
            
            # 啟動各個處理器
            self.stt_processor.start()
            self.llm_processor.start()
            
            # 啟動音訊捕獲
            if not self.audio_capture.start(device_index):
                logger.error("啟動音訊捕獲失敗")
                self.stt_processor.stop()
                self.llm_processor.stop()
                return False
            
            self.is_running = True
            
            # 啟動協調線程
            threading.Thread(target=self._audio_to_stt_loop, daemon=True).start()
            threading.Thread(target=self._stt_to_llm_loop, daemon=True).start()
            threading.Thread(target=self._llm_to_display_loop, daemon=True).start()
            
            logger.info("翻譯管道已啟動")
            return True
            
        except Exception as e:
            logger.error(f"啟動翻譯管道時發生錯誤: {e}")
            self.stop()
            return False
    
    def stop(self) -> None:
        """停止管道"""
        if not self.is_running:
            return
        
        logger.info("正在停止翻譯管道...")
        
        self.is_running = False
        
        # 停止各個組件
        self.audio_capture.stop()
        self.stt_processor.stop()
        self.llm_processor.stop()
        
        logger.info("翻譯管道已停止")
    
    def _audio_to_stt_loop(self) -> None:
        """音訊 → STT 循環"""
        logger.debug("音訊→STT線程已啟動")
        
        while self.is_running:
            try:
                # 從音訊捕獲器獲取音訊塊
                audio_chunk = self.audio_capture.get_audio_chunk(timeout=0.5)
                
                if audio_chunk is not None:
                    # 放入STT處理隊列
                    self.stt_processor.put_audio(audio_chunk)
                
            except Exception as e:
                logger.error(f"音訊→STT循環錯誤: {e}")
                time.sleep(0.1)
        
        logger.debug("音訊→STT線程已結束")
    
    def _stt_to_llm_loop(self) -> None:
        """STT → LLM 循環"""
        logger.debug("STT→LLM線程已啟動")
        
        partial_text = ""
        
        while self.is_running:
            try:
                # 從STT獲取轉錄結果
                result = self.stt_processor.get_result(timeout=0.1)
                
                if result:
                    text = result.get("text", "")
                    words = result.get("words", [])
                    
                    if text:
                        # 更新部分文本顯示（逐字）
                        if self.on_partial_text and words:
                            for word in words:
                                if word and word not in partial_text:
                                    self.on_partial_text(word)
                                    partial_text += word
                        
                        # 放入LLM翻譯隊列
                        self.llm_processor.put_text(text)
                        
                        # 重置部分文本
                        partial_text = ""
                
            except Exception as e:
                logger.error(f"STT→LLM循環錯誤: {e}")
                time.sleep(0.1)
        
        logger.debug("STT→LLM線程已結束")
    
    def _llm_to_display_loop(self) -> None:
        """LLM → 顯示 循環"""
        logger.debug("LLM→顯示線程已啟動")
        
        while self.is_running:
            try:
                # 從LLM獲取翻譯結果
                result = self.llm_processor.get_result(timeout=0.1)
                
                if result:
                    original = result.get("original", "")
                    translation = result.get("translation", "")
                    context = result.get("context", "")
                    
                    if translation and self.on_translation:
                        self.on_translation(original, translation, context)
                
            except Exception as e:
                logger.error(f"LLM→顯示循環錯誤: {e}")
                time.sleep(0.1)
        
        logger.debug("LLM→顯示線程已結束")


class PipelineBuilder:
    """管道構建器"""
    
    @staticmethod
    def build_from_config(config) -> Optional[TranslationPipeline]:
        """
        從配置構建管道
        
        Args:
            config: 配置管理器
            
        Returns:
            翻譯管道實例或None
        """
        try:
            logger.info("正在構建翻譯管道...")
            
            # 創建音訊捕獲器
            audio_capture = AudioCapture(
                sample_rate=config.get("audio.sample_rate", 16000),
                chunk_duration=config.get("audio.chunk_duration", 2.0)
            )
            
            # 創建STT模塊
            stt_module = STTModule(
                model_size=config.get("models.whisper_model", "medium"),
                device=config.get("models.whisper_device", "cpu"),
                compute_type=config.get("models.whisper_compute_type", "int8"),
                language=config.get("translation.source_language", "ja")
            )
            
            # 創建上下文管理器
            context_manager = ContextManager(
                window_size=config.get("translation.context_window_size", 5),
                update_interval=config.get("translation.update_context_interval", 3)
            )
            
            # 創建LLM模塊
            llm_module = LLMModule(
                model_path=config.get("models.llm_model", "models/qwen2.5-7b-instruct-q4_k_m.gguf"),
                n_gpu_layers=config.get("models.llm_n_gpu_layers", 35),
                n_ctx=config.get("models.llm_n_ctx", 2048)
            )
            
            # 創建處理器
            stt_processor = STTProcessor(stt_module)
            llm_processor = LLMProcessor(llm_module, context_manager)
            
            # 創建管道
            pipeline = TranslationPipeline(
                audio_capture,
                stt_processor,
                llm_processor,
                context_manager
            )
            
            logger.info("翻譯管道構建完成")
            return pipeline
            
        except Exception as e:
            logger.error(f"構建翻譯管道時發生錯誤: {e}")
            return None
    
    @staticmethod
    def load_models(pipeline: TranslationPipeline) -> bool:
        """
        載入管道中的所有模型
        
        Args:
            pipeline: 翻譯管道實例
            
        Returns:
            是否全部載入成功
        """
        try:
            logger.info("正在載入模型...")
            
            # 載入STT模型
            if not pipeline.stt_processor.stt.load_model():
                logger.error("載入STT模型失敗")
                return False
            
            # 載入LLM模型
            if not pipeline.llm_processor.llm.load_model():
                logger.error("載入LLM模型失敗")
                return False
            
            logger.info("所有模型載入完成")
            return True
            
        except Exception as e:
            logger.error(f"載入模型時發生錯誤: {e}")
            return False
    
    @staticmethod
    def warm_up_models(pipeline: TranslationPipeline) -> None:
        """
        預熱管道中的所有模型
        
        Args:
            pipeline: 翻譯管道實例
        """
        try:
            logger.info("正在預熱模型...")
            
            # 預熱STT模型
            pipeline.stt_processor.stt.warm_up()
            
            # 預熱LLM模型
            pipeline.llm_processor.llm.warm_up()
            
            logger.info("所有模型預熱完成")
            
        except Exception as e:
            logger.error(f"預熱模型時發生錯誤: {e}")

