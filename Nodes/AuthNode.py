import socket
import random
import threading
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

    def connect_to_loadbalancer(self, load_balancer_ip):
        try:
            node_type = "AuthNode"
            purpose = "Establish Connection"
            data = f"{self.node_name}:{node_type}:{purpose}"
            self.connect((load_balancer_ip, 50000))
            self.sendall(data.encode("utf-8"))

            print("Node name successfully sent to Loadstrapper.")

            # Start a separate thread for ongoing communication with the Load Balancer
            threading.Thread(
                target=self.communicate_with_load_balancer).start()

            # Start a separate thread to listen for client connections
            threading.Thread(target=self.listen_for_clients).start()

        except ConnectionRefusedError:
            print("Error connecting to Loadstrapper: Connection refused")
        except Exception as e:
            print(f"Error connecting to Loadstrapper: {str(e)}")

    def communicate_with_load_balancer(self):
        try:
            while True:
                time.sleep(320)
                print("Sending heartbeat to Load Balancer")
                self.sendall("Heartbeat".encode("utf-8"))
        except Exception as e:
            print(f"Error in communicating with Load Balancer: {str(e)}")

    def listen_for_clients(self):
        try:
            self.listen(5)
            while True:
                conn, addr = self.accept()
                threading.Thread(target=self.handle_client,
                                 args=(conn, addr)).start()

        except Exception as e:
            print(f"Error in listening for clients: {str(e)}")

    def handle_client(self, conn, addr):
        try:
            data = conn.recv(1024).decode("utf-8")
            
            if data: 
                purpose, username, password = data.split(":")
                match purpose: 
                    case "login":
                        
            
            

            print(f"Received data from {addr}: {data}")

            # Authenticate the client
            self.authenticate_client(conn, addr, data)

        except Exception as e:
            print(f"Error in handling client: {str(e)}")


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
