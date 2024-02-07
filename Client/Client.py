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

    def connect_to_load_balancer(self):
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(("172.24.112.1", 50000))
        except Exception as e:
            print(f"Error connecting to load balancer: {e}")
            return

    def send_error_message_to_load_balancer(self, error_message):
        """
        Sends an error message to the load balancer.
        """
        try:
            self.connect_to_load_balancer()
            self.client_socket.sendall(error_message.encode("utf-8"))
        except Exception as e:
            print(f"Error sending error message to load balancer: {e}")

    def get_auth_node_details(self):
        """
        Connects to the load balancer and sends node details to request authentication node information.
        Returns the authentication node information received from the load balancer.
        """
        try:
            self.connect_to_load_balancer()
            # Send node details to load balancer
            client_details = {
                "node_type": "Client",
                "purpose": "REQUEST_AUTH_NODE"
            }

            json_data = json.dumps(client_details)
            self.client_socket.sendall(json_data).encode("utf-8")

            auth_node_info = self.client_socket.recv(1024).decode("utf-8")
            auth_node_info = json.loads(auth_node_info)

            if auth_node_info != "NO_AUTH_NODES":
                return auth_node_info

        except Exception:
            print(f"Error getting authentication node details from load balancer.")

            message = {
                "node_type": "Client",
                "purpose": "AUTHENTICATION_NODE_ERROR"
            }

            message = json.dumps(message)
            self.send_error_message_to_load_balancer(message)

            try:
                response = self.recieve_response()
                self.client_socket.settimeout(5)

                if response:
                    return response
            except TimeoutError:
                print("Error: Connection to the server timed out.")
            except Exception:
                print("Error: Connection to the server was forcibly closed.")

    def get_credentials(self):
        print("Enter your credentials")

        while True:
            purpose = input("Login or Register: ").lower()

            if purpose in ["login", "register"]:
                credentials = self.get_credentials(purpose)

                username = input("Username: ")
                password = input("Password: ")
                credentials = {
                    "username": username,
                    "password": password,
                    "purpose": purpose
                }

                credentials = json.dumps(credentials)

                return credentials
            else:
                print("Invalid input. Please enter either 'login' or 'register'.")
                continue

    def send_credentials(self, credentials):
        """
        Sends the credentials to the authentication node.
        """
        try:
            self.client_socket.sendall(credentials.encode("utf-8"))
        except ConnectionResetError:
            print("Error: Connection to the server was forcibly closed.")
            # Handle the error or exit the program gracefully

    def recieve_response(self):
        """
        Receives the response from the authentication node.
        """
        try:
            while True:
                response = self.client_socket.recv(1024).decode("utf-8")
                return response
        except ConnectionResetError:
            print("Error: Connection to the server was forcibly closed.")
        # Handle the error or exit the program gracefully

    def authenticate(self):
        """
        Connects to the authentication node using the authentication node information received from the load balancer.
        """
        try:
            auth_node_info = self.get_auth_node_details()

            print(auth_node_info)

            if not auth_node_info:
                print(
                    "Error: Authentication node information not received from the load balancer. Exiting...")
                return  # Exit the program gracefully

            try:
                self.client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)

                self.client_socket.connect(
                    (auth_node_info[0], auth_node_info[1]))

                credentials = self.get_credentials()

                self.client_socket.sendall(credentials.encode("utf-8"))
                content_node_credentials = self.recieve_response()

                print(content_node_credentials)

            except Exception:
                print("Error: Connection to the authentication node refused.")
                traceback.print_exc()
                return  # Exit the program gracefully

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
