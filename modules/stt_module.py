"""
語音轉文字模塊
使用faster-whisper進行語音識別
"""

import numpy as np
import threading
import queue
from typing import Optional, Callable, List, Tuple
from faster_whisper import WhisperModel
from utils.logger import logger


class STTModule:
    """語音轉文字模塊"""
    
    def __init__(
        self,
        model_size: str = "medium",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "ja"
    ):
        """
        初始化STT模塊
        
        Args:
            model_size: 模型大小 (tiny, base, small, medium, large)
            device: 運行設備 (cpu, cuda)
            compute_type: 計算類型 (float32, float16, int8)
            language: 識別語言
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        
        self.model: Optional[WhisperModel] = None
        self.is_ready = False
        
        self.on_partial_result: Optional[Callable[[str], None]] = None
        self.on_final_result: Optional[Callable[[str], None]] = None
        
        logger.info(f"STT模塊初始化: model={model_size}, device={device}, language={language}")
    
    def load_model(self) -> bool:
        """
        載入Whisper模型
        
        Returns:
            是否載入成功
        """
        try:
            logger.info(f"正在載入Whisper模型: {self.model_size}")
            
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                download_root="models/whisper"
            )
            
            self.is_ready = True
            logger.info("Whisper模型載入完成")
            return True
            
        except Exception as e:
            logger.error(f"載入Whisper模型時發生錯誤: {e}")
            self.is_ready = False
            return False
    
    def warm_up(self) -> None:
        """預熱模型（執行一次推理）"""
        if not self.is_ready:
            logger.warning("模型未載入，無法預熱")
            return
        
        try:
            logger.info("預熱STT模型...")
            # 創建一個短的靜音音訊進行預熱
            dummy_audio = np.zeros(16000, dtype=np.float32)
            list(self.model.transcribe(dummy_audio, language=self.language))
            logger.info("STT模型預熱完成")
        except Exception as e:
            logger.error(f"預熱STT模型時發生錯誤: {e}")
    
    def transcribe(
        self,
        audio_data: np.ndarray,
        return_timestamps: bool = True
    ) -> Tuple[str, List[dict]]:
        """
        轉錄音訊
        
        Args:
            audio_data: 音訊數據（numpy數組）
            return_timestamps: 是否返回時間戳
            
        Returns:
            (完整文本, 分段信息列表)
        """
        if not self.is_ready:
            logger.error("模型未載入，無法轉錄")
            return "", []
        
        try:
            # 轉錄音訊
            segments, info = self.model.transcribe(
                audio_data,
                language=self.language,
                beam_size=5,
                word_timestamps=return_timestamps,
                vad_filter=True,
                vad_parameters={
                    "threshold": 0.5,
                    "min_speech_duration_ms": 250,
                    "min_silence_duration_ms": 500,
                    "window_size_samples": 512,
                    "speech_pad_ms": 400
                }
            )
            
            # 收集所有分段
            full_text = ""
            segments_list = []
            
            for segment in segments:
                segment_text = segment.text.strip()
                full_text += segment_text
                
                segment_info = {
                    "text": segment_text,
                    "start": segment.start,
                    "end": segment.end,
                    "words": []
                }
                
                # 收集單詞時間戳（如果有）
                if hasattr(segment, 'words') and segment.words:
                    for word in segment.words:
                        segment_info["words"].append({
                            "word": word.word,
                            "start": word.start,
                            "end": word.end
                        })
                
                segments_list.append(segment_info)
            
            return full_text, segments_list
            
        except Exception as e:
            logger.error(f"轉錄音訊時發生錯誤: {e}")
            return "", []
    
    def transcribe_stream(
        self,
        audio_data: np.ndarray
    ) -> Tuple[str, List[str]]:
        """
        串流式轉錄（支持逐字輸出）
        
        Args:
            audio_data: 音訊數據
            
        Returns:
            (完整文本, 單詞列表)
        """
        full_text, segments = self.transcribe(audio_data, return_timestamps=True)
        
        # 提取所有單詞
        words = []
        for segment in segments:
            if segment.get("words"):
                words.extend([w["word"].strip() for w in segment["words"]])
            else:
                # 如果沒有單詞級時間戳，將句子拆分為字符（日文）
                words.extend(list(segment["text"].strip()))
        
        return full_text, words
    
    def set_callbacks(
        self,
        on_partial: Optional[Callable[[str], None]] = None,
        on_final: Optional[Callable[[str], None]] = None
    ) -> None:
        """
        設置回調函數
        
        Args:
            on_partial: 部分結果回調（逐字）
            on_final: 最終結果回調（完整句子）
        """
        self.on_partial_result = on_partial
        self.on_final_result = on_final
    
    def process_audio_chunk(self, audio_data: np.ndarray) -> None:
        """
        處理音訊塊並觸發回調
        
        Args:
            audio_data: 音訊數據
        """
        try:
            # 檢查音訊是否包含語音（簡單能量檢測）
            energy = np.sqrt(np.mean(audio_data ** 2))
            if energy < 0.01:  # 靜音閾值
                return
            
            # 轉錄音訊
            full_text, words = self.transcribe_stream(audio_data)
            
            if not full_text:
                return
            
            # 觸發部分結果回調（逐字）
            if self.on_partial_result and words:
                for word in words:
                    if word:
                        self.on_partial_result(word)
            
            # 觸發最終結果回調
            if self.on_final_result and full_text:
                self.on_final_result(full_text)
                
        except Exception as e:
            logger.error(f"處理音訊塊時發生錯誤: {e}")


class STTProcessor:
    """STT處理器（異步處理）"""
    
    def __init__(self, stt_module: STTModule):
        """
        初始化STT處理器
        
        Args:
            stt_module: STT模塊實例
        """
        self.stt = stt_module
        self.is_running = False
        self.process_thread: Optional[threading.Thread] = None
        self.audio_queue = queue.Queue(maxsize=5)
        self.result_queue = queue.Queue(maxsize=10)
    
    def start(self) -> None:
        """啟動處理器"""
        if self.is_running:
            logger.warning("STT處理器已在運行中")
            return
        
        self.is_running = True
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        logger.info("STT處理器已啟動")
    
    def stop(self) -> None:
        """停止處理器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.process_thread:
            self.process_thread.join(timeout=2.0)
        
        logger.info("STT處理器已停止")
    
    def put_audio(self, audio_data: np.ndarray) -> bool:
        """
        放入音訊數據進行處理
        
        Args:
            audio_data: 音訊數據
            
        Returns:
            是否成功放入
        """
        try:
            self.audio_queue.put_nowait(audio_data)
            return True
        except queue.Full:
            logger.warning("STT音訊隊列已滿，丟棄數據")
            return False
    
    def get_result(self, timeout: float = 0.1) -> Optional[dict]:
        """
        獲取轉錄結果
        
        Args:
            timeout: 超時時間
            
        Returns:
            結果字典或None
        """
        try:
            return self.result_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def _process_loop(self) -> None:
        """處理循環"""
        logger.debug("STT處理線程已啟動")
        
        while self.is_running:
            try:
                # 獲取音訊數據
                audio_data = self.audio_queue.get(timeout=0.5)
                
                # 轉錄
                full_text, words = self.stt.transcribe_stream(audio_data)
                
                if full_text:
                    result = {
                        "text": full_text,
                        "words": words,
                        "timestamp": threading.get_ident()
                    }
                    
                    try:
                        self.result_queue.put_nowait(result)
                    except queue.Full:
                        # 移除最舊的結果
                        try:
                            self.result_queue.get_nowait()
                            self.result_queue.put_nowait(result)
                        except:
                            pass
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"STT處理循環錯誤: {e}")
        
        logger.debug("STT處理線程已結束")

