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
        #Keep track of players currently in the game
        self.players = players
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

        # Main connection loop. Handles all messages from
        while True:
            try:
                cmd = client_connection.recv(4096).decode()
                logging.info("Received cmd: %s", cmd)

                if not cmd:
                    logging.info("Empty message received")
                    break

                cmd = json.loads(cmd)
                client_response = ""

                if "current_player" in cmd.keys():
                    self.current_player = cmd["current_player"]

                # Add a new player and set up match
                if "new_player" in cmd.keys():
                    self.current_player = cmd["new_player"]
                    if self.add_player(cmd["new_player"]):
                        client_response = "Welcome to the game %s!" % (self.current_player)
                        client_connection.send(client_response.encode())
                        while len(self.players) == 1:
                            client_response = json.dumps({"status": "200 WAIT"})
                            client_connection.send(client_response.encode())
                            time.sleep(2)
                        if len(self.players) == 2:
                            client_response = json.dumps({"status": "200 READY"})
                            client_connection.send(client_response.encode())
                    else:
                        client_response = json.dumps({"status": "400 FULL"})
                        client_connection.send(client_response.encode())

                elif "next_move" in cmd.keys():
                    move = cmd["next_move"]
                    logging.info("Processing move %s: ", move)

                    # Valid move
                    if move.isdigit() and len(move) == 1:
                        logging.info("Valid move %s: ", move)
                        client_response = json.dumps({"status": "200 READY"})
                        client_connection.send(client_response.encode())

                    # User wants to exit
                    elif move == "exit":
                        logging.info("self.current_player, self.players: %s %s", self.current_player, self.players)
                        self.lock.acquire()
                        self.players.remove(self.current_player)
                        client_response = json.dumps({"status": "200 DISC"})
                        client_connection.send(client_response.encode())
                        client_connection.close()
                        self.lock.release()
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
            logging.info("New player %s added", player)
            logging.info("Current players: %s", self.players)
            self.lock.release()
            return True
        else:
            return False



    def run(self):
        self.setup_connection()

        # Main program loop
        while True:
            conn, addr = self.client_socket.accept()
            client_thread = threading.Thread(target=self.connect_client, args=(conn,))
            client_thread.start()

if __name__ == "__main__":
    Server().run()
