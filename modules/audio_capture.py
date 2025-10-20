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
        
        logger.info(f"音訊捕獲器初始化: 採樣率={sample_rate}Hz, 塊大小={chunk_duration}秒")
    
    def list_devices(self) -> List[Dict]:
        """
        列出所有WASAPI loopback設備
        
        Returns:
            設備信息列表
        """
        devices = []
        
        try:
            # 查找所有loopback設備
            wasapi_info = self.audio.get_host_api_info_by_type(pyaudio.paWASAPI)
            
            for i in range(wasapi_info['deviceCount']):
                device_info = self.audio.get_device_info_by_host_api_device_index(
                    wasapi_info['index'], i
                )
                
                # 只列出loopback設備（輸出設備）
                if device_info['maxOutputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxOutputChannels'],
                        'sample_rate': int(device_info['defaultSampleRate'])
                    })
                    logger.debug(f"找到設備: {device_info['name']}")
            
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
            wasapi_info = self.audio.get_host_api_info_by_type(pyaudio.paWASAPI)
            
            # 如果device_index為0，使用預設loopback設備
            if device_index == 0:
                # 獲取預設輸出設備
                default_device = self.audio.get_default_output_device_info()
                device_name = default_device['name']
                
                # 查找對應的loopback設備
                for i in range(wasapi_info['deviceCount']):
                    device_info = self.audio.get_device_info_by_host_api_device_index(
                        wasapi_info['index'], i
                    )
                    if device_info['name'] == device_name and device_info['maxOutputChannels'] > 0:
                        # 查找loopback版本（通常名稱相同但isLoopback為True）
                        if device_info.get('isLoopbackDevice', False):
                            self.device_info = device_info
                            logger.info(f"已設置音訊設備: {device_info['name']}")
                            return True
                
                # 如果沒有找到明確的loopback標記，使用預設設備作為loopback
                self.device_info = default_device
                logger.info(f"使用預設設備作為loopback: {default_device['name']}")
                return True
            else:
                # 使用指定索引的設備
                device_info = self.audio.get_device_info_by_host_api_device_index(
                    wasapi_info['index'], device_index
                )
                self.device_info = device_info
                logger.info(f"已設置音訊設備: {device_info['name']}")
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
            # 打開音訊流
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,  # 單聲道
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024,
                input_device_index=self.device_info['index'] if self.device_info else None,
                as_loopback=True  # 啟用loopback模式
            )
            
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
                    audio_data = np.frombuffer(data, dtype=np.float32)
                    
                    # 添加到緩衝區
                    self.buffer = np.concatenate([self.buffer, audio_data])
                    
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

