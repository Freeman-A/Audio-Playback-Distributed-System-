import socket
import random
import time


class AuthNode(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.node_name = f"AN{random.randint(1, 10)}"

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
            except Exception as e:
                print(f"Binding failed on {host}:{port}")

        print("Unable to bind to any port in range 50000, 50010")
        return False

        # need to alter the code to start a thread to connect to the load balancer and close the connection and then start a thread to connect to the auth node and accept messages from the client

    def connect_to_loadbalancer(self, load_balancer_ip):
        try:
            node_type = "AuthNode"
            data = f"{self.node_name}:{node_type}"
            self.connect((load_balancer_ip, 50000))
            self.sendall(data.encode("utf-8"))

            print("Node name successfully sent to Loadstrapper.")

            self.settimeout(60)

            while True:
                time.sleep(60)
                print("Alive")

        except ConnectionRefusedError:
            print("Error connecting to Loadstrapper: Connection refused")
        except Exception as e:
            print(f"Error connecting to Loadstrapper: {str(e)}")


if __name__ == "__main__":
    auth_node = AuthNode(socket.AF_INET, socket.SOCK_STREAM)
    if auth_node.initialize():
        try:
            auth_node.connect_to_loadbalancer("172.27.192.1")
        except KeyboardInterrupt:
            print("Node closed by user")
        except:
            print("Error in connecting to the load balancer")
        finally:
            auth_node.close()
