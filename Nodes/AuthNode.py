import socket
import random
import threading
import time


class AuthNode(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node_name = f"AN{random.randint(1, 10)}"

    def assign_ports(self):
        """
        Binds the socket to an available port in the range 50000-50010.

        Returns:
            tuple: A tuple containing the load balancer port and client port if successfully bound, None otherwise.
        """
        host = socket.gethostbyname(socket.gethostname())
        load_balancer_port = self.find_port_in_range(host)

        client_socket = AuthNode(socket.AF_INET, socket.SOCK_STREAM)
        client_port = client_socket.find_port_in_range(host)

        if load_balancer_port is not None and client_port is not None:
            return (load_balancer_port, client_port)
        else:

            print("Unable to bind to any port in range 50000, 50010")
            return False

    def find_port_in_range(self, host):
        """
        Finds an available port in the specified range.

        Args:
            host (str): The host IP address.
            var (int): The port variable to assign the found port to.

        Returns:
            int: The found port if successful, None otherwise.
        """
        for port in range(50000, 50011):
            try:
                self.bind((host, port))
                return port
            except Exception as e:
                print(e)
                print(f"Socket bind failed on {host}:{port}")

    def connect_to_loadbalancer(self, load_balancer_ip, client_port):
        """
        Connects to the load balancer and registers the node's address.

        Args:
            load_balancer_ip (str): The IP address of the load balancer.
        """
        try:
            node_type = "AuthNode"
            purpose = "REGISTERING_NODE_ADDRESS"
            data = f"{self.node_name}:{node_type}:{purpose}:{client_port}"
            self.connect((load_balancer_ip, 50000))
            self.sendall(data.encode("utf-8"))

        except ConnectionRefusedError:
            print("Error connecting to Loadstrapper: Connection refused")
        except Exception as e:
            print(f"Error connecting to Loadstrapper: {str(e)}")

    def handle_client(self, conn, addr):
        """
        Handles the client connection.

        Args:
            conn (socket.socket): The client socket connection.
            addr (tuple): The client address (IP, port).
        """
        try:
            data = conn.recv(1024).decode("utf-8")

            if data:
                purpose, username, password = data.split(":")
                match purpose:
                    case "login":
                        print(f"Received login request from {username}")
                    case "register":
                        print(f"Received registration request")

            print(f"Received data from {addr}: {data}")

            # Authenticate the client
            self.authenticate_client(conn, addr, data)

        except Exception as e:
            print(f"Error in handling client: {str(e)}")


if __name__ == "__main__":
    auth_node = AuthNode(socket.AF_INET, socket.SOCK_STREAM)
    try:
        ports = auth_node.assign_ports()
        if ports:
            load_balancer_port, client_port = ports

            auth_node.connect_to_loadbalancer(
                "172.27.192.1", client_port)
            # Now you can use 'client_port' to listen for client connections
            print(f"Client connections will be accepted on port {client_port}")

    except:
        print("Error in connecting to the load balancer")
    finally:
        auth_node.close()
        print()
