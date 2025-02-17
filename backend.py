import json
import socket
import threading
from modules import llm  # Import llm module correctly from the same package
from modules.forgeUI import generate_image  # Import function correctly

HOST = 'localhost'
USER_PORT = 5555  # Receive messages from UI
LLM_PORT = 6666   # Send responses from LLM to UI
IMAGE_PORT = 7777 # Send image filenames
LOADING_PORT = 8888  # New port for loading status updates

def send_to_port(data, port):
    """Helper function to send data to a specific port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, port))
        if isinstance(data, str):
            data = data.encode('utf-8')
        s.sendall(data)

def handle_image_generation(prompt):
    """Generate the image and send the filename to the UI."""
    # Check if the prompt is empty
    if not prompt.strip() or len(prompt.strip()) < 4:
        print("The Artist is still uncertain...")
        return ""

    # Notify frontend that image generation has started
    send_to_port("loading_start", LOADING_PORT)

    image_filename = generate_image(prompt) 
    if image_filename:
        send_to_port(image_filename, IMAGE_PORT)

    # Notify frontend that image generation has ended
    send_to_port("loading_end", LOADING_PORT)

def handle_user_input():
    """Listen for user messages and process responses."""
    messages = None
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, USER_PORT))
    server.listen()

    print("Backend running. Waiting for UI input...")

    try:
        while True:
            client, addr = server.accept()
            user_input = client.recv(1024).decode().strip()
            client.close()

            if user_input.lower() == 'quit':
                break

            # Get chat response and prompt from the LLM
            reply, prompt, messages = llm.chat(user_input, messages)

            # Send chat response to the LLM listener port
            send_to_port(reply, LLM_PORT)

            # Start a thread for image generation
            image_thread = threading.Thread(target=handle_image_generation, args=(prompt,))
            image_thread.start()

    finally:
        server.close()

if __name__ == "__main__":
    handle_user_input()