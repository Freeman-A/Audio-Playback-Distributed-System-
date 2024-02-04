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
            load_balancer_client = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            load_balancer_client.settimeout(1)  # Add a timeout of 5 seconds
            load_balancer_client.connect(("172.27.192.1", 50000))
            print("Connected to load balancer")

            # Send node details to load balancer
            node_details = {
                "node_name": self.node_name,
                "node_IP":  self.node_ip,
                "node_port": self.node_port,
                "node_type": "AuthNode"
            }
            load_balancer_client.sendall(str(node_details).encode())
            load_balancer_client.close()  # Close the connection after sending details
        except:
            print("Error connecting to load balancer")

        print("Node details sent to load balancer")

    def run(self):
        server_thread = threading.Thread(target=self.start_auth_node)
        server_thread.start()

        time.sleep(1)  # Wait for server to start

        self.connect_to_load_balancer()


if __name__ == "__main__":
    auth_node = AuthNode()
    auth_node.run()
