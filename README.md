# 5-in-a-row
Connect 5 game that supports client server interactions


## How to Run

All commands listed below should be run in the root of the project directory (this folder)

### Run the server

Simply run:
```
python server.py
```
to start the server. This will set up the server and start listening on 127.0.0.1:1337 for client connections

If you would lke to enable logging set the LOGLEVEL environment variable.

### Run the client

Once the server is running you can run the client in abother terminal to connect to the server over http. Simply run:
```
python client.py
```
You will be prompted to enter your username and then the server will try to start a game if it has two players connected.

### Run tests

To run the tests just run:
```
pip install -r requirements.txt
```
To make sure you have all dependencies installed. Then run:
```
python -m pytest
```
To run the tests. pytest will detext and run all tests in the project.
