import socket
import json
import logging
import os
import sys

class Server():
    # Set log level to environment variable LOGLEVEL
    # or default to ERROR
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "ERROR"))

    def __init__(self, players=[]):
        #Keep track of players currently in the game
        self.players = players

    def setup_connection(self):
        # Setup connection parameters
        host='127.0.0.1'
        port=1337

        #Create server socket object
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.info("Server socket connected")
        except socket.error:
            logging.error("Could not create server socket")

        # Allow socket to be reused for testing
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #Bind to specified port
        try:
            self.server_socket.bind((host,port))
            logging.info("Successfully binded to host %s at port %s", host, port)
        except socket.error:
            logging.error("Failed to bind to host %s at port %s", host, port)
            sys.exit()

        self.server_socket.listen(5)
        logging.info("Listening")

    # Add player to the game if there is space
    def add_player(self, player):
        logging.info("Current players: %s", self.players)
        if len(self.players) < 2:
            self.players.append(player)
            logging.info("New player %s added", player)
            response = "Welcome to the game " + player
            return response
        else:
            response = "Sorry %s, we already have two players " % (player)
            return response


    def run(self):
        self.setup_connection()

        # Main connection loop. Handles all messages from client
        while True:
            conn, addr = self.server_socket.accept()
            while True:
                data = conn.recv(4096).decode()
                logging.info("Received data: %s", data)

                if not data:
                    logging.info("Empty message received")
                    break

                data = json.loads(data)
                # Add a new player
                if "new_player" in data.keys():
                    server_response = self.add_player(data["new_player"])
                    conn.send(server_response.encode())

            conn.close()
            print('client disconnected')

if __name__ == "__main__":
    Server().run()
