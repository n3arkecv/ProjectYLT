"""
ProjectYLT - YouTube直播即時翻譯
主入口文件
"""

import sys
from pathlib import Path

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from modules.gui_window import MainWindow
from modules.overlay_window import OverlayWindow, OverlayController
from modules.pipeline import PipelineBuilder, TranslationPipeline
from modules.system_check import SystemCheck, create_check_dialog
from utils.config import config
from utils.logger import logger


class ModelLoadThread(QThread):
    """模型載入線程"""
    
    finished = pyqtSignal(bool)
    progress = pyqtSignal(str)
    
    def __init__(self, pipeline: TranslationPipeline):
        super().__init__()
        self.pipeline = pipeline
    
    def run(self):
        """執行載入"""
        try:
            # 載入模型
            self.progress.emit("正在載入STT模型...")
            if not self.pipeline.stt_processor.stt.load_model():
                self.finished.emit(False)
                return
            
            self.progress.emit("正在載入LLM模型...")
            if not self.pipeline.llm_processor.llm.load_model():
                self.finished.emit(False)
                return
            
            # 預熱模型
            self.progress.emit("正在預熱STT模型...")
            self.pipeline.stt_processor.stt.warm_up()
            
            self.progress.emit("正在預熱LLM模型...")
            self.pipeline.llm_processor.llm.warm_up()
            
            self.progress.emit("模型載入完成")
            self.finished.emit(True)
            
        except Exception as e:
            logger.error(f"載入模型時發生錯誤: {e}")
            self.finished.emit(False)


class Application:
    """主應用程式"""
    
    def __init__(self):
        """初始化應用程式"""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("ProjectYLT")
        
        # 組件
        self.main_window: MainWindow = None
        self.overlay_window: OverlayWindow = None
        self.overlay_controller: OverlayController = None
        self.pipeline: TranslationPipeline = None
        
        # 模型載入線程
        self.model_load_thread: ModelLoadThread = None
        
        # 狀態
        self.models_loaded = False
        
        logger.info("=" * 60)
        logger.info("ProjectYLT - YouTube直播即時翻譯")
        logger.info("=" * 60)
    
    def initialize(self) -> bool:
        """
        初始化應用程式
        
        Returns:
            是否初始化成功
        """
        try:
            # 1. 創建GUI視窗
            logger.info("正在創建GUI視窗...")
            self.main_window = MainWindow()
            self.main_window.show()
            
            # 2. 創建Overlay視窗
            logger.info("正在創建Overlay視窗...")
            self.overlay_window = OverlayWindow()
            self.overlay_controller = OverlayController(self.overlay_window)
            
            # 從配置恢復Overlay位置和設置
            self.overlay_window.set_position(
                config.get("overlay.position_x", 100),
                config.get("overlay.position_y", 100)
            )
            self.overlay_window.set_opacity(config.get("overlay.opacity", 0.9))
            self.overlay_window.set_background(config.get("overlay.show_background", True))
            self.overlay_window.apply_size(config.get("overlay.size", "medium"))
            self.overlay_window.show()
            
            # 3. 連接GUI信號
            self._connect_signals()
            
            # 強制處理事件，確保視窗已顯示
            self.app.processEvents()
            
            # 4. 執行系統檢查
            if not config.get("system_check.skip_check", False):
                logger.info("正在執行系統檢查...")
                checker = SystemCheck()
                passed, results = checker.check_all()
                
                # 顯示檢查結果
                dialog = create_check_dialog(self.main_window, results, passed)
                dialog.exec()
                
                if not passed:
                    logger.warning("系統檢查未通過，但將繼續啟動")
            
            # 5. 構建翻譯管道
            logger.info("正在構建翻譯管道...")
            self.pipeline = PipelineBuilder.build_from_config(config)
            
            if not self.pipeline:
                QMessageBox.critical(
                    self.main_window,
                    "錯誤",
                    "無法構建翻譯管道"
                )
                return False
            
            # 6. 設置管道回調
            self.pipeline.set_callbacks(
                on_partial=self._on_partial_text,
                on_translation=self._on_translation
            )
            
            # 7. 載入音訊設備列表
            self._refresh_audio_devices()
            
            # 8. 在背景載入模型
            logger.info("正在背景載入模型...")
            self.main_window.set_status("正在載入模型...")
            
            self.model_load_thread = ModelLoadThread(self.pipeline)
            self.model_load_thread.finished.connect(self._on_models_loaded)
            self.model_load_thread.progress.connect(self._on_load_progress)
            self.model_load_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"初始化應用程式時發生錯誤: {e}")
            QMessageBox.critical(
                None,
                "初始化錯誤",
                f"無法初始化應用程式:\n{e}"
            )
            return False
    
    def _connect_signals(self) -> None:
        """連接GUI信號"""
        # 控制信號
        self.main_window.start_requested.connect(self._on_start)
        self.main_window.stop_requested.connect(self._on_stop)
        
        # Overlay設置信號
        self.main_window.opacity_changed.connect(self.overlay_window.set_opacity)
        self.main_window.background_changed.connect(self.overlay_window.set_background)
        self.main_window.size_changed.connect(self.overlay_window.apply_size)
        
        logger.debug("GUI信號已連接")
    
    def _refresh_audio_devices(self) -> None:
        """刷新音訊設備列表"""
        try:
            devices = self.pipeline.audio_capture.list_devices()
            self.main_window.update_device_list(devices)
            logger.info(f"已載入 {len(devices)} 個音訊設備")
        except Exception as e:
            logger.error(f"刷新音訊設備時發生錯誤: {e}")
    
    def _on_load_progress(self, message: str) -> None:
        """模型載入進度"""
        self.main_window.set_status(message)
        logger.info(message)
    
    def _on_models_loaded(self, success: bool) -> None:
        """模型載入完成"""
        if success:
            self.models_loaded = True
            self.main_window.set_status("就緒 - 可以開始翻譯")
            logger.info("應用程式已就緒")
        else:
            self.main_window.set_status("模型載入失敗")
            QMessageBox.critical(
                self.main_window,
                "錯誤",
                "模型載入失敗，請檢查模型文件是否存在"
            )
    
    def _on_start(self) -> None:
        """開始翻譯"""
        if not self.models_loaded:
            QMessageBox.warning(
                self.main_window,
                "警告",
                "模型尚未載入完成"
            )
            return
        
        try:
            # 獲取選擇的音訊設備
            device_index = config.get("audio.device_index", 0)
            
            # 啟動管道
            if self.pipeline.start(device_index):
                self.main_window.set_status("運行中...")
                self.overlay_controller.clear()
                logger.info("翻譯管道已啟動")
            else:
                QMessageBox.critical(
                    self.main_window,
                    "錯誤",
                    "無法啟動翻譯管道"
                )
                # 重置按鈕狀態
                self.main_window.start_button.setEnabled(True)
                self.main_window.stop_button.setEnabled(False)
                
        except Exception as e:
            logger.error(f"啟動翻譯時發生錯誤: {e}")
            QMessageBox.critical(
                self.main_window,
                "錯誤",
                f"啟動失敗:\n{e}"
            )
    
    def _on_stop(self) -> None:
        """停止翻譯"""
        try:
            self.pipeline.stop()
            self.main_window.set_status("已停止")
            logger.info("翻譯管道已停止")
        except Exception as e:
            logger.error(f"停止翻譯時發生錯誤: {e}")
    
    def _on_partial_text(self, text: str) -> None:
        """處理部分文本（逐字）"""
        self.overlay_controller.on_partial_text(text)
    
    def _on_translation(self, original: str, translation: str, context: str) -> None:
        """處理翻譯結果"""
        self.overlay_controller.on_translation(original, translation, context)
    
    def run(self) -> int:
        """
        運行應用程式
        
        Returns:
            退出代碼
        """
        try:
            return self.app.exec()
        except Exception as e:
            logger.error(f"應用程式運行時發生錯誤: {e}")
            return 1
        finally:
            self._cleanup()
    
    def _cleanup(self) -> None:
        """清理資源"""
        try:
            logger.info("正在清理資源...")
            
            # 停止管道
            if self.pipeline:
                self.pipeline.stop()
            
            # 保存配置
            if self.overlay_window:
                x, y = self.overlay_window.get_position()
                config.set("overlay.position_x", x)
                config.set("overlay.position_y", y)
            
            config.save_config()
            
            logger.info("資源清理完成")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"清理資源時發生錯誤: {e}")


def main():
    """主函數"""
    try:
        app = Application()
        
        if not app.initialize():
            return 1
        
        return app.run()
        
    except Exception as e:
        print(f"致命錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

