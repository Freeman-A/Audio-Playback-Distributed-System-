import socket
import random
import threading
import traceback
import time
import os
import json
import sqlite3


class AuthNode():
    def __init__(self, bootstrap_ip=None):
        self.node_name = f"AN{random.randint(0, 10)}"
        self.bootstrap_ip = "10.30.8.126"
        self.node_ip = None
        self.node_port = None
        self.server_socket = None
        self.user_database = None
        self.user_cursor = None

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

    def connect_to_bootstrapper(self):
        try:
            bootstrapper_client = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            bootstrapper_client.settimeout(3)
            bootstrapper_client.connect((self.bootstrap_ip, 50000))
            print("Connected to load balancer")

            # Send node details to load balancer
            node_details = {
                "node_name": self.node_name,
                "node_IP":  self.node_ip,
                "node_port": self.node_port,
                "node_type": "AuthNode"
            }

            json_data = json.dumps(node_details)

            bootstrapper_client.sendall(json_data.encode("utf-8"))
            bootstrapper_client.close()

            print("Node details sent to load balancer")

        except Exception as e:
            print(f"Error connecting to load balancer: {e}")

    def start_auth_node(self):
        self.initilize_database()
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

                        case "register":
                            register_user_status = self.register_user(
                                username, password)

                            if register_user_status:
                                client_socket.sendall(
                                    register_user_status.encode("utf-8"))

                        case _:
                            print("Invalid purpose")

            except json.JSONDecodeError:
                print("Error decoding JSON. Empty or invalid message received.")
            except:
                print(
                    f"Client disconnected from {client_socket.getpeername()}")
                return

    def validate_credentials(self, username, password):
        with sqlite3.connect("data/user_credentials.db") as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user:
                # Assuming password is the second column
                stored_password = user[1]
                if stored_password == password:
                    return "AUTHORIZED"
                else:
                    return "UNAUTHORIZED"
            else:
                return "NO_USER_FOUND"

    def register_user(self, username, password):
        with sqlite3.connect("data/user_credentials.db") as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT * FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()

            if user:
                return "USER_EXISTS"
            else:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                connection.commit()
                return "REGISTERED"

    def initilize_database(self):
        database_exists = os.path.exists("data/user_credentials.db")

        with sqlite3.connect("data/user_credentials.db") as connection:
            self.user_database = connection
            self.user_cursor = connection.cursor()

            if not database_exists:
                # Create the users table if the database is newly created
                self.user_cursor.execute(
                    "CREATE TABLE users (username TEXT, password TEXT)")
                connection.commit()

    def run(self):
        if self.bootstrap_ip is None:
            self.bootstrap_ip = input("Enter the IP address of the server: ")
            return

        server_thread = threading.Thread(target=self.start_auth_node)
        server_thread.start()

        time.sleep(1)  # Wait for server to start

        self.connect_to_bootstrapper()

        server_thread.join()


if __name__ == "__main__":
    auth_node = AuthNode()
    auth_node.run()
