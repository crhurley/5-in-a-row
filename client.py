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
            self.server_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            logging.info("Client socket connected")
        except socket.error:
            logging.error("Could not create client socket")

        #Connect to specified port
        try:
            self.server_socket.connect((host,port))
            logging.info(
                "Successfully connected to host %s at port %s",
                host,
                port
            )
        except socket.error:
            logging.error(
                "Failed to connect to host %s at port %s",
                host,
                port
            )
            sys.exit()

    def send_username(self):
        # Send username to server to register as a new player
        client_message = json.dumps({
            "new_player": self.username
        })
        self.server_socket.send(client_message.encode())
        logging.info("User %s sent to server", self.username)

        # Get response from server
        user_response =json.loads(
            self.server_socket.recv(4096).decode()
        )
        logging.info("user_response %s ", user_response)

        # Print message on successful join
        if user_response["status"] == "200 JOIN":
            print(f"Welcome to the game {self.username}")

        # Exit if we already have two players
        elif user_response["status"] == "400 FULL":
            print(f"Sorry {self.username}, we already have two players")
            print("Exiting")
            self.server_socket.close()
            sys.exit()

    def play_game(self):
        """Client loop. Always either waiting for further
        instructions and not taking user input or taking
        user input and returning server response"""
        while True:
            self.response=json.loads(self.server_socket.recv(4096).decode())
            logging.debug(
                "Start of client loop. Response from server %s: ",
                self.response
            )

            # Make sure we don't prompt if the game is over
            self.check_game_over(self.response)

            # Wait for second player to join
            while self.response["status"] == "200 WAIT_PLAYER":
                print("We are waiting for one more player")
                self.response=json.loads(
                    self.server_socket.recv(4096).decode()
                )

            # Wait for your first turn
            if self.response["status"] == "200 WAIT_TURN":
                print("Please wait for your opponent's turn")

            if self.response["status"] == "200 READY":
                logging.info("Taking turn")
                if ("board" in self.response.keys() and
                        "marker" in self.response.keys()):
                    board = self.response["board"]
                    marker = self.response["marker"]
                    self.make_move(board, marker)

                # Wait for your turn
                if self.response["status"] == "200 WAIT_TURN":
                    print("Please wait for your opponent's turn")

    def make_move(self, board, marker):
        input_validated = False
        self.print_board(board, marker)
        # Keep prompting until the server accepts the input
        while not input_validated:
            #Take user input from command line interface
            user_input=input("5row->")

            #Send user input to server, and collect response
            client_message = json.dumps({
                "current_player": self.username,
                "next_move": user_input
            })
            self.server_socket.send(client_message.encode())
            self.response=json.loads(
                self.server_socket.recv(4096).decode()
            )
            logging.debug(
                "After move, response from server %s: ",
                self.response
            )

            self.check_game_over(self.response)
            # Close socket and quit if user chooses to exit
            if self.response["status"] == "200 DISC":
                self.server_socket.close()
                sys.exit()

            #Error handling
            if self.response["status"]=="400 ERR":
                print(f"Sorry {self.username}, that's an invalid command. Please try again")
                input_validated = False
            elif self.response["status"]=="400 COL_FULL":
                print(f"Sorry {self.username}, that column is full")
                input_validated = False
            else:
                input_validated = True

    def print_board(self, board, marker):
        print("The current state of the board is:")
        boardwidth = len(board[0])
        for row in board:
            print(" ".join(row))
        print(
            f"Please enter a number between 1-{boardwidth} to place an {marker}"
        )

    def check_game_over(self, response):
        # Close socket and quit if server says to disconnect
        if response["status"] == "200 DISC":
            print("Server error. Have to disconnect")
            self.exit()

        # Close socket and quit if user won
        if response["status"] == "200 WIN":
            print(f"Congratulations {self.username}! You won!")
            self.exit()

        # Close socket and quit if user lost
        if response["status"] == "200 LOSS":
            print(f"Sorry {self.username}. You lost!")
            self.exit()

        # Close socket and quit if draw
        if response["status"] == "200 DRAW":
            print(f"The game ended in a draw {self.username}")
            self.exit()

    def exit(self):
        try:
            # Send exit message to server
            client_message = json.dumps({
                "current_player": self.username,
                "next_move": "exit"
            })
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
