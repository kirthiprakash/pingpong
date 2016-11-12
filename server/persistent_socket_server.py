"""
author: kp
date: 11/11/16
"""
import SocketServer
import socket
from pingpong import PingPong


class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The request handler
    """

    # def handle(self):
    #     """
    #     Activate this implementation for performing testing.
    #     :return:
    #     """
    #     self.request.sendall("HTTP/1.0 200 OK\r\nContent-Length: 5\r\n\r\nPong!\r\n");
    #     self.request.close()

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
    # Create the server, binding to host
    try:
        server = ThreadedTCPServer(SERVER_ADDRESS, MyTCPHandler)
    except socket.error as e:
        PORT = 5556
        SERVER_ADDRESS = (HOST, PORT)
        server = SocketServer.TCPServer(SERVER_ADDRESS, MyTCPHandler)

    print "Listening at: {}".format(SERVER_ADDRESS)
    # Run server
    server.serve_forever()
