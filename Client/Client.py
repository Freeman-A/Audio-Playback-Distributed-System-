import socket
import socket
import wx
import random


class Client(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_name = f"C{random.randint(1, 10)}"
        self.app = wx.App(False)
        self.frame = wx.Frame(None, wx.ID_ANY, "Client Node", size=(300, 200))
        self.panel = wx.Panel(self.frame, wx.ID_ANY)

        self.button = wx.Button(self.panel, label="Authenticate", pos=(0, 0))
        self.button.Bind(wx.EVT_BUTTON, self.authenticate)

        self.frame.Show(True)
        self.app.MainLoop()

    def authenticate(self, address):
        try:
            self.connect_to_loadbalancer(
                address, "Authenticate")

            if address:
                pass

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

                    return auth_node_address

        except ConnectionRefusedError:
            print("Error connecting to Loadstrapper: Connection refused")
            pass
        except Exception as e:
            print(f"Error connecting to Loadstrapper: {str(e)}")


if __name__ == "__main__":
    client = Client(socket.AF_INET, socket.SOCK_STREAM)
    if client.initialize():
        try:
            client.authenticate("172.27.192.1")
        except:
            print("Client closed")
