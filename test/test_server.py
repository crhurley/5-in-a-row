import pytest
from server import Server

def test_add_players():
    server = Server()

    # Add first player
    server.add_player("Alice")
    assert server.players == ['Alice']

    # Add second player
    server.add_player("Bob")
    assert server.players == ['Alice', 'Bob']

    # Server should not allow more than two players
    server.add_player("Charlie")
    assert server.players == ['Alice', 'Bob']
