import socket
import threading
import traceback
import subprocess
import random
import time
import json
import threading


class BootStrapper():
    """
    A class representing a load balancer node.

    Inherits from the `socket.socket` class.

    Attributes:
        lock (threading.Lock): A lock object for thread synchronization.
        connected_nodes (dict): A dictionary to store information about connected nodes.

    Methods:
        initialize: Binds the socket to an available port in the range 50000-50010.
        handle_connections: Handles a new connection to the load balancer.
        start: Starts the load balancer by listening for incoming connections.

    Usage:
        load_balance_node = Bootstrapper(socket.AF_INET, socket.SOCK_STREAM)
        if load_balance_node.initialize():
            load_balance_node.start()
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.bootstrap_ip = None
        self.auth_nodes = {}
        self.content_nodes = {}
        self.node_counter = {"AuthNodes": 0, "ContentNodes": 0}
        self.bootstrap_socket = None

    def bind_server_socket(self, host):
        for port in range(50000, 50011):
            try:
                self.bootstrap_socket.bind((host, port))
                print(f"Socket bound to {host}:{port}")
                return port
            except:
                print(f"BootStrap bind failed on {host}:{port}")

    def start_bootstrap(self):
        self.bootstrap_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.bootstrap_ip = socket.gethostbyname(socket.gethostname())
        try:
            port = self.bind_server_socket(self.bootstrap_ip)

        except:
            print(f"Unable to bind to any port in range 50000, 50010")

        self.bootstrap_socket.listen(5)
        print(f"Server started on port {port}")

        while True:
            client_socket, client_address = self.bootstrap_socket.accept()

            # Handle client connection here
            threading.Thread(target=self.handle_client_messages,
                             args=(client_socket,)).start()

    def handle_client_messages(self, client_socket):

        while True:
            try:
                message_str = client_socket.recv(1024).decode("utf-8")
                if message_str:
                    message = json.loads(message_str)

                    node_type = message.get("node_type")
                    node_name = message.get("node_name")

                    if message.get("purpose") == "REQUEST_NODE_INFO":
                        node_info = self.get_node_info(
                            node_name)
                        client_socket.sendall(
                            json.dumps(node_info).encode("utf-8"))

                    if node_type == "AuthNode":
                        print("AuthNode connected from ",
                              client_socket.getpeername())
                        with self.lock:
                            self.auth_nodes[node_name] = {
                                "address": message.get("node_IP"),
                                "port": message.get("node_port")
                            }
                            self.node_counter["AuthNodes"] += 1
                    elif node_type == "ContentNode":
                        print("ContentNode connected from ",
                              client_socket.getpeername())
                        with self.lock:
                            self.content_nodes[node_name] = {
                                "address": message.get("node_IP"),
                                "port": message.get("node_port")
                            }
                            self.node_counter["ContentNodes"] += 1

                    elif node_type == "Client":
                        print("Client connected from ",
                              client_socket.getpeername())
                        if message.get("purpose") == "REQUEST_AUTH_NODE":
                            print("Client requesting AuthNode")

                            if self.node_counter["AuthNodes"] > 0:
                                auth_node = random.choice(
                                    list(self.auth_nodes.values()))
                                client_socket.sendall(
                                    json.dumps(auth_node).encode("utf-8"))
                            else:   # If no AuthNode is available
                                client_socket.sendall(
                                    json.dumps({"error": "No AuthNode available"}).encode("utf-8"))
                        if message.get("purpose") == "REQUEST_CONTENT_NODE":
                            print("Client requesting ContentNode")

                            if self.node_counter["ContentNodes"] > 0:
                                content_node = random.choice(
                                    list(self.content_nodes.values()))
                                client_socket.sendall(
                                    json.dumps(content_node).encode("utf-8"))
                            else:   # If no ContentNode is available
                                client_socket.sendall(
                                    json.dumps({"error": "No ContentNode available"}).encode("utf-8"))

                    else:
                        print("Invalid node type")

            except:
                traceback.print_exc()
                break

    def start_node(self, node_path):
        try:
            subprocess.Popen(["python", node_path])

            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f"Error starting {node_path}: {e}")

    def service_node_checker(self):
        check_interval = 10  # seconds
        health_check_interval = 10 * 6  # 10 minutes

        first_iteration = True  # Flag to identify the first iteration

        while True:
            # Check minimum node count immediately on the first iteration
            if first_iteration or time.time() % health_check_interval == 0:
                if self.node_counter["AuthNodes"] < 2 or self.node_counter["ContentNodes"] < 2:
                    print("Warning: Insufficient Nodes available - Services Offline")
                    print("Booting up nodes")

                    if self.node_counter["AuthNodes"] < 2:
                        print("Booting up AuthNodes")
                        file_location = "nodes/AuthNode.py"
                        self.start_node(file_location)

                    if self.node_counter["ContentNodes"] < 2:
                        print("Booting up ContentNodes")
                        file_location = "nodes/ContentNode.py"
                        self.start_node(file_location)

                # Reset the first_iteration flag after the initial check
                first_iteration = False

            if time.time() % check_interval == 0:
                # Check the health of each node in both the AuthNodes and ContentNodes dictionaries
                for node in self.auth_nodes:
                    self.check_node_health(node)
                for node in self.content_nodes:
                    self.check_node_health(node)

    def check_node_health(self, node_name):
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        node_info = self.get_node_info(node_name)

        try:
            temp_socket.connect((node_info["address"], node_info["port"]))
            temp_socket.settimeout(10)
            live_message = {
                "purpose": "HEALTH_CHECK",
                "node_type": "LoadBalancer"
            }

            temp_socket.sendall(json.dumps(live_message).encode("utf-8"))

            response = temp_socket.recv(1024).decode("utf-8")
            if response != "ALIVE":
                print(f"Node {node_name} is dead")
                self.remove_node(node_name)
            temp_socket.close()
            return

        except socket.timeout:
            print(
                f"Timed out waiting for response from {node_name}. Assuming it's not alive.")
            self.remove_node(node_name)

        except socket.error:
            print(
                f"Node {node_name} is not responding. Removing from the list.")
            self.remove_node(node_name)

        finally:
            temp_socket.close()

    def remove_node(self, node_name):
        if node_name in self.auth_nodes:
            with self.lock:
                del self.auth_nodes[node_name]
                self.node_counter["AuthNodes"] -= 1
        elif node_name in self.content_nodes:
            with self.lock:
                del self.content_nodes[node_name]
                self.node_counter["ContentNodes"] -= 1

    def run(self):
        self.bootstrap_ip = input("Enter the IP address of the server: ")

        threading.Thread(target=self.start_bootstrap).start()

        threading.Thread(
            target=self.service_node_checker).start()

    def get_node_info(self, node_name):
        """
        Get the address and port of the node with the given name.
        Args:
            node_name (str): The name of the node.
        Returns:
            tuple: The address and port of the node.
        """
        if node_name in self.auth_nodes:
            return self.auth_nodes[node_name]
        elif node_name in self.content_nodes:
            return self.content_nodes[node_name]
        else:
            return {"error": "Node not found"}


if __name__ == "__main__":
    bootstrap = BootStrapper()
    bootstrap.run()
