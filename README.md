# C2-Project

## About the Project

The goal of this project is to learn more about Red Teaming tools and how to develop them.

## How to Use
The server.py file can be run in three ways:

1. Simply run the server.py file with python to start the server on the default IP and port. (127.0.0.1:8080)
```
python3 server.py
```
2. Run the server.py file and specify an IP address to run on. This is helpful for someone who doesn't want to edit the file every time they run the server. This will start the server on the specified IP with port 8080.
```
python3 server.py {IP ADDRESS}
```
3. Run the server.py file and specify an IP address and port to run on.
```
python3 server.py {IP ADDRESS} {PORT}
```

The client.py file can be run in the same three ways:
1. Simply run the client.py file with python to connect to the server on the default IP and port. (127.0.0.1:8080)
```
python3 client.py
```
2. Run the client.py file and specify an IP address to connect to. This is helpful for someone who doesn't want to edit the file every time they run the server. This will connect to the server on the specified IP with port 8080.
```
python3 client.py {IP ADDRESS}
```
3. Run the client.py file and specify an IP address and port to connect to.
```
python3 client.py {IP ADDRESS} {PORT}
```

Once you are in the server, you will be greeted with a message that tells you what IP and port the server is running on. Type 'help' for a list of possible commands.

```
Help Menu:
    Use 'list' to list active connections.
    Use 'select' to choose a client from the list.
    Use 'help' to show this menu.
    Use 'exit' to quit the program.
```

## About the Author

Drew Young - First year CSEC student. This is my first security project and I am having a ton of fun making it! Discord: Youngster#8968