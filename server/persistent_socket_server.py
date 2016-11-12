"""
author: kp
date: 11/11/16
"""
import SocketServer
import socket
from pingpong import PingPong
from server.data_store import dao, Collection


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
    HOST, PORT = "192.168.1.33", 5555
    SERVER_ADDRESS = (HOST, PORT)
    try:
        server = ThreadedTCPServer(SERVER_ADDRESS, MyTCPHandler)
    except socket.error as e:
        print "Failed to bind: {}".format(SERVER_ADDRESS)

    print "Listening at: {}".format(SERVER_ADDRESS)

    # Clean up previous connections (hanged). start fresh.
    dao.delete(Collection.Connection.name)

    server.serve_forever()
