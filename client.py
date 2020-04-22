import socket
import json
import logging
import os
import sys

class Client():
    # Set log level to environment variable LOGLEVEL
    # or default to ERROR
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "ERROR"))

    def __init__(self, username=''):
        #Current user
        self.username = username

    def get_username(self):
        # Prompt client for username
        self.username = input("Please enter your username: ")
        while not self.username.isalpha():
            print("Only letters are allowed in your username")
            self.username = input("Please enter your username: ")

    def setup_connection(self):
        # Setup connection parameters
        host='127.0.0.1'
        port=1337

        #Create socket object
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.info("Client socket connected")
        except socket.error:
            logging.error("Could not create client socket")

        #Connect to specified port
        try:
            self.client_socket.connect((host,port))
            logging.info("Successfully connected to host %s at port %s", host, port)
        except socket.error:
            logging.error("Failed to connect to host %s at port %s", host, port)
            sys.exit()

    def send_username(self):
        # Send username to server to register as a new player
        client_message = json.dumps({"new_player": self.username})
        self.client_socket.send(client_message.encode())
        logging.info("User %s sent to server", self.username)

        # Get response from server
        from_server = self.client_socket.recv(4096)
        print(from_server.decode())

    def run(self):
        self.get_username()
        self.setup_connection()
        self.send_username()

        # Close the socket
        self.client_socket.close()

if __name__ == "__main__":
    Client().run()
