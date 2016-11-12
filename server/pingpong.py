"""
author: kp
date: 11/11/16
"""
import socket
import struct, datetime
from multiprocessing.reduction import reduce_handle, rebuild_handle
from data_store import dao, Collection
from ppong_queue import ppong_message_queue

accounts = {}

QUIT_COMMAND = "quit"
LIST_USERS_COMMAND = "ls"
DUPLICATE_MESSAGE_WINDOW = 5  # in secs


class PingPong(object):
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
                self.list_online_users()
                continue
            if user_given_name == QUIT_COMMAND:
                self.end_connection_and_clean_up()
                return None

            # pick only the 1st word.
            user_given_name = user_given_name.split(" ")[0]
            account = dao.findOne(Collection.Account.name, params={"_id": user_given_name})

            # New registration
            if not account:
                # Insert New Account
                dao.insertOne(Collection.Account.name,
                              params={"_id": user_given_name, "last_login": datetime.datetime.now(),
                                      "status": Collection.Account.STATUS_ONLINE})
            else:
                dao.update(Collection.Account.name, params={"_id": user_given_name},
                           set_params={"status": Collection.Account.STATUS_ONLINE,
                                       "last_login": datetime.datetime.now()})

            # User already exists, add new connection if not already present (To support login from multiple devices)
            ip_address, port = self.connection.getpeername()
            existing_connection = dao.findOne(Collection.Connection.name,
                                              params={"username": user_given_name, "ip_address": ip_address,
                                                      "port": port})
            if not existing_connection:
                # TODO: Use these reduced connection objects in a different worker process to route messages
                reduced_connection = reduce_handle(self.connection.fileno())
                dao.insertOne(Collection.Connection.name,
                              params={"username": user_given_name, "reduced_connection": reduced_connection,
                                      "ip_address": ip_address, "port": port})

            self.name = user_given_name
            break

        self.send_message(
                'Welcome {}\n Usage: @username Hello World!'.format(self.name.upper()))

        # mapping connection and username in memory for some send quick prompt messages
        ip_address, port = self.connection.getpeername()
        self.name_and_address = "{}__{}__{}".format(self.name, ip_address, port)
        accounts[self.name_and_address] = self.connection
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

        pending_messages = dao.find(Collection.Message.name,
                                    params={"recipient": username, "status": Collection.Message.STATUS_PENDING})
        for pending_message in pending_messages:
            self.route_message(pending_message.get("_id"))

        # If authentication is success, keep monitoring the connection
        while username and True:
            data = self.recv_all()
            if data == LIST_USERS_COMMAND:
                self.list_online_users()
            elif data == QUIT_COMMAND:
                print "Got QUIT command from: {}".format(self.name)
                break
            else:
                recipient_name_str = data.split(" ")[0]
                recipient_message = " ".join(data.split(" ")[1:])
                if recipient_name_str.startswith("@"):
                    recipient_name = recipient_name_str[1:]
                    recipient_name = recipient_name.strip() if recipient_name else recipient_name
                    time_of_message = datetime.datetime.now()
                    message_id = dao.insertOne(Collection.Message.name,
                                               {"status": Collection.Message.STATUS_PENDING, "data": recipient_message,
                                                "owner": self.name, "recipient": recipient_name,
                                                "timestamp": time_of_message})

                    self.route_message(message_id)
                else:
                    self.send_message("Invalid message. Usage: @username Hello World!")

        self.end_connection_and_clean_up()

    def list_online_users(self):
        online_users_cur = dao.find(Collection.Account.name,
                                    params={"status": Collection.Account.STATUS_ONLINE,
                                            "_id": {"$ne": self.name}})
        online_users = list(online_users_cur)
        self.send_message(", ".join([el.get("_id") for el in online_users[-10:]]))

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
        if user_connections.count() < 1:
            dao.update(Collection.Account.name, params={"_id": self.name},
                       set_params={"status": Collection.Account.STATUS_OFFLINE})

        connection = accounts.pop(self.name_and_address)
        connection.shutdown(socket.SHUT_RDWR)
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

    def route_message(self, message_id):
        message = dao.findOne(Collection.Message.name, params={"_id": message_id})

        # duplicate check
        t_minus_dup_window = message.get("timestamp") - datetime.timedelta(seconds=DUPLICATE_MESSAGE_WINDOW)
        prev_messages = dao.find(Collection.Message.name,
                                 params={"data": message.get("data"), "recipient": message.get("recipient"),
                                         "timestamp": {"$gt": t_minus_dup_window}, "_id": {"$ne": message.get('_id')}})
        if prev_messages.count() > 0:
            dao.update(Collection.Message.name, params={"_id": message.get("_id")},
                       set_params={"status": Collection.Message.STATUS_DUPLICATE})
            return

        recipient_name = message.get('recipient')
        recipient_data = message.get("data")
        recipient_account = dao.findOne(Collection.Account.name,
                                        params={"_id": recipient_name})
        if not recipient_account:
            self.send_message("No such user found: {}".format(recipient_name))
        elif Collection.Account.STATUS_ONLINE == recipient_account.get("status"):
            connections = dao.find(Collection.Connection.name, params={"username": recipient_name})
            for connection in connections:
                ip_address = connection.get("ip_address")
                port = connection.get("port")
                connection_key = "{}__{}__{}".format(recipient_name, ip_address, port)
                recipient_connection = accounts.get(connection_key)
                if recipient_connection:
                    recipient_message = "{} ({}): {}".format(message.get("owner"),
                                                             message.get('timestamp').strftime("%x %X"), recipient_data)
                    self.send_message(recipient_message, connection=recipient_connection)
                else:
                    print "Recipient connection not found:{}; connections:{}".format(connection_key, accounts)
            if connections.count() > 0:
                dao.update(Collection.Message.name, params={"_id": message_id},
                           set_params={"status": Collection.Message.STATUS_SENT})
                if self.name != recipient_name:
                    self.send_message("Message sent to {}".format(recipient_name))
            else:
                self.send_message("Messages are delayed")
        else:
            self.send_message("User {} is {}. Messages will be delivered once {}".format(recipient_name,
                                                                                         recipient_account.get(
                                                                                                 "status"),
                                                                                         Collection.Account.STATUS_ONLINE))
