import socket
import random
import traceback
import time


class Client(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_name = f"Client{random.random()}"

    def establish_user_purpose(self, address):
        try:
            purpose = input("Enter purpose: Login or Register").lower()

            match purpose:
                case "login":
                    username = input("Enter username: ")
                    password = input("Enter password: ")
                    data = f"{purpose}:{username}:{password}"
                    self.connect_to_authnode(address, data)

                case"register":
                    username = input("Enter username: ")
                    password = input("Enter password: ")
                    data = f"{purpose}:{username}:{password}"
                    self.connect_to_authnode(address, data)
                case _:
                    print("Invalid input. Please try again.")

        except Exception as e:
            print("Invalid input. Please try again.")

    def connect_to_authnode(self, address, data):
        try:
            self.connect(address)
            self.sendall(data.encode("utf-8"))

            response = self.recv(1024).decode("utf-8")

            time.timeout(5)

            print(response)

        except ConnectionRefusedError:
            print("Error connecting to AuthNode: Connection refused")
        except Exception as e:
            print(f"Error connecting to AuthNode: {str(e)}")
            print(traceback.format_exc())

    def authenticate(self, address):
        try:

            response = self.connect_to_loadbalancer(
                address, "Authenticate")

            if response:
                name, ip, port = response.split(":")
                self.establish_user_purpose((ip, port))

        except Exception as e:
            print(f"Error in authenticating user: {str(e)}")
        pass

    def initialize(self):
        host = socket.gethostbyname(socket.gethostname())
        for port in range(50000, 50011):
            try:
                self.bind((host, port))
                print(f"Socket bound to {host}:{port}")
                return True
            except Exception as e:
                print(f"Binding failed on {host}:{port}")

        print("Unable to bind to any port in the range 50000-50010")
        return False

    def connect_to_loadbalancer(self, load_balancer_ip, purpose):
        try:

            match purpose:
                case "Authenticate":
                    node_type = "Client"
                    purpose = purpose
                    data = f"{self.client_name}:{node_type}:{purpose}"
                    self.connect((load_balancer_ip, 50000))
                    self.sendall(data.encode("utf-8"))

                    auth_node_address = self.recv(1024).decode("utf-8")

                    self.settimeout(5)

                    if not auth_node_address:
                        print(
                            "Failed to authenticate user. No auth node available. Try again later.")
                        return None

                    self.close()
                    return auth_node_address

        except ConnectionRefusedError:
            print("Error connecting to Loadstrapper: Connection refused")
            pass
        except Exception as e:
            print(f"Error connecting to Loadstrapper: {str(e)}")
            print(traceback.format_exc())


if __name__ == "__main__":
    client = Client(socket.AF_INET, socket.SOCK_STREAM)
    if client.initialize():
        try:
            client.authenticate("172.27.192.1")
        except:
            print("Error in authenticating user")
