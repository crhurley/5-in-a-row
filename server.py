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
        self.reset_server(players)

    def reset_server(self, players=[]):
        # Keep track of players currently in the game
        self.players = players
        # Keep track of connections
        self.connections = {}
        # Lock for threads
        self.lock=RLock()
        # Keep track of who's turn it is
        self.turn = ""
        self.waiting = ""
        self.markers = {}
        # Keep track of whether we've started the game
        # So that we don't try start it multiple times
        self.game_started = False
        # Board size
        self.boardheight = 5
        self.boardwidth = 5
        # Board state
        self.board =[]
        # Check if column is full
        self.column_full = False

        # Don't start the server unless the board is the right size
        if not(5 <= self.boardwidth <= 9 and 5 <= self.boardheight <= 9):
            logging.error(
                "SERVER ERROR: Board height and width \
                must be between 5 and 9"
            )
            sys.exit()



    def setup_connection(self):
        # Setup connection parameters
        host='127.0.0.1'
        port=1337

        #Create server socket object to allow connection from client
        try:
            self.client_socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )
            logging.info("Server socket connected")
        except socket.error:
            logging.error("Could not create server socket")
            sys.exit()

        # Allow socket to be reused for testing
        self.client_socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        #Bind to specified port
        try:
            self.client_socket.bind((host,port))
            logging.info(
                "Successfully binded to host %s at port %s",
                host,
                port
            )
        except socket.error:
            logging.error(
                "Failed to bind to host %s at port %s",
                host,
                port
            )
            sys.exit()

        self.client_socket.listen(5)
        logging.info("Listening")

    def connect_client(self, client_connection):
        """Run for each client that connects to the server
        Handles messages sent from the client and sends
        corresponding responses"""

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
                        client_response = json.dumps({
                            "status": "200 JOIN"
                        })
                        client_connection.send(client_response.encode())

                        # Add new player's connection to the list
                        self.lock.acquire()
                        self.connections[self.current_player] = client_connection
                        self.lock.release()

                        # Waiting for second player
                        while len(self.players) == 1:
                            client_response = json.dumps({
                                "status": "200 WAIT_PLAYER"
                            })
                            client_connection.send(client_response.encode())
                            time.sleep(2)

                        # Second player has arrived we can start the game
                        if len(self.players) == 2 and not self.game_started:
                            # Initialise turn and markers
                            self.turn = self.players[0]
                            self.markers[self.players[0]] = 'X'
                            self.waiting = self.players[1]
                            self.markers[self.players[1]] = 'O'
                            logging.info(
                                "Starting game: %s goes first: ",
                                self.turn
                            )
                            self.generate_board()
                            self.prompt_players()
                            self.game_started = True
                    else:
                        client_response = json.dumps({
                            "status": "400 FULL"
                        })
                        client_connection.send(client_response.encode())

                elif "next_move" in cmd.keys():
                    move = cmd["next_move"]
                    logging.info("Processing move %s: ", move)

                    # Valid move
                    if (move.isdigit() and len(move) == 1
                            and int(move) <= self.boardwidth):
                        logging.info("Valid move %s: ", move)
                        self.mark_board(int(move))

                        # Don't prompt both players if the
                        # last column chosen was full
                        if not self.column_full:
                            self.prompt_players()
                        else:
                            self.column_full = False

                    # User wants to exit
                    elif move == "exit":
                        logging.info(
                            "self.current_player, self.players: %s %s",
                            self.current_player,
                            self.players
                        )
                        if self.current_player in self.players:
                            self.lock.acquire()
                            self.players.remove(self.current_player)
                            self.lock.release()
                        client_response = json.dumps({
                            "status": "200 DISC"
                        })
                        client_connection.send(client_response.encode())
                        client_connection.close()
                        logging.info("Client disconnected")
                        self.disconnect_clients()
                        break

                    # Unknown command
                    else:
                        client_response = json.dumps({"status": "400 ERR"})
                        client_connection.send(client_response.encode())

            except (BrokenPipeError, ConnectionResetError) as conn_err:
                logging.error("Connection error")
                self.disconnect_clients()

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

        # Switch turn
        if self.turn==self.players[0]:
            self.turn=self.players[1]
            self.waiting=self.players[0]
        else:
            self.turn=self.players[0]
            self.waiting=self.players[1]
        logging.info(
            "It's: %s's turn. %s is waiting",
            self.turn,
            self.waiting
        )

        # Tell each player whether to go or else to wait
        ready_json = {
            "status": "200 READY",
            "board": self.board,
            "marker": self.markers[self.turn]
        }
        ready_response = json.dumps(ready_json)
        self.connections[self.turn].send(ready_response.encode())
        wait_json = {
            "status": "200 WAIT_TURN",
            "board": self.board,
            "marker": self.markers[self.waiting]
        }
        wait_response = json.dumps(wait_json)
        self.connections[self.waiting].send(wait_response.encode())


    #generate empty board
    def generate_board(self):
        # Maintain board as a list of rows
        for i in range(self.boardheight):
            self.board.append(["[ ]"] * self.boardwidth)

    def mark_board(self, move):
        # Decrement move as list starts at 0
        move -= 1
        board_marked = False
        # [0,0] is top left of the board so we need to loop
        # from bottom to top of the column represented by move
        # Offset by -1 as list starts at 0
        for i in range(self.boardheight -1 , -1, -1):
            if self.board[i][move] == "[ ]" and not board_marked:
                self.board[i][move] = f"[{self.markers[self.turn]}]"
                board_marked = True

        # If we get to the end without marking
        # the column must be full
        if not board_marked:
            self.column_full = True
            col_full_response = json.dumps({"status": "400 COL_FULL"})
            self.connections[self.turn].send(col_full_response.encode())
            logging.info("Column full")

        if self.check_winner():
            # Inform players of result
            logging.info("%s has won!", self.turn)
            win_response = json.dumps({"status": "200 WIN"})
            self.connections[self.turn].send(win_response.encode())
            loss_response = json.dumps({"status": "200 LOSS"})
            self.connections[self.waiting].send(loss_response.encode())
            # TODO exit gracefully
            # sys.exit()

        if self.check_draw():
            # Inform players of result
            logging.info("The game has ended in a draw")
            draw_response = json.dumps({"status": "200 DRAW"})
            self.connections[self.turn].send(draw_response.encode())
            self.connections[self.waiting].send(draw_response.encode())
            # TODO exit gracefully
            # sys.exit()

    def check_winner(self):
        # x is the row number y is the column number

        #check horizontal spaces
        for y in range(self.boardwidth):
            for x in range(self.boardheight - 4):
                if (self.markers[self.turn] in self.board[x][y] and
                        self.markers[self.turn] in self.board[x+1][y] and
                        self.markers[self.turn] in self.board[x+2][y] and
                        self.markers[self.turn] in self.board[x+3][y] and
                        self.markers[self.turn] in self.board[x+4][y]):
                    return True

        #check vertical spaces
        for x in range(self.boardheight):
            for y in range(self.boardwidth - 4):
                if (self.markers[self.turn] in self.board[x][y] and
                        self.markers[self.turn] in self.board[x][y+1] and
                        self.markers[self.turn] in self.board[x][y+2] and
                        self.markers[self.turn] in self.board[x][y+3] and
                        self.markers[self.turn] in self.board[x][y+4]):
                    return True

        # #check / diagonal spaces
        for x in range(self.boardheight - 4):
            for y in range(4, self.boardwidth):
                if (self.markers[self.turn] in self.board[x][y] and
                        self.markers[self.turn] in self.board[x+1][y-1] and
                        self.markers[self.turn] in self.board[x+2][y-2] and
                        self.markers[self.turn] in self.board[x+3][y-3] and
                        self.markers[self.turn] in self.board[x+4][y-4]):
                    return True

        #check \ diagonal spaces
        for x in range(self.boardheight - 4):
            for y in range(self.boardwidth - 4):
                if (self.markers[self.turn] in self.board[x][y] and
                        self.markers[self.turn] in self.board[x+1][y+1] and
                        self.markers[self.turn] in self.board[x+2][y+2] and
                        self.markers[self.turn] in self.board[x+3][y+3] and
                        self.markers[self.turn] in self.board[x+4][y+4]):
                    return True

        return False

    def check_draw(self):
        # Check if the top row is full
        if "[ ]" not in self.board[0]:
            if not self.check_winner():
                return True

    def disconnect_clients(self):
        logging.info("Disconnecting all players")
        for player in self.players:
            # Try tell each player to disconnect and remove them from list
            try:
                self.players.remove(player)
                ready_response = json.dumps({"status": "200 DISC"})
                self.connections[player].send(ready_response.encode())
            except:
                logging.info("Socket for %s already closed", player)
        self.reset_server()

    def run(self):
        self.setup_connection()

        # Main program loop
        while True:
            conn, addr = self.client_socket.accept()
            client_thread = threading.Thread(
                target=self.connect_client,
                args=(conn,)
            )
            client_thread.start()

if __name__ == "__main__":
    Server().run()
