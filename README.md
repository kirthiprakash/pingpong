# PingPong
A basic socket based chat server and client, written in python.


## Features
- Handles new user registrations
- Allows logins from multiple devices. Messages addressed will be delivered to all active connections
- Persists messages addressed to offline users and sends it when they become available
- Checks for duplicate messages

## Architecture

The server is a multi threaded TCP server which can persist connections from client 
and also handle mutiple clients simultaneously.
Each request is processed and the message is stored in database (MongoDB) with message status 'PENDING'. 
A worker ~~process~~ picks up these 'PENDING' messages and routes it to the appropriate user and marks it as 'SENT'

TODO: sharing socket objects between process

## Installation
Make sure MongoDB sever is installed locally and is running at default port 27017

TODO: A config file for all IP address and port

Create a virtual environment and install python packages

    >virtualenv pingpong
    >source pingpong/bin/activate
    >(pingpong) pip install -r requirements.txt

    >cd server
    >python persistent_socket_server.py [HOST [PORT]]
    Listening at: ('locahost', 5555)

## Usage
In an other terminal

    >cd client
    >python socket_test_client.py [HOST [PORT]]
    Welcome to PingPong!
    (PS: use "ls" to list users. use "quit" to exit)
    Please enter your unique name to begin
    tom
    Welcome TOM.
    Usage: @username Hello World!
    ls
    dick, harry
    @harry Hey! How are you?
    
 Harry's terminal
 
     Welcome HARRY
     Usage: @username Hello World!
     ls
     tom, dick
     tom (11/12/16 17:31:04): Hey! How are you?
     @tom whats up?!
     
Tom's terminal

      @dick Hey! How are you?
      dick (11/12/16 17:32:04): whats up?
      
 Messaging an OFFLINE user
 
     @jazz are you there?
     User jazz is OFFLINE. Messages will be delivered once ONLINE

## Data models
3 models are used
### Account
* _id (the username which will be unique)
* last_login
* status (ONLINE, OFFLINE)

### Connection
A mapping between user and their socket/connection information

* username (maps to _id of Account)
* reduced_connection (serialized version of socket object which can be used to get a reference of socket in a different process)
* ip_address (IP address of client)
* port (port address of client

### Message
* _id 
* data
* owner (maps to Account)
* recipient (maps to Account)
* status (PENDING, SENT, DUPLICATE)
* timestamp
