"""
author: kp
date: 11/11/16
"""
import struct, datetime
from multiprocessing.reduction import reduce_handle

from data_store import dao, Collection

accounts = {}

QUIT_COMMAND = "quit"
LIST_USERS_COMMAND = "ls"


class PingPong():
    def __init__(self, connection):
        self.connection = connection
        self.address = connection.getsockname()
        self.name = ""

    def authenticate(self):
        """
        For the initial phase, this method gets an unique identifier from the user and uses it to map connections
        TODO: Introduce password based authentication system
        :return: Username => str
        """
        self.send_message("Please enter your unique name to begin")
        while True:
            user_given_name = self.get_name()
            if user_given_name == LIST_USERS_COMMAND:
                self.send_message(", ".join(accounts.keys()[-10:]))
                continue
            if user_given_name == QUIT_COMMAND:
                self.end_connection_and_clean_up()
                return None

            account = dao.findOne(Collection.Account.name, params={"_id": user_given_name})

            # New registration
            if not account:
                # Insert New Account
                dao.insertOne(Collection.Account.name,
                              params={"_id": user_given_name, "last_login": datetime.datetime.now(),
                                      "status": Collection.Account.STATUS_ONLINE})

            # User already exists, add new connection if not already present (To support login from multiple devices)
            ip_address, port = self.connection.getpeername()
            existing_connection = dao.findOne(Collection.Connection.name,
                                              params={"username": user_given_name, "ip_address": ip_address,
                                                      "port": port})
            if not existing_connection:
                reduced_connection = ()
                # reduced_connection = reduce_handle(self.connection.fileno())
                dao.insertOne(Collection.Connection.name,
                              params={"username": user_given_name, "reduced_connection": reduced_connection,
                                      "ip_address": ip_address, "port": port})

            self.name = user_given_name
            break

        self.send_message(
                'Logged in successfully. Usage: @username Hello World!\n(PS: use "{}" to list users. use "{}" to exit)'.format(
                        LIST_USERS_COMMAND, QUIT_COMMAND))

        # mapping connection and username in memory for some send quick prompt messages
        accounts[self.name] = self.connection
        return self.name

    def process(self):
        """
        The main blocking method for each new connection. Firsts authenticates the user and keeps monitoring the
        connection until quit command is issued by the user
        :return: None
        """

        self.send_message(
                'Welcome to PingPong!\n(PS: use "{}" to list users. use "{}" to exit)'.format(LIST_USERS_COMMAND,
                                                                                              QUIT_COMMAND))

        username = self.authenticate()

        # If authentication is success, keep monitoring the connection
        while username and True:
            data = self.recv_all()
            if data == LIST_USERS_COMMAND:
                self.send_message(", ".join(accounts.keys()[-10:]))
            elif data == QUIT_COMMAND:
                print "GOT QUIT command from: {}".format(self.name)
                break
            else:
                recipient_name_str = data.split(" ")[0]
                recipient_message = " ".join(data.split(" ")[1:])
                if "@" in recipient_name_str:
                    recipient_name = recipient_name_str[1:]
                    recipient_name = recipient_name.strip() if recipient_name else recipient_name
                    if recipient_name in accounts:
                        recipient_connection = accounts[recipient_name]
                        recipient_data = "{}:{}".format(self.name, recipient_message)
                        self.send_message(recipient_data, connection=recipient_connection)
                        self.send_message("SENT to {}".format(recipient_name_str))
                    else:
                        self.send_message("User {} not found".format(recipient_name_str))
                else:
                    self.send_message("Invalid message. Usage: @username Hello World!")

        self.end_connection_and_clean_up()

    def end_connection_and_clean_up(self):
        """
        #Closes socket connection and releases the username and connection mapping
        :return: None
        """
        print "Ending connection for {}".format(self.name)

        # delete the particular connection for this user
        ip_address, port = self.connection.getpeername()
        dao.delete(Collection.Connection.name, params={'username': self.name, "ip_address": ip_address, "port": port})

        # Mark user as inactive if there aren't any sockets active for this user
        user_connections = dao.find(Collection.Connection.name, params={"username": self.name})
        if not user_connections:
            dao.update(Collection.Account.name, params={"_id": self.name},
                       set_params={"status": Collection.Account.STATUS_OFFLINE})

        connection = accounts.pop(self.name)
        connection.close()
        print "Remaining connections: {}".format(accounts.keys())

    def send_message(self, message, connection=False):
        """
        Formats the message by pre-pending the message length and writes to the connection
        :param message:
        :param connection: optional. If not passed, uses current connection
        :return: None
        """
        send_data = struct.pack('>I', len(message)) + message
        if connection:
            connection.sendall(send_data)
        else:
            self.connection.sendall(send_data)

    def get_name(self):
        name = self.recv_all()
        return name

    def recv_all(self):
        """
        Reads the entire data from the socket assuming the 1st 4 bytes will describe the message length
        :return: data from the current socket => str
        """
        raw_msglen = self.connection.recv(4)
        if not raw_msglen:
            return None
        msg_len = struct.unpack('>I', raw_msglen)[0]
        data = self.connection.recv(msg_len)
        return data
