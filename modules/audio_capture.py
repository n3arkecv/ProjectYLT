"""
音訊捕獲模塊
使用WASAPI loopback捕獲系統音訊
"""

import numpy as np
import pyaudiowpatch as pyaudio
import threading
import queue
import time
from typing import Optional, List, Dict, Callable
from utils.logger import logger
from scipy import signal


class AudioCapture:
    """WASAPI音訊捕獲器"""
    
    def __init__(self, sample_rate: int = 16000, chunk_duration: float = 2.0):
        """
        初始化音訊捕獲器
        
        Args:
            sample_rate: 採樣率（Hz）
            chunk_duration: 音訊塊持續時間（秒）
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.device_info: Optional[Dict] = None
        
        self.is_running = False
        self.capture_thread: Optional[threading.Thread] = None
        self.audio_queue = queue.Queue(maxsize=10)
        
        self.buffer = np.array([], dtype=np.float32)
        
        # 音訊處理參數
        self.source_sample_rate = None  # 來源音訊的實際採樣率
        self.source_channels = None     # 來源音訊的實際通道數
        self.resample_filter = None     # 重採樣濾波器
        
        logger.info(f"音訊捕獲器初始化: 採樣率={sample_rate}Hz, 塊大小={chunk_duration}秒")
    
    def _setup_audio_processing(self, source_rate: int, source_channels: int) -> None:
        """
        設置音訊處理參數
        
        Args:
            source_rate: 來源音訊採樣率
            source_channels: 來源音訊通道數
        """
        self.source_sample_rate = source_rate
        self.source_channels = source_channels
        
        # 如果來源採樣率與目標不同，設置重採樣濾波器
        if source_rate != self.sample_rate:
            # 計算重採樣比例
            resample_ratio = self.sample_rate / source_rate
            
            # 設計抗混疊濾波器
            nyquist = min(source_rate, self.sample_rate) / 2
            cutoff = 0.8 * nyquist  # 80%的奈奎斯特頻率
            
            # 設計低通濾波器
            self.resample_filter = signal.butter(4, cutoff, btype='low', fs=source_rate, output='sos')
            
            logger.info(f"設置音訊重採樣: {source_rate}Hz -> {self.sample_rate}Hz, 通道數: {source_channels} -> 1")
        else:
            self.resample_filter = None
            logger.info(f"無需重採樣: {source_rate}Hz, 通道數: {source_channels} -> 1")
    
    def _process_audio_data(self, raw_data: np.ndarray) -> np.ndarray:
        """
        處理原始音訊數據
        
        Args:
            raw_data: 原始音訊數據
            
        Returns:
            處理後的音訊數據
        """
        # 如果是多聲道，轉換為單聲道（取平均值）
        if len(raw_data.shape) > 1 and raw_data.shape[1] > 1:
            processed_data = np.mean(raw_data, axis=1)
        else:
            processed_data = raw_data.flatten()
        
        # 如果採樣率不同，進行重採樣
        if self.resample_filter is not None and self.source_sample_rate != self.sample_rate:
            # 使用sosfilt進行濾波
            filtered_data = signal.sosfilt(self.resample_filter, processed_data)
            
            # 重採樣
            num_samples = int(len(filtered_data) * self.sample_rate / self.source_sample_rate)
            processed_data = signal.resample(filtered_data, num_samples)
        else:
            processed_data = processed_data
        
        # 確保數據類型為float32
        processed_data = processed_data.astype(np.float32)
        
        # 正規化音量（避免削波）
        max_val = np.max(np.abs(processed_data))
        if max_val > 0:
            processed_data = processed_data / max_val * 0.8
        
        return processed_data
    
    def list_devices(self) -> List[Dict]:
        """
        列出所有音訊設備
        
        Returns:
            設備信息列表
        """
        devices = []
        
        try:
            # 列出所有設備
            device_count = self.audio.get_device_count()
            
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                
                # 只列出有輸入能力的設備
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'input_channels': device_info['maxInputChannels'],
                        'output_channels': device_info['maxOutputChannels'],
                        'sample_rate': int(device_info['defaultSampleRate']),
                        'host_api': device_info['hostApi']
                    })
                    logger.debug(f"找到設備: {device_info['name']} (輸入通道: {device_info['maxInputChannels']})")
            
        except Exception as e:
            logger.error(f"列出音訊設備時發生錯誤: {e}")
        
        return devices
    
    def set_device(self, device_index: int = 0) -> bool:
        """
        設置要使用的音訊設備
        
        Args:
            device_index: 設備索引
            
        Returns:
            是否設置成功
        """
        try:
            # 如果device_index為0，使用預設輸入設備
            if device_index == 0:
                # 獲取預設輸入設備
                self.device_info = self.audio.get_default_input_device_info()
                logger.info(f"使用預設輸入設備: {self.device_info['name']}")
            else:
                # 使用指定索引的設備
                self.device_info = self.audio.get_device_info_by_index(device_index)
                logger.info(f"已設置音訊設備: {self.device_info['name']}")
            
            # 設置音訊處理參數
            self._setup_audio_processing(
                int(self.device_info['defaultSampleRate']),
                self.device_info['maxInputChannels']
            )
            return True
                
        except Exception as e:
            logger.error(f"設置音訊設備時發生錯誤: {e}")
            return False
    
    def start(self, device_index: int = 0) -> bool:
        """
        開始捕獲音訊
        
        Args:
            device_index: 設備索引
            
        Returns:
            是否啟動成功
        """
        if self.is_running:
            logger.warning("音訊捕獲已在運行中")
            return False
        
        # 設置設備
        if not self.set_device(device_index):
            return False
        
        try:
            # 使用設備的原始通道數和採樣率開啟音訊流
            device_channels = self.device_info['maxInputChannels'] if self.device_info else 1
            device_sample_rate = int(self.device_info['defaultSampleRate']) if self.device_info else 44100
            
            logger.info(f"嘗試開啟音訊流: 設備通道數={device_channels}, 設備採樣率={device_sample_rate}Hz")
            
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=device_channels,  # 使用設備的原始通道數
                rate=device_sample_rate,    # 使用設備的原始採樣率
                input=True,
                frames_per_buffer=1024,
                input_device_index=self.device_info['index'] if self.device_info else None
            )

            logger.info("音訊流開啟成功")
            
            self.is_running = True
            self.buffer = np.array([], dtype=np.float32)
            
            # 啟動捕獲線程
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.info("音訊捕獲已開始")
            return True
            
        except Exception as e:
            logger.error(f"啟動音訊捕獲時發生錯誤: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> None:
        """停止捕獲音訊"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 等待捕獲線程結束
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        
        # 關閉音訊流
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        logger.info("音訊捕獲已停止")
    
    def _capture_loop(self) -> None:
        """音訊捕獲循環（在獨立線程中運行）"""
        logger.debug("音訊捕獲線程已啟動")
        
        while self.is_running:
            try:
                if self.stream and self.stream.is_active():
                    # 讀取音訊數據
                    data = self.stream.read(1024, exception_on_overflow=False)
                    
                    # 根據設備通道數重新整形數據
                    if self.source_channels and self.source_channels > 1:
                        # 多聲道數據
                        audio_data = np.frombuffer(data, dtype=np.float32)
                        audio_data = audio_data.reshape(-1, self.source_channels)
                    else:
                        # 單聲道數據
                        audio_data = np.frombuffer(data, dtype=np.float32)
                    
                    # 處理音訊數據（重採樣、通道轉換等）
                    processed_data = self._process_audio_data(audio_data)
                    
                    # 添加到緩衝區
                    self.buffer = np.concatenate([self.buffer, processed_data])
                    
                    # 當緩衝區達到目標大小時，放入隊列
                    if len(self.buffer) >= self.chunk_size:
                        chunk = self.buffer[:self.chunk_size]
                        self.buffer = self.buffer[self.chunk_size:]
                        
                        # 放入隊列（如果隊列滿了，丟棄舊數據）
                        try:
                            self.audio_queue.put_nowait(chunk)
                        except queue.Full:
                            # 隊列滿了，移除最舊的數據
                            try:
                                self.audio_queue.get_nowait()
                                self.audio_queue.put_nowait(chunk)
                            except:
                                pass
                else:
                    time.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"音訊捕獲循環錯誤: {e}")
                time.sleep(0.1)
        
        logger.debug("音訊捕獲線程已結束")
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        獲取一個音訊塊
        
        Args:
            timeout: 超時時間（秒）
            
        Returns:
            音訊數據（numpy數組）或None
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def clear_queue(self) -> None:
        """清空音訊隊列"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def __del__(self):
        """析構函數"""
        self.stop()
        if self.audio:
            self.audio.terminate()

