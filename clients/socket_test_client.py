"""
author: kp
date: 11/11/16
"""
import socket
import sys
import struct
from threading import Thread

server_address = ('192.168.1.33', 5555)

# Create a TCP/IP socket
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
print >> sys.stderr, 'connecting to %s port %s' % server_address
try:
    connection.connect(server_address)
except socket.error:
    server_address = ('192.168.1.33', 5556)
    print >> sys.stderr, 'connecting to %s port %s' % server_address
    connection.connect(server_address)

# connection.settimeout(5)

# Send messages on both sockets
# for s in socks:
#     formated_msg = struct.pack(">I", len(message)) + message
#     print >> sys.stderr, '{}: sending {}'.format(s.getsockname(), formated_msg)
#     s.sendall(formated_msg)

# Read responses on both sockets

running = True


def receive_data_from_server():
    global running
    while True:
        raw_msg_len = connection.recv(4)
        if not raw_msg_len:
            connection.close()
            running = False
            print "Connection closed"
            break
        if raw_msg_len:
            try:
                msg_len = struct.unpack('>I', raw_msg_len)[0]
            except Exception as e:
                print e
                print "Bad message format: {}".format(raw_msg_len)
                continue
            data = connection.recv(msg_len)
            print data
        else:
            print "Bad message format: {}".format(raw_msg_len)


Thread(target=receive_data_from_server).start()
while running:
    user_input = raw_input(">")
    if user_input:
        send_data = struct.pack('>I', len(user_input)) + user_input
        connection.sendall(send_data)
