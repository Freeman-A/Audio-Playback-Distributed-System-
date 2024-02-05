import socket
import random
import threading
import traceback
import time
import os
import json


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
        self.make_user_database()
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
            client_socket, client_address = self.server_socket.accept()
            print(f"Received connection from {client_address}")

            threading.Thread(target=self.handle_client_messages,
                             args=(client_socket,)).start()

    def handle_client_messages(self, client_socket):
        while True:
            try:
                message_str = client_socket.recv(1024).decode("utf-8")
                if message_str:
                    message = json.loads(message_str)

                    purpose = message.get("purpose")

                    username = message.get("username")
                    password = message.get("password")

                    match purpose:
                        case "login":

                            validate_credentials_status = self.validate_credentials(
                                username, password)

                            if validate_credentials_status:
                                client_socket.sendall(
                                    validate_credentials_status.encode("utf-8"))

            except json.JSONDecodeError:
                print("Error decoding JSON. Empty or invalid message received.")
            except:
                print("Error handling client messages", traceback.print_exc())
                break

    def validate_credentials(self, username, password):
        """
        Authenticates the user by checking the username and password against the database.
        """
        print("here")
        file_path = "data/user_data.json"
        if os.path.isfile(file_path):
            print("here2")
            with open(file_path, "r") as file:
                data = json.load(file)

                print("here3")
            if username in data:
                print("here4")
                # If the username exists, check the password
                if data[username]["password"] == password:
                    return "AUTHORIZED"
                else:
                    return "UNAUTHORIZED"
            else:
                return "NOT_FOUND"
        else:
            return "SERVER ERROR"

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

            json_data = json.dumps(node_details)

            load_balancer_client.sendall(json_data.encode("utf-8"))
            load_balancer_client.close()  # Close the connection after sending details
        except:
            print("Error connecting to load balancer")

        print("Node details sent to load balancer")

    def make_user_database(self):
        """
        Creates a user database in the form of a json file.
        If the file already exists, it updates the existing data with the new user data.
        If the file exists but doesn't contain the admin profile, it adds it.
        """
        user_data = [{"username": "admin", "password": "admin"}]
        folder_path = "data"
        file_path = os.path.join(folder_path, "user_data.json")

        try:
            # Check if the folder exists, and create it if not
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            if os.path.exists(file_path):
                # If the file already exists, update existing data
                with open(file_path, "r") as file:
                    data = json.load(file)

                    # Add admin account if not already in the file
                    admin_exists = any(
                        user["username"] == "admin" for user in data)
                    if not admin_exists:
                        data.extend(user_data)

                with open(file_path, "w") as file:
                    json.dump(data, file, indent=4)
            else:
                # If the file doesn't exist, create a new one
                with open(file_path, "w") as file:
                    json.dump(user_data, file, indent=4)
        except Exception as e:
            print(f"Error: {e}")

    def run(self):
        server_thread = threading.Thread(target=self.start_auth_node)
        server_thread.start()

        time.sleep(1)  # Wait for server to start

        self.connect_to_load_balancer()

        server_thread.join()


if __name__ == "__main__":
    auth_node = AuthNode()
    auth_node.run()
