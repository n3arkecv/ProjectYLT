#!/usr/bin/env python3
"""
測試音訊捕獲模組
"""

import sys
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.audio_capture import AudioCapture
import pyaudiowpatch as pyaudio

def test_audio():
    """測試音訊捕獲"""
    try:
        # 初始化PyAudio
        audio = pyaudio.PyAudio()
        print("PyAudio初始化成功")

        # 獲取WASAPI信息
        wasapi_info = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
        print(f"找到 {wasapi_info['deviceCount']} 個WASAPI設備")

        # 列出設備
        for i in range(wasapi_info['deviceCount']):
            device_info = audio.get_device_info_by_host_api_device_index(
                wasapi_info['index'], i
            )
            print(f"設備 {i}: {device_info['name']}")
            print(f"  - 輸入通道: {device_info['maxInputChannels']}")
            print(f"  - 輸出通道: {device_info['maxOutputChannels']}")
            print(f"  - 預設樣率: {device_info['defaultSampleRate']}")
            print(f"  - 是否為Loopback: {device_info.get('isLoopbackDevice', False)}")
            print()

        # 測試音訊捕獲器
        capture = AudioCapture()
        devices = capture.list_devices()
        print(f"音訊捕獲器找到 {len(devices)} 個可用的輸入設備:")

        for i, device in enumerate(devices):
            print(f"  {i}: {device['name']} (輸入通道: {device['input_channels']})")

        # 嘗試設置設備並啟動
        if devices:
            print("\n嘗試啟動音訊捕獲...")
            if capture.start(0):  # 使用第一個設備
                print("音訊捕獲啟動成功")

                # 測試獲取音訊數據
                print("測試音訊數據捕獲...")
                chunk = capture.get_audio_chunk(timeout=2.0)
                if chunk is not None:
                    print(f"成功獲取音訊數據，大小: {len(chunk)} 樣本")
                else:
                    print("未獲取到音訊數據（這可能是正常的，如果沒有音訊輸入）")

                capture.stop()
                print("音訊捕獲停止成功")
            else:
                print("音訊捕獲啟動失敗")

        audio.terminate()
        print("測試完成")

    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_audio()
