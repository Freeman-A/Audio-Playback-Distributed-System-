import socket
import threading


class LoadStrapper(socket.socket):
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()
        self.connected_nodes = {}
        self.connected_clients = {}

    def initialize(self):
        """
        Binds the socket to an available port in the range 50000-50010.

        Returns:
            bool: True if the socket is successfully bound to a port, False otherwise.
        """
        host = "172.27.192.1"
        for port in range(50000, 50011):
            try:
                self.bind((host, port))
                print(f"Socket bound to {host}:{port}")
                return True
            except:
                print(f"Socket bind failed on {host}:{port}")

        print(f"Unable to bind to any port in range 50000, 50010")
        return False

    def handle_connections(self, conn, addr):
        """
        Handles a new connection to the load balancer.

        Args:
            conn (socket.socket): The socket object representing the connection.
            addr (tuple): The address of the connected node.

        Returns:
            None
        """
        while True:
            try:
                data = conn.recv(1024).decode("utf-8")

                if not data:
                    break

                name, node_type, node_purpose = data.split(":")

                with self.lock:
                    print(
                        f"Connection at {addr} has been established with {name}")

                    match node_purpose:
                        case "Establish Connection":
                            if node_type == "AuthNode":
                                self.connected_nodes[name] = {
                                    'type': node_type, 'address': addr[0], 'port': addr[1]}
                        case "Authenticate":
                            if node_type == "Client":
                                # Authenticate the user send them the address of an available auth node
                                self.connected_clients[name] = {'type': node_type,
                                                                'address': addr[0], 'port': addr[1]}

                                auth_node = next(
                                    (node for node in self.connected_nodes if self.connected_nodes[node]['type'] == "AuthNode"))
                                if auth_node:
                                    auth_node_address = self.get_node_info(
                                        auth_node)
                                    response = f"{auth_node}:{auth_node_address}"
                                    conn.sendall(response.encode("utf-8"))
                                else:
                                    print("No auth node available")

            except ConnectionResetError:
                print(
                    f"Connection at {addr} has been closed: {name}")
                conn.close()
                del self.connected_nodes[name]
                break

    def start(self):
        """
        Starts the load balancer by listening for incoming connections.

        Returns:
            None
        """
        self.listen(5)
        print("Socket is listening for connections")
        try:
            while True:
                conn, addr = self.accept()
                thread = threading.Thread(
                    target=self.handle_connections, args=(conn, addr))
                thread.start()
        except KeyboardInterrupt:
            print("Load balancer shutting down...")
        finally:
            self.close()

    def get_node_info(self, node_name):
        """
        Get the address and port of the node with the given name.
        Args:
            node_name (str): The name of the node.
        Returns:
            tuple: The address and port of the node.
        """
        with self.lock:
            return self.connected_nodes.get(node_name, None)


if __name__ == "__main__":
    load_balance_node = LoadStrapper(socket.AF_INET, socket.SOCK_STREAM)
    if load_balance_node.initialize():
        try:
            load_balance_node.start()
        except:
            print("Error in starting the load balancer")
