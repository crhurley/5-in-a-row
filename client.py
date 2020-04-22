import socket
import json
import logging
import os
import sys

# Set log level to environment variable LOGLEVEL
# or default to INFO
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

# Setup connection parameters
host='127.0.0.1'
port=1337

# Prompt client for username
username = input("Please enter your username: ")
while not username.isalpha():
    print("Only letters are allowed in your username")
    username = input("Please enter your username: ")

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
client_message = json.dumps({"new_player": username})
client.send(client_message.encode())
logging.info("User %s sent to server", username)

# Get response from server
from_server = client.recv(4096)
print(from_server.decode())

# Close the socket
client.close()
