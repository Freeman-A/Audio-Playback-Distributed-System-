
import socket
import threading


class ServerNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.lock = threading.Lock()

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(self.host, self.port)
        server_socket.listen(5)

        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_socket, client_address))
            client_thread.start()
