import socket
import threading


class LoadStrapper(socket.socket):
    """
    A class representing a load balancer node.

    Inherits from the `socket.socket` class.

    Attributes:
        None

    Methods:
        initialize: Binds the socket to an available port in the range 50000-50010.
        handle_connection: Handles a new connection to the load balancer.
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
        while True:
            try:
                data = conn.recv(1024).decode("utf-8")

                if not data:
                    break

                node_name, node_type = data.split(":")

                with self.lock:
                    print(
                        f"Connection at {addr} has been established with {node_name}")
                    self.connected_nodes[node_name] = {
                        'type': node_type, 'address': addr[0], 'port': addr[1]}

                    print(self.connected_nodes)

                # Send a response message to the connected node
                response = "Message received"
                conn.send(response.encode("utf-8"))

            except ConnectionResetError:
                print(f"Connection at {addr} has been closed")
                break

        conn.close()

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


if __name__ == "__main__":
    load_balance_node = LoadStrapper(socket.AF_INET, socket.SOCK_STREAM)
    if load_balance_node.initialize():
        try:
            load_balance_node.start()
        except:
            print("Error in starting the load balancer")
