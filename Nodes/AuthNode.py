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

                    match purpose:
                        case "AUTHENTICATE":
                            username = message.get("username")
                            password = message.get("password")

                            authentication_status = self.authenticate_user(
                                username, password)

                            client_socket.sendall(
                                authentication_status.encode("utf-8"))

            except json.JSONDecodeError:
                print("Error decoding JSON. Empty or invalid message received.")
            except:
                print("Error handling client messages", traceback.print_exc())
                break

    def authenticate_user(self, username, password):
        """
        Authenticates the user by checking the username and password against the database.
        """
        file_path = "data/user_data.json"

        print(f"File path: {file_path}")

        if not os.path.exists(file_path):
            print("User database not found.")
            return "Authentication failed"

        try:
            with open(file_path, "r") as file:
                file_content = file.read()
                if not file_content:
                    print("User database is empty.")
                    user_data = []
                else:
                    try:
                        user_data = json.loads(file_content)
                    except json.JSONDecodeError as json_error:
                        print(f"Error decoding JSON: {json_error}")
                        return "Authentication failed - JSON decoding error"

                print("User data:", user_data)

            if any(user["username"] == username and user["password"] == password for user in user_data):
                return "Authentication successful"
            else:
                # Add the user to the database
                user_data.append({"username": username, "password": password})

            # Write back to the file outside the 'with' statement to ensure proper closing
            with open(file_path, "w") as file:
                json.dump(user_data, file, indent=4)

            return "User added to the database"
        except Exception as e:
            print(f"Error: {e}")
            return "Authentication failed - General error"

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

        file_path = "data/user_data.json"

        try:
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
