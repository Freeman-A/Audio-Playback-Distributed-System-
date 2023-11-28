import socket


class BootstrapClient:
    def __init__(self, bootstrap_host, bootstrap_port):
        self.bootstrap_host = bootstrap_host
        self.bootstrap_port = bootstrap_port

    def connect_to_bootstrap(self):
        bootstrap_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bootstrap_socket.connect((self.bootstrap_host, self.bootstrap_port))

        servers_str = bootstrap_socket.recv(1024).decode('utf-8')
        servers_list = servers_str.split(',')

        print("Connected Servers:")
        for server in servers_list:
            print(server)

        bootstrap_socket.close()


def main():
    bootstrap_client = BootstrapClient('127.0.0.1', 9090)
    bootstrap_client.connect_to_bootstrap()


if __name__ == "__main__":
    main()
