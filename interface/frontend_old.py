import os
import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QScrollArea, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSizePolicy
)
from PySide6.QtGui import QIcon, QPixmap, QMovie
from PySide6.QtCore import Qt, QTimer, QSize, QPropertyAnimation
from ui_functions import Backend, LLMListener, ImageListener, LoadingListener, HOST, USER_PORT, LLM_PORT, IMAGE_PORT, LOADING_PORT
from chat_message import ChatMessage
from PySide6.QtWidgets import QWidget, QGraphicsBlurEffect, QGraphicsOpacityEffect

fade = 250

class BlurOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(30, 30, 30, 150);")  # Semi-transparent dark overlay
        self.setGeometry(0, 0, parent.width(), parent.height())  # Cover full image area
        self.setVisible(False)

        # Apply blur effect only to this overlay (NOT to image_label)
        self.blur_effect = QGraphicsBlurEffect()
        self.setGraphicsEffect(self.blur_effect)  # ✅ Now blur only applies to this overlay

        # Blur Animation
        self.blur_animation = QPropertyAnimation(self.blur_effect, b"blurRadius")
        self.blur_animation.setDuration(fade)
        self.blur_animation.setStartValue(0)
        self.blur_animation.setEndValue(25)
        self.blur_animation.setTargetObject(self.blur_effect)

    def show_blur(self):
        """Show blur effect before loading starts."""
        self.setVisible(True)
        self.blur_animation.setDirection(QPropertyAnimation.Forward)
        self.blur_animation.start()

    def hide_blur(self):
        """Hide blur effect after loading ends."""
        self.blur_animation.setDirection(QPropertyAnimation.Backward)
        self.blur_animation.start()
        self.blur_animation.finished.connect(lambda: self.setVisible(False))  # Hide after animation ends


class LoadingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        self.movie = QMovie("assets/loading.gif")
        self.movie.setScaledSize(QSize(100, 100))  # Scale GIF to fit the widget size
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

        # Main Layout
        self.main_layout = QHBoxLayout()
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setLayout(self.main_layout)

        # Left-side Image Display Widget
        self.image_label = QLabel()
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.image_label, stretch=4)

        # Right-side Chat Widget
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.main_layout.addWidget(self.chat_widget, stretch=3)

        # Chat area (scrollable)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("background-color: #2d2d2d; border: none; border-radius: 8px;")
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide Vertical scrollbar
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Hide horizontal scrollbar

        self.chat_area = QWidget()
        self.chat_area_layout = QVBoxLayout(self.chat_area)
        self.chat_area_layout.setAlignment(Qt.AlignTop)
        self.chat_area_layout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)  # Allow dynamic expansion
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

        # Send Button
        send_icon = QPixmap("assets/send_btn_sym.png")  # Load the image
        scaled_icon = send_icon.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.send_btn = QPushButton()
        self.send_btn.setIcon(QIcon(scaled_icon))  # Set image as button icon
        self.send_btn.setIconSize(scaled_icon.size())
        # Remove button text to keep only the icon
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

        # Connect button
        self.send_btn.clicked.connect(self.send_message)
        self.user_input.returnPressed.connect(self.send_message)

        # Start listeners in QThread
        self.llm_thread = LLMListener()
        self.llm_thread.received_data.connect(self.start_typing_animation)
        self.llm_thread.start()

        self.image_thread = ImageListener()
        self.image_thread.received_image.connect(self.display_image)
        self.image_thread.start()

        # Apply blur effect directly to the image label (so only the image is blurred)
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(0)  # Start with no blur
        self.image_label.setGraphicsEffect(self.blur_effect)  # ✅ Blur applies only to image

        # Blur animation
        self.blur_animation = QPropertyAnimation(self.blur_effect, b"blurRadius")
        self.blur_animation.setDuration(fade)
        self.blur_animation.setStartValue(0)
        self.blur_animation.setEndValue(15)  # Adjust blur intensity
        self.blur_animation.setTargetObject(self.blur_effect)  # ✅ Ensure target is set

        # Loading Indicator (separate from image_label so it's not blurred)
        self.loading_indicator = LoadingIndicator(self)
        self.loading_indicator.hide()

        # Loading Listener
        self.loading_thread = LoadingListener()
        self.loading_thread.loading_status.connect(self.handle_loading_status)
        self.loading_thread.start()

    def handle_loading_status(self, status):
        """Handle loading status updates from the backend."""
        if status == "loading_start":
            # Start blur animation immediately
            self.blur_animation.setDirection(QPropertyAnimation.Forward)
            self.blur_animation.start()

            # Show indicator immediately
            self.show_loading_indicator()

        elif status == "loading_end":
            # Start blur fade-out
            self.blur_animation.setDirection(QPropertyAnimation.Backward)
            self.blur_animation.start()

            # Hide indicator immediately
            self.hide_loading_indicator()


    def show_loading_indicator(self):
        """Show the loading indicator over the image section."""
        self.loading_indicator.move(
            self.image_label.width() // 2 - self.loading_indicator.width() // 2,
            self.image_label.height() // 2 - self.loading_indicator.height() // 2
        )
        self.loading_indicator.show()

    def hide_loading_indicator(self):
        """Hide the loading indicator."""
        self.loading_indicator.hide()

    def send_message(self):
        """Send user input to the backend and show the loading indicator."""
        text = self.user_input.text().strip()
        if not text:
            return

        self.display_message(text, 'user')
        self.user_input.clear()

        error = self.backend.send_message(text)
        if error:
            self.display_message(error, 'error')

    def start_typing_animation(self, text):
        """Start the typing animation for the AI response."""
        self.typing_text = text
        self.typing_index = 0

        # Insert initial empty assistant message
        self.typing_message = ChatMessage("", "assistant")
        self.chat_area_layout.addWidget(self.typing_message)
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.typing_animation)
        self.typing_timer.start(20)  # Adjust the speed of typing animation

    def typing_animation(self):
        """Animate the typing of the AI response."""
        if self.typing_index < len(self.typing_text):
            partial_text = self.typing_text[:self.typing_index + 1]
            self.typing_message.message_label.setText(partial_text)
            self.typing_message.adjust_bubble_width()  # Update width dynamically
            self.typing_index += 1
            # Scroll to bottom while typing
            QTimer.singleShot(1, self.scroll_to_bottom)  # Ensures smooth scrolling
        else:
            self.typing_timer.stop()

    def display_message(self, text, sender):
        """Display a message in the chat area."""
        message_widget = ChatMessage(text, sender)
        self.chat_area_layout.addWidget(message_widget)
        # Use a QTimer to delay the scroll action
        QTimer.singleShot(10, self.scroll_to_bottom)  # Delay of 10ms

    def scroll_to_bottom(self):
        """Scroll the chat area to the bottom."""
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())
        self.chat_scroll.ensureWidgetVisible(self.chat_area_layout.itemAt(self.chat_area_layout.count() - 1).widget())

    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)
        self.update_image_size()

    def display_image(self, image_path):
        """Display the generated image in the image section."""
        if not os.path.exists(image_path):
            self.display_message(f"Error: Image not found ({image_path})", 'error')
            return

        self.original_pixmap = QPixmap(image_path)  # Store original image
        self.update_image_size()  # Scale it properly

    def update_image_size(self):
        """Update the size of the displayed image based on the available space."""
        if hasattr(self, "original_pixmap") and not self.original_pixmap.isNull():
            # Scale the image based on available space
            scaled_pixmap = self.original_pixmap.scaled(
                self.image_label.width(),
                self.image_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("assets/icon.png"))  # Set app icon globally
    backend = Backend(HOST, USER_PORT, LLM_PORT, IMAGE_PORT, LOADING_PORT)
    window = ChatUI(backend)
    window.show()
    sys.exit(app.exec())