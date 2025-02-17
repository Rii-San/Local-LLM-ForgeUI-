import os
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QScrollArea, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSizePolicy, QGraphicsBlurEffect
)
from PySide6.QtGui import QIcon, QPixmap, QMovie
from PySide6.QtCore import Qt, QTimer, QSize, QPropertyAnimation
from ui_functions import Backend, LLMListener, ImageListener, LoadingListener, HOST, USER_PORT, LLM_PORT, IMAGE_PORT, LOADING_PORT
from chat_message import ChatMessage

# Animation duration constant (in ms)
fade = 250

class LoadingIndicator(QWidget):
    """A widget showing an animated GIF loading indicator."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self.movie = QMovie("assets/loading.gif")
        self.movie.setScaledSize(QSize(100, 100))
        self.label = QLabel(self)
        self.label.setMovie(self.movie)
        self.label.setAlignment(Qt.AlignCenter)
        self.movie.start()

    def showEvent(self, event):
        self.movie.start()
        super().showEvent(event)

    def hideEvent(self, event):
        self.movie.stop()
        super().hideEvent(event)


class ChatUI(QMainWindow):
    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.setWindowTitle("The Artist")
        self.setGeometry(100, 100, 850, 600)
        self.setWindowIcon(QIcon("assets/icon_png.png"))
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self._build_ui()
        self._setup_listeners()
        self._setup_effects()

    def _build_ui(self):
        # Main layout and central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # Image display widget (left)
        self.image_label = QLabel()
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.image_label, stretch=4)

        # Chat area (right)
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.main_layout.addWidget(self.chat_widget, stretch=3)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background-color: #2d2d2d; border: none; border-radius: 8px;")
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.chat_area = QWidget()
        self.chat_area_layout = QVBoxLayout(self.chat_area)
        self.chat_area_layout.setAlignment(Qt.AlignTop)
        self.chat_area_layout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)
        self.chat_scroll.setWidget(self.chat_area)
        self.chat_layout.addWidget(self.chat_scroll)

        # Input area
        self.input_layout = QHBoxLayout()
        self.user_input = QLineEdit()
        self.user_input.setStyleSheet("""
            QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }
        """)
        send_icon = QPixmap("assets/send_btn_sym.png").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.send_btn = QPushButton()
        self.send_btn.setIcon(QIcon(send_icon))
        self.send_btn.setIconSize(send_icon.size())
        self.send_btn.setText("")
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.input_layout.addWidget(self.user_input)
        self.input_layout.addWidget(self.send_btn)
        self.chat_layout.addLayout(self.input_layout)

        # Connect signals
        self.send_btn.clicked.connect(self.send_message)
        self.user_input.returnPressed.connect(self.send_message)

    def _setup_listeners(self):
        self.llm_thread = LLMListener()
        self.llm_thread.received_data.connect(self.start_typing_animation)
        self.llm_thread.start()

        self.image_thread = ImageListener()
        self.image_thread.received_image.connect(self.display_image)
        self.image_thread.start()

        self.loading_thread = LoadingListener()
        self.loading_thread.loading_status.connect(self.handle_loading_status)
        self.loading_thread.start()

    def _setup_effects(self):
        # Blur effect applied to the image label
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(0)
        self.image_label.setGraphicsEffect(self.blur_effect)
        self.blur_animation = QPropertyAnimation(self.blur_effect, b"blurRadius")
        self.blur_animation.setDuration(fade)
        self.blur_animation.setStartValue(0)
        self.blur_animation.setEndValue(15)
        self.blur_animation.setTargetObject(self.blur_effect)

        # Loading indicator on top (remains unblurred)
        self.loading_indicator = LoadingIndicator(self)
        self.loading_indicator.hide()

    def handle_loading_status(self, status):
        if status == "loading_start":
            self.blur_animation.setDirection(QPropertyAnimation.Forward)
            self.blur_animation.start()
            self.show_loading_indicator()
        elif status == "loading_end":
            self.blur_animation.setDirection(QPropertyAnimation.Backward)
            self.blur_animation.start()
            self.hide_loading_indicator()

    def show_loading_indicator(self):
        """Show the loading indicator and ensure it remains centered on the image."""
        self.update_loading_indicator_position()  # Ensure correct position before showing
        self.loading_indicator.show()

    def update_loading_indicator_position(self):
        """Keep the loading indicator centered on the image."""
        if self.image_label and self.loading_indicator:
            x = self.image_label.x() + (self.image_label.width() - self.loading_indicator.width()) // 2
            y = self.image_label.y() + (self.image_label.height() - self.loading_indicator.height()) // 2
            self.loading_indicator.move(x, y)

    def hide_loading_indicator(self):
        self.loading_indicator.hide()

    def send_message(self):
        text = self.user_input.text().strip()
        if not text:
            return
        self.display_message(text, 'user')
        self.user_input.clear()
        error = self.backend.send_message(text)
        if error:
            self.display_message(error, 'error')

    def start_typing_animation(self, text):
        self.typing_text = text
        self.typing_index = 0
        self.typing_message = ChatMessage("", "assistant")
        self.chat_area_layout.addWidget(self.typing_message)
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.typing_animation)
        self.typing_timer.start(20)

    def typing_animation(self):
        if self.typing_index < len(self.typing_text):
            partial = self.typing_text[:self.typing_index + 1]
            self.typing_message.message_label.setText(partial)
            self.typing_message.adjust_bubble_width()
            self.typing_index += 1
            QTimer.singleShot(1, self.scroll_to_bottom)
        else:
            self.typing_timer.stop()

    def display_message(self, text, sender):
        message = ChatMessage(text, sender)
        self.chat_area_layout.addWidget(message)
        QTimer.singleShot(10, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
        self.chat_scroll.ensureWidgetVisible(self.chat_area_layout.itemAt(self.chat_area_layout.count() - 1).widget())

    def resizeEvent(self, event):
        """Ensure the loading indicator remains centered when resizing the window."""
        super().resizeEvent(event)
        self.update_loading_indicator_position()
        self.update_image_size()

    def display_image(self, image_path):
        if not os.path.exists(image_path):
            self.display_message(f"Error: Image not found ({image_path})", 'error')
            return
        self.original_pixmap = QPixmap(image_path)
        self.update_image_size()

    def update_image_size(self):
        if hasattr(self, "original_pixmap") and not self.original_pixmap.isNull():
            scaled = self.original_pixmap.scaled(
                self.image_label.width(), self.image_label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icon.png"))
    backend = Backend(HOST, USER_PORT, LLM_PORT, IMAGE_PORT, LOADING_PORT)
    window = ChatUI(backend)
    window.show()
    sys.exit(app.exec())
