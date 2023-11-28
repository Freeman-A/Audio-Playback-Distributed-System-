import socket
import threading
import pickle

class BootstrapNode:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.lock = threading.Lock()

    def start(self):
        bootstrap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bootstrap_socket.bind((self.host, self.port))
        bootstrap_socket.listen(5)

        print(f"Bootstrap Node listening on {self.host}:{self.port}")

        while True:
            client_socket, client_address = bootstrap_socket.accept()  # connected clients(nodes)
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_socket,))  # target service
            client_thread.start()

    def handle_client(self, client_socket):
        with self.lock:
            self.clients.append(client_socket)

        connected_clients_str = ",".join(
            [f"{client.getpeername()[0]}:{client.getpeername()[1]}" for client in self.clients])

        print(connected_clients_str)
        
        data = client_socket.recv(1024)
        recieved_message = pickle.loads(data)

        print(recieved_message)

def main():
    boostrap_node = BootstrapNode("127.0.0.1", 50002)
    bootstrap_thread = threading.Thread(target=boostrap_node.start())
    bootstrap_thread.start()


if __name__ == "__main__":
    main()
