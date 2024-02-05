import socket
import random
import threading
import traceback
import time
import json


class Client():
    def __init__(self):
        """
        Initializes a Client object.
        """
        self.client_name = f"Client{random.random()}"
        self.client_socket = None

    def get_auth_node_details(self):
        """
        Connects to the load balancer and sends node details to request authentication node information.
        Returns the authentication node information received from the load balancer.
        """
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(("172.27.192.1", 50000))

        # Send node details to load balancer
        client_details = {
            "node_name": self.client_name,
            "node_type": "Client",
            "purpose": "REQUEST_AUTH_NODE"
        }
        json_data = json.dumps(client_details)
        self.client_socket.sendall(json_data.encode())

        auth_node_info = self.client_socket.recv(1024).decode("utf-8")
        auth_node_info = json.loads(auth_node_info)

        self.client_socket.close()

        auth_node_info = ((auth_node_info.get("address"),
                          auth_node_info.get("port")))

        return auth_node_info

    def get_credentials(self, purpose):
        print("Enter your credentials")
        username = input("Username: ")
        password = input("Password: ")
        credentials = {
            "username": username,
            "password": password,
            "purpose": purpose
        }

        credentials = json.dumps(credentials)

        return credentials

    def send_credentials(self, credentials):
        """
        Sends the credentials to the authentication node.
        """
        self.client_socket.sendall(credentials.encode("utf-8"))

    def authenticate(self):
        """
        Connects to the authentication node using the authentication node information received from the load balancer.
        """
        try:
            auth_node_info = self.get_auth_node_details()

            if not auth_node_info:
                print(
                    "Error: Authentication node information not received from the load balancer.")
                return

            try:
                self.client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)

                self.client_socket.connect(
                    (auth_node_info[0], auth_node_info[1]))
            except ConnectionRefusedError:
                print("Error: Connection to the authentication node refused.")
                return

            while True:
                purpose = input("Login or Register: ").lower()

                if purpose in ["login", "register"]:
                    credentials = self.get_credentials(purpose)
                    self.send_credentials(credentials)

                    self.client_socket.settimeout(5)
                    try:
                        response = self.client_socket.recv(
                            1024).decode("utf-8")
                        print(response)

                        # Optionally, you can exit the loop after successful authentication
                        if response.startswith("AUTHORIZED"):
                            break

                    except socket.timeout:
                        print(
                            "Error: Timeout while waiting for authentication response.")
                else:
                    print("Invalid choice. Please enter either 'Login' or 'Register'.")

        except json.JSONDecodeError as json_error:
            print(f"Error decoding JSON: {json_error}")
        except Exception:
            traceback.print_exc()

    def start(self):
        """
        Starts the authentication process in a separate thread.
        """
        threading.Thread(
            target=self.authenticate).start()


if __name__ == "__main__":
    client = Client()
    client.start()
