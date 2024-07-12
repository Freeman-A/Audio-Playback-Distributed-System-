import socket
import threading
import traceback
import subprocess
import random
import time
import json
import threading


class BootStrapper():
    def __init__(self):
        self.lock = threading.Lock()
        self.bootstrap_ip = "10.30.8.126"
        self.auth_nodes = {}
        self.content_nodes = {}
        self.node_counter = {"AuthNodes": 0, "ContentNodes": 0}
        self.bootstrap_socket = None
        self.threads = []  # List to keep track of threads

    def bind_server_socket(self, host):
        for port in range(50000, 50011):
            try:
                self.bootstrap_socket.bind((host, port))
                print(f"Socket bound to {host}:{port}")
                return port
            except:
                print(f"BootStrap bind failed on {host}:{port}")

    def start_bootstrap(self):
        self.bootstrap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bootstrap_ip = socket.gethostbyname(socket.gethostname())
        try:
            port = self.bind_server_socket(self.bootstrap_ip)
        except:
            print(f"Unable to bind to any port in range 50000, 50010")

        self.bootstrap_socket.listen(5)
        print(f"Server started on port {port}")

        while True:
            client_socket, client_address = self.bootstrap_socket.accept()

            t = threading.Thread(target=self.handle_client_messages, args=(client_socket,))
            self.threads.append(t)
            t.start()

    def handle_client_messages(self, client_socket):
        while True:
            try:
                message_str = client_socket.recv(1024).decode("utf-8")
                if message_str:
                    message = json.loads(message_str)

                    node_type = message.get("node_type")
                    node_name = message.get("node_name")

                    if message.get("purpose") == "REQUEST_NODE_INFO":
                        node_info = self.get_node_info(node_name)
                        client_socket.sendall(json.dumps(node_info).encode("utf-8"))

                    if node_type == "AuthNode":
                        with self.lock:
                            self.auth_nodes[node_name] = {
                                "address": message.get("node_IP"),
                                "port": message.get("node_port")
                            }
                            self.node_counter["AuthNodes"] += 1
                    elif node_type == "ContentNode":
                        with self.lock:
                            self.content_nodes[node_name] = {
                                "address": message.get("node_IP"),
                                "port": message.get("node_port")
                            }
                            self.node_counter["ContentNodes"] += 1

                    elif node_type == "Client":
                        if message.get("purpose") == "REQUEST_AUTH_NODE":
                            if self.node_counter["AuthNodes"] > 0:
                                auth_node = random.choice(list(self.auth_nodes.values()))
                                client_socket.sendall(json.dumps(auth_node).encode("utf-8"))
                            else:   # If no AuthNode is available
                                client_socket.sendall(json.dumps({"error": "No AuthNode available"}).encode("utf-8"))
                        if message.get("purpose") == "REQUEST_CONTENT_NODE":
                            if self.node_counter["ContentNodes"] > 0:
                                content_node = random.choice(list(self.content_nodes.values()))
                                client_socket.sendall(json.dumps(content_node).encode("utf-8"))
                            else:   # If no ContentNode is available
                                client_socket.sendall(json.dumps({"error": "No ContentNode available"}).encode("utf-8"))

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
        while True:
            if self.node_counter["AuthNodes"] < 1 and self.node_counter["ContentNodes"] < 1:
                print("Warning: No Nodes available - Services Offline")
                print("Booting up nodes")

                if self.node_counter["AuthNodes"] < 2:
                    print("Booting up AuthNodes")
                    file_location = "nodes/AuthNode.py"
                    self.start_node(file_location)

                if self.node_counter["ContentNodes"] < 2:
                    print("Booting up ContentNodes")
                    file_location = "nodes/ContentNode.py"
                    self.start_node(file_location)

            else:
                print("Services running")
                print(f"AuthNodes: {self.node_counter['AuthNodes']}")
                print(f"ContentNodes: {self.node_counter['ContentNodes']}")

            time.sleep(60)

    def run(self):
        self.bootstrap_ip = input("Enter the IP address of the server: ")

        t1 = threading.Thread(target=self.start_bootstrap)
        t1.start()
        self.threads.append(t1)

        t2 = threading.Thread(target=self.service_node_checker)
        t2.start()
        self.threads.append(t2)

        # Wait for threads to finish before exiting
        for t in self.threads:
            t.join()

    def get_node_info(self, node_name):
        if node_name in self.auth_nodes:
            return self.auth_nodes[node_name]
        elif node_name in self.content_nodes:
            return self.content_nodes[node_name]
        else:
            return {"error": "Node not found"}


if __name__ == "__main__":
    bootstrap = BootStrapper()
    bootstrap.run()