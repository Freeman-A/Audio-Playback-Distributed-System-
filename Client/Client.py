import socket
import random
import threading
import traceback
import time
import json


class Client():
    def __init__(self):
        self.client_name = f"Client{random.random()}"
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_loadbalancer(self, load_balancer_ip, client_port):
        self.client_socket.connect((load_balancer_ip, client_port))

    def request_auth_node(self):
        try:
            self.connect_to_loadbalancer("172.27.192.1", 50000)

            # Send node details to load balancer
            client_details = {
                "node_name": self.client_name,
                "node_type": "Client",
                "purpose": "REQUEST_AUTH_NODE"
            }

            json_data = json.dumps(client_details)

            self.client_socket.sendall(json_data.encode())
            print("Client details sent to load balancer")

            # Receive the address and port of the AuthNode
            auth_node_info = self.client_socket.recv(1024).decode("utf-8")

            try:
                auth_node_info = json.loads(auth_node_info)

                auth_node_ip = auth_node_info.get("address")
                auth_node_port = auth_node_info.get("port")

                # Connect to AuthNode only if it's not already connected
                if not (auth_node_ip == self.client_socket.getpeername()[0] and auth_node_port == self.client_socket.getpeername()[1]):
                    auth_node_socket = socket.socket(
                        socket.AF_INET, socket.SOCK_STREAM)
                    auth_node_socket.connect((auth_node_ip, auth_node_port))
                    print(
                        f"Connected to AuthNode: {auth_node_ip}:{auth_node_port}")

            except Exception as e:
                print(f"Error loading JSON: {e}")
                print(f"Received AuthNode info: {auth_node_info}")

        except Exception as e:
            traceback.print_exc()

    def start(self):
        request_thread = threading.Thread(
            target=self.request_auth_node).start()


if __name__ == "__main__":
    client = Client()
    client.start()
