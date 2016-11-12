# PingPong
A basic socket based chat server and client, written in python.


## Features
- Handles new user registrations
- Persists messages addressed to offline users and sends it when they become available
- Checks for duplicate messages

## Architecture

The server is a multi threaded TCP server which can persist connections from client 
and also handle mutiple clients simultaneously.
Each request is processed and the message is stored in database (MongoDB) with message status 'PENDING'
A worker ~~process~~ picks up these 'PENDING' messages and routes it to the appropriate user and marks is as 'SENT'

TODO: sharing socket objects between process

## Installation
    >cd server
    >python persistent_socket_server.py
    Listening at: ('locahost', 5555)

## Usage
In an other terminal

    >cd client
    >python socket_test_client.py
    Welcome to PingPong!
    (PS: use "ls" to list users. use "quit" to exit)
    Please enter your unique name to begin
    tom
    Welcome TOM.
    Usage: @username Hello World!
    ls
    dick, harry
    @tom Hey!
    
 Harry's terminal
 
     Welcome HARRY
     Usage: @username Hello World!
     ls
     tom, dick
     tom (11/12/16 17:31:04): Hey!
     @tom whats up?!
     
Tom's terminal

      @tom Hey!
      dick (11/12/16 17:32:04): whats up?
      
 Messaging an OFFLINE user
 
     @jazz are you there?
     User jazz is OFFLINE. Messages will be delivered once ONLINE
