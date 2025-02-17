from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QSizePolicy
from PySide6.QtCore import Qt

# Constants 
min_width = 50
max_width = 300

class ChatMessage(QWidget):
    def __init__(self, text, sender):
        super().__init__()
        self.sender = sender
        self.setup_ui(text)

    def adjust_bubble_width(self):
        text_width = self.message_label.sizeHint().width() + 20  # Calculate width
        bubble_width = max(min_width, min(text_width, max_width))  # Ensure within limits

        self.message_label.setFixedWidth(bubble_width)
        self.bubble.setFixedWidth(bubble_width + 20)  # Extra padding
        self.adjustSize()  # Ensure resizing


    def setup_ui(self, text):
        # Main layout
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 2)  # Reduce outer margins
        self.layout.setSpacing(3)  # Reduce space between messages

        # Message bubble
        self.bubble = QFrame()
        self.bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {"#4CAF50" if self.sender == 'user' else "#3d3d3d"};
                color: {"#000" if self.sender == 'user' else "#fff"};
                border-radius: 10px;
            }}
            QFrame:hover {{
                background-color: {"#45a049" if self.sender == 'user' else "#444"};
            }}
        """)

        # Message text
        self.message_label = QLabel(text)
        self.message_label.setWordWrap(True)  # Enable word wrapping
        self.message_label.setStyleSheet("font: 11pt 'Segoe UI'; padding: 5px;")  # Reduce padding inside text
        self.message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # Allow text selection
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Center vertically, left align

        # Dynamic width adjustment
        text_width = self.message_label.sizeHint().width() + 10  # Reduce extra padding
        bubble_width = max(min_width, min(text_width, max_width))  # Ensure within limits

        # Apply dynamic width
        self.message_label.setFixedWidth(bubble_width)
        self.bubble.setFixedWidth(bubble_width + 15)  # Slightly less extra padding

        # Bubble layout
        bubble_layout = QVBoxLayout(self.bubble)
        bubble_layout.setContentsMargins(8, 5, 8, 5)  # Reduce padding inside bubble
        bubble_layout.addWidget(self.message_label)

        # Ensure proper resizing
        self.bubble.setMinimumHeight(self.message_label.sizeHint().height() + 5)
        self.adjustSize()

        # Align messages correctly
        if self.sender == 'user':
            self.layout.addStretch()
            self.layout.addWidget(self.bubble)
        else:
            self.layout.addWidget(self.bubble)
            self.layout.addStretch()

        self.setLayout(self.layout)