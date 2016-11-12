"""
author: kp
date: 11/11/16
"""
import SocketServer
import socket

import sys

from pingpong import PingPong
from data_store import dao, Collection


class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler
    """

    def handle(self):
        print "New Connection from: {}".format(self.request.getpeername())
        pp = PingPong(self.request)
        pp.process()  # blocking call
        print "Done Processing"


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":

    # Default
    HOST, PORT = "localhost", 5555
    if len(sys.argv) >= 2:
        HOST = sys.argv[1]
        PORT = int(sys.argv[2])

    SERVER_ADDRESS = (HOST, PORT)
    try:
        server = ThreadedTCPServer(SERVER_ADDRESS, MyTCPHandler)
    except socket.error as e:
        print "Failed to bind: {}".format(SERVER_ADDRESS)
        sys.exit(0)

    print "Listening at: {}".format(SERVER_ADDRESS)

    # Clean up previous connections (hanged). start fresh.
    dao.delete(Collection.Connection.name)

    server.serve_forever()
