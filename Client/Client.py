import socket
import random
import traceback
import time


class Client():
    def __init__(self):
        self.client_name = f"Client{random.random()}"
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_to_loadbalancer(self, load_balancer_ip, client_port):
        self.client_socket.connect((load_balancer_ip, client_port))

    def start(self):
        self.connect_to_loadbalancer("172.27.192.1", 50000)


if __name__ == "__main__":
    client = Client()
    client.start()
