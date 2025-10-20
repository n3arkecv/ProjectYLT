"""
主GUI控制面板
提供應用程式控制介面
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QCheckBox, QComboBox,
    QTextEdit, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QTextCursor
from typing import Optional, List
from utils.logger import logger


class MainWindow(QMainWindow):
    """主GUI視窗"""
    
    # 信號定義
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    opacity_changed = pyqtSignal(float)
    background_changed = pyqtSignal(bool)
    size_changed = pyqtSignal(str)
    device_changed = pyqtSignal(int)
    
    def __init__(self):
        """初始化主視窗"""
        super().__init__()
        
        self.is_running = False
        
        # 初始化UI
        self._init_ui()
        
        # 連接日誌
        from utils.logger import logger as app_logger
        app_logger.add_gui_callback(self._on_log_message)
        
        logger.info("主GUI視窗已創建")
    
    def _init_ui(self) -> None:
        """初始化UI組件"""
        self.setWindowTitle("ProjectYLT - YouTube直播翻譯")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主佈局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 標題
        title_label = QLabel("YouTube直播即時翻譯")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Overlay設置區
        overlay_group = self._create_overlay_settings()
        main_layout.addWidget(overlay_group)
        
        # 音訊設置區
        audio_group = self._create_audio_settings()
        main_layout.addWidget(audio_group)
        
        # 控制按鈕區
        control_layout = self._create_control_buttons()
        main_layout.addLayout(control_layout)
        
        # 日誌區
        log_group = self._create_log_area()
        main_layout.addWidget(log_group)
        
        central_widget.setLayout(main_layout)
        
        # 設置樣式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QGroupBox {
                color: #ffffff;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                background: #555555;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 3px;
            }
        """)
    
    def _create_overlay_settings(self) -> QGroupBox:
        """創建Overlay設置區"""
        group = QGroupBox("Overlay設置")
        layout = QVBoxLayout()
        
        # 透明度設置
        opacity_layout = QHBoxLayout()
        opacity_label = QLabel("透明度:")
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(90)
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        self.opacity_value_label = QLabel("90%")
        self.opacity_value_label.setMinimumWidth(40)
        
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        
        opacity_layout.addWidget(opacity_label)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_value_label)
        
        # 文字背景開關
        self.background_checkbox = QCheckBox("顯示文字背景")
        self.background_checkbox.setChecked(True)
        self.background_checkbox.stateChanged.connect(self._on_background_changed)
        
        # Overlay大小
        size_layout = QHBoxLayout()
        size_label = QLabel("Overlay大小:")
        self.size_combo = QComboBox()
        self.size_combo.addItems(["小", "中", "大"])
        self.size_combo.setCurrentText("中")
        self.size_combo.currentTextChanged.connect(self._on_size_changed)
        
        size_layout.addWidget(size_label)
        size_layout.addWidget(self.size_combo)
        size_layout.addStretch()
        
        layout.addLayout(opacity_layout)
        layout.addWidget(self.background_checkbox)
        layout.addLayout(size_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_audio_settings(self) -> QGroupBox:
        """創建音訊設置區"""
        group = QGroupBox("音訊設置")
        layout = QHBoxLayout()
        
        device_label = QLabel("音訊設備:")
        self.device_combo = QComboBox()
        self.device_combo.addItem("預設 (系統音訊)", 0)
        self.device_combo.currentIndexChanged.connect(self._on_device_changed)
        
        self.refresh_button = QPushButton("重新整理")
        self.refresh_button.setMaximumWidth(100)
        self.refresh_button.clicked.connect(self._on_refresh_devices)
        
        layout.addWidget(device_label)
        layout.addWidget(self.device_combo, 1)
        layout.addWidget(self.refresh_button)
        
        group.setLayout(layout)
        return group
    
    def _create_control_buttons(self) -> QHBoxLayout:
        """創建控制按鈕區"""
        layout = QHBoxLayout()
        
        self.start_button = QPushButton("開始")
        self.start_button.setMinimumHeight(50)
        self.start_button.clicked.connect(self._on_start_clicked)
        
        self.stop_button = QPushButton("停止")
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #c4170a;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        
        return layout
    
    def _create_log_area(self) -> QGroupBox:
        """創建日誌區"""
        group = QGroupBox("事件日誌")
        layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        clear_button = QPushButton("清空日誌")
        clear_button.setMaximumWidth(100)
        clear_button.clicked.connect(self._on_clear_log)
        
        layout.addWidget(self.log_text)
        layout.addWidget(clear_button, alignment=Qt.AlignmentFlag.AlignRight)
        
        group.setLayout(layout)
        return group
    
    def _on_opacity_changed(self, value: int) -> None:
        """透明度改變處理"""
        opacity = value / 100.0
        self.opacity_value_label.setText(f"{value}%")
        self.opacity_changed.emit(opacity)
    
    def _on_background_changed(self, state: int) -> None:
        """背景開關改變處理"""
        show = state == Qt.CheckState.Checked.value
        self.background_changed.emit(show)
    
    def _on_size_changed(self, text: str) -> None:
        """大小改變處理"""
        size_map = {"小": "small", "中": "medium", "大": "large"}
        size = size_map.get(text, "medium")
        self.size_changed.emit(size)
    
    def _on_device_changed(self, index: int) -> None:
        """設備改變處理"""
        device_index = self.device_combo.itemData(index)
        if device_index is not None:
            self.device_changed.emit(device_index)
    
    def _on_refresh_devices(self) -> None:
        """重新整理設備列表"""
        logger.info("重新整理音訊設備列表...")
        # 這個方法會在主程式中被連接到實際的刷新邏輯
    
    def _on_start_clicked(self) -> None:
        """開始按鈕點擊"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.is_running = True
        self.start_requested.emit()
        logger.info("用戶點擊開始按鈕")
    
    def _on_stop_clicked(self) -> None:
        """停止按鈕點擊"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.is_running = False
        self.stop_requested.emit()
        logger.info("用戶點擊停止按鈕")
    
    def _on_clear_log(self) -> None:
        """清空日誌"""
        self.log_text.clear()
    
    def _on_log_message(self, level: str, message: str) -> None:
        """處理日誌消息"""
        # 根據日誌級別設置顏色
        color_map = {
            "DEBUG": "#888888",
            "INFO": "#ffffff",
            "WARNING": "#FFA500",
            "ERROR": "#FF0000",
            "CRITICAL": "#FF00FF"
        }
        
        color = color_map.get(level, "#ffffff")
        
        # 格式化消息
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        html_message = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span>'
        
        # 添加到日誌文本框
        self.log_text.append(html_message)
        
        # 自動滾動到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def update_device_list(self, devices: List[dict]) -> None:
        """
        更新音訊設備列表
        
        Args:
            devices: 設備信息列表
        """
        current_index = self.device_combo.currentIndex()
        current_device = self.device_combo.itemData(current_index) if current_index >= 0 else 0
        
        self.device_combo.clear()
        self.device_combo.addItem("預設 (系統音訊)", 0)
        
        for device in devices:
            device_name = f"{device['name']} ({device['channels']}ch)"
            self.device_combo.addItem(device_name, device['index'])
        
        # 嘗試恢復之前選擇的設備
        for i in range(self.device_combo.count()):
            if self.device_combo.itemData(i) == current_device:
                self.device_combo.setCurrentIndex(i)
                break
    
    def set_status(self, status: str) -> None:
        """
        設置狀態顯示
        
        Args:
            status: 狀態文本
        """
        self.statusBar().showMessage(status)
    
    def closeEvent(self, event) -> None:
        """關閉事件"""
        if self.is_running:
            logger.warning("應用程式運行中，正在停止...")
            self.stop_requested.emit()
        
        logger.info("主GUI視窗已關閉")
        event.accept()

