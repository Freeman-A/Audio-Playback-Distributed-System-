import socket
import threading
import traceback
import random
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
        self.clients = {}
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

            threading.Thread(target=self.handle_clients,
                             args=(client_socket,)).start()

    def handle_clients(self, client_socket):
        while True:
            try:
                message_str = client_socket.recv(1024).decode("utf-8")
                if message_str:
                    message = json.loads(message_str)

                    node_type = message.get("node_type")

                    if node_type == "AuthNode":
                        self.auth_nodes[message.get("node_name")] = {"address": message.get(
                            "node_IP"), "port": message.get("node_port")}
                        print(
                            f"Auth Node {message.get('node_name')} connected")

                    elif node_type == "ContentNode":
                        self.content_nodes[message.get("node_name")] = {"address": message.get(
                            "node_IP"), "port": message.get("node_port")}
                        print(
                            f"Content Node {message.get('node_name')} connected")

                    elif node_type == "Client":
                        self.clients[message.get("node_name")] = {
                            "address": client_socket.getpeername()[0], "port": client_socket.getpeername()[1]}

                        if message.get("purpose") == "REQUEST_AUTH_NODE":

                            if self.auth_nodes:
                                if self.node_counter["AuthNodes"] >= 1:
                                    auth_node = random.choice(
                                        list(self.auth_nodes.values()))
                                    client_socket.sendall(
                                        json.dumps(auth_node).encode("utf-8"))

                            else:   # If no AuthNode is available
                                client_socket.sendall(
                                    json.dumps({"Error": "No AuthNode available"}).encode("utf-8"))

                    else:
                        print("Unknown node type")

            except:
                traceback.print_exc()
                break

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
