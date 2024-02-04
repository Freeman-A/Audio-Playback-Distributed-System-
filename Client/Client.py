import socket
import socket
import wx
import time


class Client(socket.socket):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app = wx.App(False)
        self.frame = wx.Frame(None, wx.ID_ANY, "Client Node")
        self.panel = wx.Panel(self.frame, wx.ID_ANY)

        self.button = wx.Button(self.panel, label="Authenticate", pos=(10, 70))
        self.button.Bind(wx.EVT_BUTTON, self.on_authenticate)

        self.frame.Show(True)
        self.app.MainLoop()

    def on_authenticate(self, event):
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()
        self.authenticate(username, password)

    def initialize(self):
        host = self.gethostname(self.gethostname())
        for port in range(50000, 50011):
            try:
                self.bind((self.gethostbyname(host), port))
                print(f"Socket bound to {host}:{port}")
                return True
            except Exception as e:
                print(f"Binding failed on {host}:{port}")

    def connect_to_loadbalancer(self, load_balancer_ip, purpose):
        try:
            node_type = "Client"
            purpose = purpose
            data = f"{self.node_name}:{node_type}:{purpose}"
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
    client = Client(socket.AF_INET, socket.SOCK_STREAM)
    if client.initialize():
        try:
            client.authenticate("172.27.192.1")
        except:
            print("Client closed")
