import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QFrame, QPushButton, QGraphicsDropShadowEffect)
from PyQt5.QtCore import (Qt, QPropertyAnimation, QTimer, QEasingCurve, 
                          pyqtProperty, QParallelAnimationGroup)
from PyQt5.QtGui import QPainter, QColor, QFont

class ToastOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(12)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.setLayout(self.layout)

        self.setGeometry(parent.rect())

    def add_toast(self, message: str, duration: int = 3000, toast_type: str = "info"):
        toast = Toast(message, duration, toast_type, self)
        self.layout.addWidget(toast)
        toast.show()

    def resizeEvent(self, event):
        self.setGeometry(self.parent().rect())
        super().resizeEvent(event)

class Toast(QFrame):
    def __init__(self, message, duration, toast_type, parent):
        super().__init__(parent)
        
        self._opacity = 0.0
        self._scale = 0.8
        self.toast_type = toast_type
        
        self.setFixedSize(320, 80)
        self.setup_styling()
        self.setup_shadow()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        
        self.label = QLabel(message, self)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        font = QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        font.setWeight(QFont.Medium)
        self.label.setFont(font)
        
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        self.setup_animations()
        
        self.is_fading_out = False
        
        if duration > 0:
            QTimer.singleShot(duration, self.fade_out)
            
        self.fade_in()

    def setup_styling(self):
        colors = {
            "info": {"bg": "rgba(59, 130, 246, 0.95)", "border": "#3B82F6"},
            "success": {"bg": "rgba(34, 197, 94, 0.95)", "border": "#22C55E"},
            "warning": {"bg": "rgba(245, 158, 11, 0.95)", "border": "#F59E0B"},
            "error": {"bg": "rgba(239, 68, 68, 0.95)", "border": "#EF4444"}
        }
        
        color_scheme = colors.get(self.toast_type, colors["info"])
        
        self.setStyleSheet(f"""
            QFrame {{
                background: {color_scheme["bg"]};
                color: white;
                border: 2px solid {color_scheme["border"]};
                border-radius: 12px;
            }}
            QLabel {{
                color: white;
                background: transparent;
                border: none;
            }}
        """)

    def setup_shadow(self):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)

    def setup_animations(self):
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        self.opacity_animation.setDuration(400)
        self.opacity_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(400)
        self.scale_animation.setEasingCurve(QEasingCurve.OutBack)
        
        self.fade_in_group = QParallelAnimationGroup()
        self.fade_in_group.addAnimation(self.opacity_animation)
        self.fade_in_group.addAnimation(self.scale_animation)
        
        self.fade_out_animation = QPropertyAnimation(self, b"opacity")
        self.fade_out_animation.setDuration(250)
        self.fade_out_animation.setEasingCurve(QEasingCurve.InCubic)
        self.fade_out_animation.finished.connect(self._on_animation_finish)

    def setOpacity(self, opacity):
        self._opacity = opacity
        self.update()

    def getOpacity(self):
        return self._opacity

    def setScale(self, scale):
        self._scale = scale
        self.update()

    def getScale(self):
        return self._scale

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Apply scaling transform
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.width() / 2, -self.height() / 2)
        
        super().paintEvent(event)

    def fade_in(self):
        self.fade_in_group.stop()
        
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        
        self.scale_animation.setStartValue(0.8)
        self.scale_animation.setEndValue(1.0)
        
        self.fade_in_group.start()

    def fade_out(self):
        if self.is_fading_out:
            return
        self.is_fading_out = True
        
        self.fade_out_animation.stop()
        self.fade_out_animation.setStartValue(self._opacity)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.start()

    def _on_animation_finish(self):
        if self.is_fading_out:
            self.deleteLater()

    def mousePressEvent(self, event):
        if not self.is_fading_out:
            self.fade_out()
        
    def enterEvent(self, event):
        if hasattr(self, 'dismiss_timer'):
            self.dismiss_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if hasattr(self, 'dismiss_timer') and not self.is_fading_out:
            self.dismiss_timer.start()
        super().leaveEvent(event)
        
    opacity = pyqtProperty(float, getOpacity, setOpacity)
    scale = pyqtProperty(float, getScale, setScale)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QWidget()
    window.resize(600, 500)
    window.setWindowTitle("Enhanced Toast Notifications")
    window.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #667eea, stop:1 #764ba2);
        }
        QPushButton {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            padding: 12px;
            font-size: 14px;
            font-weight: bold;
            min-height: 20px;
        }
        QPushButton:hover {
            background: rgba(255, 255, 255, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.5);
        }
        QPushButton:pressed {
            background: rgba(255, 255, 255, 0.1);
        }
    """)
    
    main_layout = QVBoxLayout(window)
    main_layout.setAlignment(Qt.AlignCenter)
    main_layout.setSpacing(20)

    toast_overlay = ToastOverlay(window)

    buttons_data = [
        ("Show Info Toast", "info", "Here's some helpful information!"),
        ("Show Success Toast", "success", "Operation completed successfully!"),
        ("Show Warning Toast", "warning", "Please check your input carefully."),
        ("Show Error Toast", "error", "Something went wrong. Please try again."),
    ]

    for text, toast_type, message in buttons_data:
        button = QPushButton(text, window)
        button.setFixedSize(250, 50)
        button.clicked.connect(lambda checked, t=toast_type, m=message: 
                             toast_overlay.add_toast(m, 4000, t))
        main_layout.addWidget(button)
    
    multi_button = QPushButton("Show Multiple Toasts", window)
    multi_button.setFixedSize(250, 50)
    
    def show_multiple():
        messages = [
            ("Welcome to the app!", "info"),
            ("File saved successfully", "success"),
            ("Low disk space warning", "warning"),
        ]
        for i, (msg, t_type) in enumerate(messages):
            QTimer.singleShot(i * 500, lambda m=msg, tt=t_type: 
                            toast_overlay.add_toast(m, 5000, tt))
            
    multi_button.clicked.connect(show_multiple)
    main_layout.addWidget(multi_button)

    window.show()
    sys.exit(app.exec_())