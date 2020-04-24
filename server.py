import socket
import json
import logging
import os
import sys
import threading
from threading import RLock
import time

class Server():
    # Set log level to environment variable LOGLEVEL
    # or default to ERROR
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "ERROR"))

    def __init__(self, players=[]):
        # Keep track of players currently in the game
        self.players = players
        # Keep track of connections
        self.connections = {}
        # Keep track of who's turn it is
        self.turn = ""
        self.waiting = ""
        # Keep track of whether we've started the game
        # So that we don't try start it multiple times
        self.game_started = False
        # Lock for threads
        self.lock=RLock()

    def setup_connection(self):
        # Setup connection parameters
        host='127.0.0.1'
        port=1337

        #Create server socket object to allow connection from client
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.info("Server socket connected")
        except socket.error:
            logging.error("Could not create server socket")
            sys.exit()

        # Allow socket to be reused for testing
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #Bind to specified port
        try:
            self.client_socket.bind((host,port))
            logging.info("Successfully binded to host %s at port %s", host, port)
        except socket.error:
            logging.error("Failed to bind to host %s at port %s", host, port)
            sys.exit()

        self.client_socket.listen(5)
        logging.info("Listening")

    def connect_client(self, client_connection):
        """Run for each client that connects to the server
        Handles messages sent from the client and sends corresponding responses"""

        # Main connection loop. Handles all messages from client
        while True:
            try:
                cmd = client_connection.recv(4096).decode()
                logging.info("Received cmd: %s", cmd)

                if not cmd:
                    logging.info("Empty message received")
                    break

                cmd = json.loads(cmd)
                client_response = ""

                # Keep track of who is currently playing
                if "current_player" in cmd.keys():
                    self.current_player = cmd["current_player"]

                # Add a new player and set up match
                if "new_player" in cmd.keys():
                    self.current_player = cmd["new_player"]
                    if self.add_player(cmd["new_player"]):
                        client_response = "Welcome to the game %s!" % (self.current_player)
                        client_connection.send(client_response.encode())

                        # Add new player's connection to the list
                        self.lock.acquire()
                        self.connections[self.current_player] = client_connection
                        self.lock.release()

                        # Waiting for second player
                        while len(self.players) == 1:
                            client_response = json.dumps({"status": "200 WAIT_PLAYER"})
                            client_connection.send(client_response.encode())
                            time.sleep(2)

                        # Second player has arrived we can start the game
                        if len(self.players) == 2 and not self.game_started:
                            # The first player to connect gets the first turn
                            self.turn = self.players[0]
                            self.waiting = self.players[1]
                            logging.info("Starting game: %s goes first: ", self.turn)
                            self.prompt_players()
                            self.game_started = True
                    else:
                        client_response = json.dumps({"status": "400 FULL"})
                        client_connection.send(client_response.encode())

                elif "next_move" in cmd.keys():
                    move = cmd["next_move"]
                    logging.info("Processing move %s: ", move)

                    # Valid move
                    if move.isdigit() and len(move) == 1:
                        logging.info("Valid move %s: ", move)
                        self.prompt_players()

                    # User wants to exit
                    elif move == "exit":
                        logging.info("self.current_player, self.players: %s %s", self.current_player, self.players)
                        self.lock.acquire()
                        self.players.remove(self.current_player)
                        self.lock.release()
                        client_response = json.dumps({"status": "200 DISC"})
                        client_connection.send(client_response.encode())
                        client_connection.close()
                        logging.info("Client %s disconnected", self.current_player)
                        break

                    # Unknown command
                    else:
                        client_response = json.dumps({"status": "400 ERR"})
                        client_connection.send(client_response.encode())

            except BrokenPipeError as bpe:
                logging.info("Connection error from %s, removing them", self.current_player)
                self.players.remove(self.current_player)



    # Add player to the game if there is space
    def add_player(self, player):
        if len(self.players) < 2:
            self.lock.acquire()
            self.players.append(player)
            self.lock.release()
            logging.info("New player %s added", player)
            logging.info("Current players: %s", self.players)
            return True
        else:
            return False

    def prompt_players(self):
        """Prompts players for move and automatically switches turn"""
        logging.info("It's: %s's turn. %s is waiting", self.turn, self.waiting)

        # Tell each player it's their go or else to wait
        ready_response = json.dumps({"status": "200 READY", "turn": self.turn})
        self.connections[self.turn].send(ready_response.encode())
        wait_response = json.dumps({"status": "200 WAIT_TURN"})
        self.connections[self.waiting].send(wait_response.encode())

        # Switch turn
        if self.turn==self.players[0]:
            self.turn=self.players[1]
            self.waiting=self.players[0]
        else:
            self.turn=self.players[0]
            self.waiting=self.players[1]

    def run(self):
        self.setup_connection()

        # Main program loop
        while True:
            conn, addr = self.client_socket.accept()
            client_thread = threading.Thread(target=self.connect_client, args=(conn,))
            client_thread.start()

if __name__ == "__main__":
    Server().run()
