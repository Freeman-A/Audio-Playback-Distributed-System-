import socket
import threading
import random
import json
import os
import time


class ContentNode:
    def __init__(self):
        self.node_name = f"CN{random.randint(0, 10)}"
        self.node_ip = None
        self.node_port = None
        self.server_socket = None
        self.available_files = self.get_available_files()

    def get_available_files(self):
        # Get the list of available audio files
        # You can implement your own logic here
        # For example, you can read the files from a directory
        # check if directory exists and if the file in the directory is exists
        if not os.path.exists("data/music"):
            os.makedirs("data/music")
        else:
            available_files = os.listdir("data/music")
            return available_files

    def bind_server_socket(self, host):
        port_range = range(50000, 50011)

        for port in port_range:
            try:
                self.server_socket.bind((host, port))
                print(f"Socket bound to {host}:{port}")
                return port
            except Exception:
                print(f"Socket bind failed on {host}:{port}")

        print("Failed to bind to any port in the specified range.")
        return None

    def connect_to_load_balancer(self):
        try:
            load_balancer_client = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            load_balancer_client.settimeout(3)
            load_balancer_client.connect(("172.24.112.1", 50000))
            print("Connected to load balancer")

            # Send node details to load balancer
            node_details = {
                "node_name": self.node_name,
                "node_IP":  self.node_ip,
                "node_port": self.node_port,
                "node_type": "ContentNode"
            }

            json_data = json.dumps(node_details)

            load_balancer_client.sendall(json_data.encode("utf-8"))
            load_balancer_client.close()

            print("Node details sent to load balancer")

        except Exception as e:
            print(f"Error connecting to load balancer: {e}")

    def start_content_node(self):
        try:
            self.server_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.node_ip = socket.gethostbyname(socket.gethostname())

            self.node_port = self.bind_server_socket(self.node_ip)
        except:
            print(f"Unable to host to any port in range 50000, 50010")
            return False

        self.server_socket.listen(5)
        print(f"Server started on port {self.node_port}")

        while True:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"Received connection from {client_address}")

                threading.Thread(target=self.handle_client_request,
                                 args=(client_socket,)).start()
            except Exception as e:
                print(f"Error accepting client connection: {e}")

    def handle_client_request(self, client_socket):
        try:
            print(self.available_files)
            # Handle client requests and send audio files
            pass
        except Exception as e:
            print(f"Error handling client request: {e}")
        finally:
            # Print a message when the thread exits
            print(f"Closing connection with {client_socket.getpeername()}")
            client_socket.close()

    def run(self):
        server_thread = threading.Thread(target=self.start_content_node)
        server_thread.start()

        time.sleep(1)  # Wait for server to start

        self.connect_to_load_balancer()

        server_thread.join()


# Usage
node = ContentNode()
node.run()
