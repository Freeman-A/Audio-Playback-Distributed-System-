import socket
import threading
import traceback
import random
import queue
import time
import json


class LoadStrapper():
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
        load_balance_node = LoadStrapper(socket.AF_INET, socket.SOCK_STREAM)
        if load_balance_node.initialize():
            load_balance_node.start()
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.auth_nodes = {}
        self.content_nodes = {}
        self.node_counter = {"AuthNodes": 0, "ContentNodes": 0}
        self.bootstrap_socket = None

        # Event to signal when AuthNode is ready
        self.node_ready_event = threading.Event()
        # Queue to pass auth_node details between threads
        self.node_queue = queue.Queue()

    def bind_server_socket(self, host):
        for port in range(50000, 50011):
            try:
                self.bootstrap_socket.bind((host, port))
                print(f"Socket bound to {host}:{port}")
                return port
            except:
                print(f"BootStrap bind failed on {host}:{port}")

    def start_bootstrap_loadbalancer(self):
        self.bootstrap_socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        bootstrap_ip = socket.gethostbyname(socket.gethostname())
        try:
            port = self.bind_server_socket(bootstrap_ip)

        except:
            print(f"Unable to bind to any port in range 50000, 50010")

        self.bootstrap_socket.listen(5)
        print(f"Server started on port {port}")

        while True:
            client_socket, client_address = self.bootstrap_socket.accept()
            # Handle client connection here

            print(f"Received connection from {client_address}")

            threading.Thread(target=self.handle_clients,
                             args=(client_socket,)).start()  # Start a new thread to handle the client

    def get_auth_node_details(self):
        if self.node_counter["AuthNodes"] >= 1:
            auth_node = random.choice(list(self.auth_nodes.values()))

            json_data = json.dumps(auth_node)

            return json_data

        else:
            return None

    def execute_auth_node_script(self, file_path: str):
        try:
            with open(file_path) as file:
                auth_node_script = file.read()
                exec(auth_node_script)

                # Notify the main thread that AuthNode is ready
                self.auth_node_ready_event.set()
        except FileNotFoundError:
            print("Script not found")
        except Exception:
            print("Error executing script")

    def handle_clients(self, client_socket):
        while True:
            try:
                message_str = client_socket.recv(1024).decode("utf-8")
                if message_str:
                    message = json.loads(message_str)

                    print(message)

                    if message.get("node_type") == "AuthNode":
                        self.auth_nodes[message.get("node_name")] = {
                            "node_IP": message.get("node_IP"),
                            "node_port": message.get("node_port")
                        }
                        self.node_counter["AuthNodes"] += 1
                        print(f"AuthNode {message.get('node_name')} connected")

                    elif message.get("node_type") == "ContentNode":
                        self.content_nodes[message.get("node_name")] = {
                            "node_IP": message.get("node_IP"),
                            "node_port": message.get("node_port")
                        }
                        self.node_counter["ContentNodes"] += 1
                        print(
                            f"ContentNode {message.get('node_name')} connected")
                    elif message.get("node_type") == "Client":
                        if message.get("purpose") == "REQUEST_AUTH_NODE":
                            if self.node_counter["AuthNodes"] > 0:
                                auth_node = random.choice(
                                    list(self.auth_nodes.values()))
                                client_socket.sendall(
                                    json.dumps(auth_node).encode("utf-8"))
                            else:
                                client_socket.sendall(
                                    json.dumps({"NO_AUTH_NODES"}).encode("utf-8"))
                        elif message.get("purpose") == "REQUEST_CONTENT_NODE":
                            if self.node_counter["ContentNodes"] > 0:
                                content_node = random.choice(
                                    list(self.content_nodes.values()))
                                client_socket.sendall(
                                    json.dumps(content_node).encode("utf-8"))
                            else:
                                client_socket.sendall(
                                    json.dumps({"NO_CONTENT_NODES"}).encode("utf-8"))
                        elif message.get("purpose") == "AUTHENTICATION_NODE_ERROR":
                            print("Error: Node Error")
                            # check if there is an autnetication node available
                            # if not execute the Authnode program and send the client the address of the new authnode
                            if self.node_counter["AuthNodes"] < 1:
                                auth_node_thread = threading.Thread(
                                    target=self.execute_auth_node_script, args=("nodes\AuthNode.py",)).start()

                                self.node_ready_event.wait()
                                client_socket.sendall(
                                    self.get_auth_node_details()).encode("utf-8")

            except Exception:
                traceback.print_exc()

    def run(self):
        server_thread = threading.Thread(
            target=self.start_bootstrap_loadbalancer)
        server_thread.start()

    def get_node_info(self, node_name, node_type):
        """
        Get the address and port of the node with the given name.
        Args:
            node_name (str): The name of the node.
        Returns:
            tuple: The address and port of the node.
        """
        if node_type == "AuthNode":
            return self.auth_nodes.get(node_name)
        elif node_type == "ContentNode":
            return self.content_nodes.get(node_name)
        else:
            return None


if __name__ == "__main__":
    bootstrap = LoadStrapper()
    bootstrap.run()
