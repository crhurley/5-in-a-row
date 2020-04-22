import socket
import json
import logging
import os
import sys

# Set log level to environment variable LOGLEVEL
# or default to ERROR
logging.basicConfig(level=os.environ.get("LOGLEVEL", "ERROR"))

# Setup connection parameters
host='127.0.0.1'
port=1337

#Create server socket object
try:
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logging.info("Server socket connected")
except socket.error:
    logging.error("Could not create server socket")

# Allow socket to be reused for testing
serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#Bind to specified port
try:
    serv.bind((host,port))
    logging.info("Successfully binded to host %s at port %s", host, port)
except socket.error:
    logging.error("Failed to bind to host %s at port %s", host, port)
    sys.exit()

serv.listen(5)
logging.info("Listening")


#Keeps track of players currently in the server
players=[]

#Main connection loop. Handles all messages from client
while True:
    conn, addr = serv.accept()
    while True:
        data = conn.recv(4096).decode()
        logging.info("Received data: %s", data)

        if not data:
            logging.info("Empty message received")
            break

        data = json.loads(data)
        # Add a new player
        if "new_player" in data.keys():
            logging.info("Current players: %s", players)
            logging.info(" len(players): %s", len(players))
            player = data["new_player"]
            if len(players) < 2:
                players.append(player)
                logging.info("New player %s added", player)
                server_response = "Welcome to the game " + player
                conn.send(server_response.encode())
            else:
                server_response = "Sorry, we already have two players " + player
                conn.send(server_response.encode())

    conn.close()
    print('client disconnected')
