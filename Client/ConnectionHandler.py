import socket
import json


class ConnectionHandler():
    def __init__(self, server_address):
        self.client_socket = None
        self.server_address = server_address

    def connect_to_server(self):
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(self.server_address)
        except Exception as e:
            print(f"Error connecting to server: {e}")

    def send_data(self, data):
        try:
            self.client_socket.sendall(data.encode("utf-8"))
        except ConnectionResetError:
            print("Error: Connection to the server was forcibly closed.")

    def receive_data(self):
        try:
            data = self.client_socket.recv(1024).decode("utf-8")

            json_data = json.loads(data)
            return json_data
        except socket.timeout:
            print("Error: Timeout while waiting for response.")
        except Exception as e:
            print(f"Error receiving data: {e}")

    def close_connection(self):
        try:
            self.client_socket.close()
        except Exception as e:
            print(f"Error closing connection: {e}")
