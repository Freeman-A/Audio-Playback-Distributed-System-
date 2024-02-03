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

    def initialize(self):
        """
        Binds the socket to an available port in the range 50000-50010.

        Returns:
            bool: True if the socket is successfully bound to a port, False otherwise.
        """
        host = socket.gethostbyname(socket.gethostname())
        for port in range(50000, 50011):
            try:
                self.bind((host, port))
                print(f"Socket bound to {host}:{port}")
                return True
            except:
                print(f"Socket bind failed on {host}:{port}")

        print(f"Unable to bind to any port in range 50000, 50010")

    def handle_connection(self, name, conn, addr):
        """
        Handles a new connection to the load balancer.

        Args:
            name (str): The name of the connection.
            conn (socket.socket): The socket object representing the connection.
            addr (tuple): The address of the client.

        Returns:
            None
        """
        print(f"Connection of {name} at {addr} has been established")

    def start(self):
        """
        Starts the load balancer by listening for incoming connections.

        Returns:
            None
        """
        self.listen(5)
        print("Socket is listening for connections")
        while True:
            conn, addr = self.accept()
            thread = threading.Thread(
                target=self.handle_connection, args=(conn, addr))
            thread.start()


if __name__ == "__main__":
    load_balance_node = LoadStrapper(socket.AF_INET, socket.SOCK_STREAM)
    if load_balance_node.initialize():
        try:
            load_balance_node.start()
        except:
            print("Error in starting the load balancer")
