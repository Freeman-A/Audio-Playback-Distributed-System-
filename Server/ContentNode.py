import socket
import threading
import traceback
import pickle

class ContentNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.songs = ["song1"]
        self.clients = []
        self.lock = threading.Lock()

    def start(self):
        content_node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        content_node.bind((self.host, self.port))

        try:
            content_node.connect(("127.0.0.1", 50002))

            data = pickle.dumps(self.songs)
            content_node.send(data)
        except: 
            traceback.print_exc()
    

def main():
    hostname = socket.gethostname()

    content_node = ContentNode(socket.gethostbyname(hostname),50002)
    content_thread = threading.Thread(target=content_node.start())
    content_thread.start()

if __name__ == "__main__":
    main()
