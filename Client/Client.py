import socket
import random
import threading
import traceback
import json
import time
import os
import playsound


class Client():
    def __init__(self):
        """
        Initializes a Client object.
        """
        self.client_socket = None
        self.authenticated = False
        self.content_node_info = None
        self.auth_node_info = None

    def get_node_details(self, purpose, max_retries=3, retry_delay=3):
        """
        Connects to the bootstrapper and sends node details to request authentication node information.
        Returns the authentication node information received from the bootstrapper.
        Retries the connection if it fails.
        """
        for attempt in range(1, max_retries + 1):
            try:
                self.client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect(("172.24.112.1", 50000))

                # Send node details to bootstrapper
                client_details = {
                    "node_type": "Client",
                    "purpose": purpose
                }

                json_data = json.dumps(client_details)
                self.client_socket.sendall(json_data.encode())

                node_info = self.client_socket.recv(1024).decode("utf-8")
                node_info = json.loads(node_info)

                self.client_socket.close()

                if node_info:
                    if purpose == "REQUEST_CONTENT_NODE":
                        self.content_node_info = (
                            node_info["address"], node_info["port"])
                    elif purpose == "REQUEST_AUTH_NODE":
                        self.auth_node_info = (
                            node_info["address"], node_info["port"])
                return

            except Exception as e:
                print(
                    f"Error getting authentication node details (Attempt {attempt}): {e}")
                time.sleep(retry_delay)

        print(
            f"Failed to get authentication node details after {max_retries} attempts.")
        return None

    def get_credentials(self, purpose):

        print("Enter your credentials")
        username = input("Username: ")
        password = input("Password: ")
        credentials = {
            "username": username,
            "password": password,
            "purpose": purpose
        }

        credentials = json.dumps(credentials)

        return credentials

    def get_purpose(self):
        """
        Returns the purpose of the client.

        """

        while True:
            purpose = input("Login or Register: ").lower()

            if purpose in ["login", "register"]:
                return purpose
            else:
                print("Invalid choice. Please enter either 'Login' or 'Register'.")

    def send_credentials(self, credentials):
        """
        Sends the credentials to the authentication node.
        """
        try:
            self.client_socket.sendall(credentials.encode("utf-8"))
        except ConnectionResetError:
            print("Error: Connection to the server was forcibly closed.")
        # Handle the error or exit the program gracefully

    def connect_to_auth_node(self):
        self.get_node_details("REQUEST_AUTH_NODE")
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect(
                (self.auth_node_info[0], self.auth_node_info[1]))

            return True
        except ConnectionRefusedError:
            print("Error: Connection to the authentication node refused.")
            return

    def authenticate(self):
        """
        Connects to the authentication node using the authentication node information received from the bootstrapper.
        """

        if self.connect_to_auth_node():

            purpose = self.get_purpose()
            credentials = self.get_credentials(purpose)
            self.send_credentials(credentials)

            self.recive_authentication_status()

            self.client_socket.close()

            return

    def recive_authentication_status(self):
        while True:
            try:
                response = self.client_socket.recv(
                    1024).decode("utf-8")

                match response:
                    case "AUTHORIZED":
                        self.authenticated = True
                        return True
                    case "UNAUTHORIZED":
                        print("Invalid credentials.")
                        print("Please try again.")
                        credentials = self.get_credentials("login")
                        self.send_credentials(credentials)
                    case "USER_EXISTS":
                        print("User already exists \n Try again.")
                        credentials = self.get_credentials("register")
                        self.send_credentials(credentials)
                    case "REGISTERED":
                        print("You have been registered.")
                        print("Please login to continue.")
                        credentials = self.get_credentials("login")
                        self.send_credentials(credentials)
                    case _:
                        print("Unknown response from server.")
                        print("Please try again.")
                        purpose = self.get_purpose()
                        credentials = self.get_credentials(purpose)
                        self.send_credentials(credentials)

            except ConnectionResetError:
                print("Error: Connection to the server was forcibly closed.")
                return

    def recive_available_music(self):
        """
        Recives the files from the content node.
        """
        try:
            content_node_info = self.get_node_details("REQUEST_CONTENT_NODE")
            try:
                self.client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)

                self.client_socket.connect(
                    (self.content_node_info[0], self.content_node_info[1]))
            except ConnectionRefusedError:
                print("Error: Connection to the content node refused.")
                return

            message = json.dumps({
                "REQUEST_TYPE": "REQUEST_FILES"
            })

            self.client_socket.sendall(message.encode("utf-8"))

            files = self.client_socket.recv(1024).decode("utf-8")
            files = json.loads(files)

            print("Available music")
            for file in files:
                print(file)

            self.client_socket.close()

        except Exception as e:
            print(f"Error receiving files: {e}")
            traceback.print_exc()

    def handle_music_request(self):
        """
        Handles the music request from the user.
        """
        try:
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)

            self.client_socket.connect(
                (self.content_node_info[0], self.content_node_info[1]))

            try:
                song_request = input(
                    "Enter the name of the song you wish to play: ")

                message = json.dumps({
                    "REQUEST_TYPE": "SONG_REQUEST",
                    "SONG_NAME": song_request
                })

                self.client_socket.sendall(message.encode("utf-8"))

                # Write the WAV data to a temporary file in the "bin" folder
                temp_wav_path = os.path.join("bin", "temp.wav")
                with open(temp_wav_path, 'wb') as temp_wav_file:
                    while True:
                        wav_data_chunk = self.client_socket.recv(4096)
                        if not wav_data_chunk:
                            break
                        temp_wav_file.write(wav_data_chunk)
                        # Play the temporary WAV file
                self.play_wav(temp_wav_path)

                # ask the user if they want to play another song
                play_another = input(
                    "Do you want to play another song? (yes/no): ")
                if play_another.lower() == "yes":
                    self.handle_music_request()

            except Exception as e:
                print(f"Error handling music request: {e}")
                traceback.print_exc()
        except:
            print("Error: Connection to the server was forcibly closed.")

    def play_wav(self, wav_path):
        print(f"Playing {wav_path}")
        playsound.playsound(wav_path)
        # Delete the temporary WAV file when done
        # return back to the function that called it
        os.remove(wav_path)
        return True

    def start(self):
        """
        Starts the authentication process in a separate thread.
        """
        # check if there is not a bin directory to temporarily store the music
        if not os.path.exists("bin"):
            os.makedirs("bin")

        self.authenticate()

        try:
            if self.authenticated == True:
                print(
                    """--------------------------------\nLoggin Successful\n--------------------------------""")
                self.recive_available_music()
                self.handle_music_request()

        except:
            print("Error: Authentication failed.")
            return


if __name__ == "__main__":
    client = Client()
    client.start()
