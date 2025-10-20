"""
Overlay浮動字幕視窗
顯示即時轉錄和翻譯結果
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QApplication
)
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette
from typing import Optional
from utils.logger import logger


class OverlayWindow(QWidget):
    """浮動字幕Overlay視窗"""
    
    SIZES = {
        "small": {"原文": 14, "譯文": 14, "上下文": 8, "width": 500, "height": 200},
        "medium": {"原文": 18, "譯文": 18, "上下文": 10, "width": 700, "height": 280},
        "large": {"原文": 22, "譯文": 22, "上下文": 12, "width": 900, "height": 350}
    }
    
    def __init__(self, parent=None):
        """初始化Overlay視窗"""
        super().__init__(parent)
        
        # 視窗屬性
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # 拖曳相關
        self.dragging = False
        self.drag_position = QPoint()
        
        # 設置屬性
        self._opacity = 0.9
        self._show_background = True
        self._size = "medium"
        
        # 初始化UI
        self._init_ui()
        
        # 應用初始設置
        self.apply_size(self._size)
        self.set_opacity(self._opacity)
        
        logger.info("Overlay視窗已創建")
    
    def _init_ui(self) -> None:
        """初始化UI組件"""
        # 主佈局
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 原文標籤
        self.original_label = QLabel("等待語音輸入...")
        self.original_label.setWordWrap(True)
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.original_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: rgba(0, 0, 0, 150);
                padding: 10px;
                border-radius: 5px;
            }
        """)
        
        # 譯文標籤
        self.translation_label = QLabel("翻譯將在此顯示...")
        self.translation_label.setWordWrap(True)
        self.translation_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.translation_label.setStyleSheet("""
            QLabel {
                color: #FFD700;
                background-color: rgba(0, 0, 0, 150);
                padding: 10px;
                border-radius: 5px;
            }
        """)
        
        # 上下文文本框
        self.context_text = QTextEdit()
        self.context_text.setReadOnly(True)
        self.context_text.setPlaceholderText("情境上下文將在此顯示...")
        self.context_text.setStyleSheet("""
            QTextEdit {
                color: #AAAAAA;
                background-color: rgba(0, 0, 0, 100);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                padding: 5px;
            }
        """)
        self.context_text.setMaximumHeight(100)
        
        # 添加到佈局
        layout.addWidget(self.original_label)
        layout.addWidget(self.translation_label)
        layout.addWidget(self.context_text)
        
        # 設置主視窗樣式
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0);
            }
        """)
        
        self.setLayout(layout)
    
    def update_original_text(self, text: str) -> None:
        """
        更新原文（逐字更新）
        
        Args:
            text: 原文文本
        """
        if text:
            current_text = self.original_label.text()
            if current_text == "等待語音輸入...":
                self.original_label.setText(text)
            else:
                self.original_label.setText(current_text + text)
    
    def set_original_text(self, text: str) -> None:
        """
        設置原文（完整替換）
        
        Args:
            text: 原文文本
        """
        self.original_label.setText(text if text else "等待語音輸入...")
    
    def set_translation_text(self, text: str) -> None:
        """
        設置譯文
        
        Args:
            text: 譯文文本
        """
        self.translation_label.setText(text if text else "翻譯將在此顯示...")
    
    def set_context_text(self, text: str) -> None:
        """
        設置上下文
        
        Args:
            text: 上下文文本
        """
        self.context_text.setPlainText(text if text else "")
    
    def clear_all(self) -> None:
        """清空所有顯示"""
        self.original_label.setText("等待語音輸入...")
        self.translation_label.setText("翻譯將在此顯示...")
        self.context_text.clear()
    
    def set_opacity(self, opacity: float) -> None:
        """
        設置透明度
        
        Args:
            opacity: 透明度 (0.0-1.0)
        """
        self._opacity = max(0.0, min(1.0, opacity))
        self.setWindowOpacity(self._opacity)
        logger.debug(f"Overlay透明度: {self._opacity}")
    
    def set_background(self, show: bool) -> None:
        """
        設置是否顯示文字背景
        
        Args:
            show: 是否顯示背景
        """
        self._show_background = show
        
        if show:
            bg_style = "background-color: rgba(0, 0, 0, 150);"
        else:
            bg_style = "background-color: rgba(0, 0, 0, 0);"
        
        self.original_label.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                {bg_style}
                padding: 10px;
                border-radius: 5px;
            }}
        """)
        
        self.translation_label.setStyleSheet(f"""
            QLabel {{
                color: #FFD700;
                {bg_style}
                padding: 10px;
                border-radius: 5px;
            }}
        """)
        
        context_bg = "background-color: rgba(0, 0, 0, 100);" if show else "background-color: rgba(0, 0, 0, 0);"
        self.context_text.setStyleSheet(f"""
            QTextEdit {{
                color: #AAAAAA;
                {context_bg}
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 5px;
                padding: 5px;
            }}
        """)
        
        logger.debug(f"Overlay背景: {'顯示' if show else '隱藏'}")
    
    def apply_size(self, size: str) -> None:
        """
        應用大小設置
        
        Args:
            size: 大小 (small, medium, large)
        """
        if size not in self.SIZES:
            size = "medium"
        
        self._size = size
        size_config = self.SIZES[size]
        
        # 設置字體大小
        original_font = QFont()
        original_font.setPointSize(size_config["原文"])
        original_font.setBold(True)
        self.original_label.setFont(original_font)
        
        translation_font = QFont()
        translation_font.setPointSize(size_config["譯文"])
        translation_font.setBold(True)
        self.translation_label.setFont(translation_font)
        
        context_font = QFont()
        context_font.setPointSize(size_config["上下文"])
        self.context_text.setFont(context_font)
        
        # 設置視窗大小
        self.setFixedSize(size_config["width"], size_config["height"])
        
        logger.debug(f"Overlay大小: {size}")
    
    def mousePressEvent(self, event) -> None:
        """滑鼠按下事件（開始拖曳）"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event) -> None:
        """滑鼠移動事件（拖曳中）"""
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event) -> None:
        """滑鼠釋放事件（結束拖曳）"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()
    
    def get_position(self) -> tuple:
        """獲取當前位置"""
        pos = self.pos()
        return (pos.x(), pos.y())
    
    def set_position(self, x: int, y: int) -> None:
        """設置位置"""
        self.move(x, y)
    
    def closeEvent(self, event) -> None:
        """關閉事件"""
        logger.info("Overlay視窗已關閉")
        event.accept()


class OverlayController:
    """Overlay控制器"""
    
    def __init__(self, overlay: OverlayWindow):
        """
        初始化控制器
        
        Args:
            overlay: Overlay視窗實例
        """
        self.overlay = overlay
        self._partial_text = ""
        
        # 設置定時器用於部分文本顯示
        self.partial_timer = QTimer()
        self.partial_timer.timeout.connect(self._on_partial_timeout)
        self.partial_timeout_ms = 3000  # 3秒後清空部分文本
        
        logger.info("Overlay控制器已創建")
    
    def on_partial_text(self, text: str) -> None:
        """
        處理部分文本（逐字）
        
        Args:
            text: 部分文本
        """
        self._partial_text += text
        self.overlay.set_original_text(self._partial_text)
        
        # 重置定時器
        self.partial_timer.start(self.partial_timeout_ms)
    
    def on_translation(self, original: str, translation: str, context: str) -> None:
        """
        處理翻譯結果
        
        Args:
            original: 原文
            translation: 譯文
            context: 上下文
        """
        # 停止部分文本定時器
        self.partial_timer.stop()
        
        # 更新顯示
        self.overlay.set_original_text(original)
        self.overlay.set_translation_text(translation)
        self.overlay.set_context_text(context)
        
        # 清空部分文本緩存
        self._partial_text = ""
        
        logger.debug(f"Overlay已更新: {original[:20]}... -> {translation[:20]}...")
    
    def _on_partial_timeout(self) -> None:
        """部分文本超時（清空）"""
        self.partial_timer.stop()
        self._partial_text = ""
    
    def clear(self) -> None:
        """清空顯示"""
        self.partial_timer.stop()
        self._partial_text = ""
        self.overlay.clear_all()

