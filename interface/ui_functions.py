import socket
from PySide6.QtCore import QThread, Signal

HOST = 'localhost'
USER_PORT = 5555  # Receive messages from UI
LLM_PORT = 6666   # Send responses from LLM to UI
IMAGE_PORT = 7777 # Send image filenames
LOADING_PORT = 8888  # New port for loading status updates

class LLMListener(QThread):
    received_data = Signal(str)
    def run(self):
        with socket.socket() as s:
            s.bind((HOST, LLM_PORT))
            s.listen()
            while True:
                conn, _ = s.accept()
                data = conn.recv(4096).decode()
                self.received_data.emit(data)  # Emit only the message, not the prefix
                conn.close()

class ImageListener(QThread):
    received_image = Signal(str)

    def run(self):
        with socket.socket() as s:
            s.bind((HOST, IMAGE_PORT))
            s.listen()
            while True:
                conn, _ = s.accept()
                data = conn.recv(4096).decode()
                self.received_image.emit(data)
                conn.close()

class LoadingListener(QThread):
    loading_status = Signal(str)  # Signal to emit loading status ("loading_start" or "loading_end")

    def run(self):
        with socket.socket() as s:
            s.bind((HOST, LOADING_PORT))
            s.listen()
            while True:
                conn, _ = s.accept()
                data = conn.recv(4096).decode()
                self.loading_status.emit(data)
                conn.close()

class Backend:
    def __init__(self, host, user_port, llm_port, image_port, loading_port):
        self.host = host
        self.user_port = user_port
        self.llm_port = llm_port
        self.image_port = image_port
        self.loading_port = loading_port

    def send_message(self, text):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.user_port))
                s.sendall(text.encode('utf-8'))
        except Exception as e:
            return f"Error: {str(e)}"
        return None