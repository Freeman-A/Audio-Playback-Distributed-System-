import socket
import random
import threading
import time


class AuthNode():
    def __init__(self):
        self.node_name = f"AN{random.randint(0, 10)}"
        self.node_ip = None
        self.node_port = None
        self.server_socket = None

    def bind_server_socket(self, host):
        for port in range(50000, 50011):
            try:
                self.server_socket.bind((host, port))
                print(f"Socket bound to {host}:{port}")
                return port
            except:
                print(f"Socket bind failed on {host}:{port}")

    def start_auth_node(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.node_ip = socket.gethostbyname(socket.gethostname())
        try:
            self.node_port = self.bind_server_socket(self.node_ip)
        except:
            print(f"Unable to bind to any port in range 50000, 50010")
            return False

        self.server_socket.listen(5)
        print(f"Server started on port {self.node_port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Received connection from {client_address}")
            # Handle client connection here

    def connect_to_load_balancer(self):
        try:
            self.listen(5)
            while True:
                conn, addr = self.accept()
                threading.Thread(target=self.handle_client,
                                 args=(conn, addr)).start()

        except Exception as e:
            print(f"Error in listening for clients: {str(e)}")

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(1024).decode("utf-8")

            if data:
                purpose, username, password = data.split(":")
                match purpose:
                    case "login":
                        print(f"Received login request from {username}")
                    case "register":
                        print(f"Received registration request")

            print(f"Received data from {addr}: {data}")

            # Authenticate the client
            self.authenticate_client(conn, addr, data)

        except Exception as e:
            print(f"Error in handling client: {str(e)}")


if __name__ == "__main__":
    auth_node = AuthNode()
    auth_node.run()
