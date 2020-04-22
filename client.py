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
        #Keep track of players currently in the game
        self.username = username

    def run(self):
        # Setup connection parameters
        host='127.0.0.1'
        port=1337

        # Prompt client for username
        self.username = input("Please enter your username: ")
        while not self.username.isalpha():
            print("Only letters are allowed in your username")
            self.username = input("Please enter your username: ")

        #Create socket object
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.info("Client socket connected")
        except socket.error:
            logging.error("Could not create client socket")

        #Connect to specified port
        try:
            client.connect((host,port))
            logging.info("Successfully connected to host %s at port %s", host, port)
        except socket.error:
            logging.error("Failed to connect to host %s at port %s", host, port)
            sys.exit()

        # Send username to server to register as a new player
        client_message = json.dumps({"new_player": self.username})
        client.send(client_message.encode())
        logging.info("User %s sent to server", self.username)

        # Get response from server
        from_server = client.recv(4096)
        print(from_server.decode())

        # Close the socket
        client.close()

if __name__ == "__main__":
    Client().run()
