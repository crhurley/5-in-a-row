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

        #Create socket object to connect to server
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.info("Client socket connected")
        except socket.error:
            logging.error("Could not create client socket")

        #Connect to specified port
        try:
            self.server_socket.connect((host,port))
            logging.info("Successfully connected to host %s at port %s", host, port)
        except socket.error:
            logging.error("Failed to connect to host %s at port %s", host, port)
            sys.exit()

    def send_username(self):
        # Send username to server to register as a new player
        client_message = json.dumps({"new_player": self.username})
        self.server_socket.send(client_message.encode())
        logging.info("User %s sent to server", self.username)

        # Get response from server
        from_server = self.server_socket.recv(4096).decode()
        print(from_server)

        # Exit if we already have two players
        if from_server == "400 FULL":
            print("Sorry %s, we already have two players " % (self.username))
            print("Exiting")
            self.server_socket.close()
            sys.exit()

    def play_game(self):
        """Client loop. Always either waiting for further instructions and not taking user input
        or taking user input and returning server response"""
        while True:
            self.response=json.loads(self.server_socket.recv(4096).decode())
            logging.info("Start of client loop. Response from server %s: ", self.response)

            # Wait for second player to join
            while self.response["status"] == "200 WAIT_PLAYER":
                print("We are waiting for one more player")
                self.response=json.loads(self.server_socket.recv(4096).decode())

            # Wait for your first turn
            if self.response["status"] == "200 WAIT_TURN":
                print("Please wait for your opponent's turn")

            if self.response["status"] == "200 READY":
                logging.info("Taking turn")
                self.make_move()

                # Wait for your turn
                if self.response["status"] == "200 WAIT_TURN":
                    print("Please wait for your opponent's turn")

    def make_move(self):
        input_validated = False
        # Keep prompting until the server accepts the input
        while not input_validated:
            #Take user input from command line interface
            user_input=input("5row->")

            #Send user input to server, and collect response
            client_message = json.dumps({"current_player": self.username, "next_move": user_input})
            self.server_socket.send(client_message.encode())
            self.response=json.loads(self.server_socket.recv(4096).decode())
            logging.info("After move, response from server %s: ", self.response)

            # Close socket and quit if user chooses to exit
            if self.response["status"] == "200 DISC":
                self.server_socket.close()
                sys.exit()

            #Error handling
            if self.response["status"]=="400 ERR":
                print("Invalid command, please try again")
                input_validated = False
            else:
                input_validated = True

    def exit(self):
        try:
            # Send exit message to server
            client_message = json.dumps({"current_player": self.username, "next_move": "exit"})
            self.server_socket.send(client_message.encode())

            # Make sure to close the socket when we're done
            self.server_socket.close()
            sys.exit()
        except:
            logging.info("Socket already closed")
            sys.exit()

    def run(self):
        try:
            self.get_username()
            self.setup_connection()
            self.send_username()
            self.play_game()

            self.exit()

        # Handle KeyboardInterrupt
        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt received, exiting")
            self.exit()


if __name__ == "__main__":
    Client().run()
