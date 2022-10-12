# CONSTANT CONTROL

## About the Project

The goal of this C2 project is to learn more about Red Teaming tools and how to develop them.

## Prerequisites

The file "config.json" must exist before running the server file. This file tells the script which host to assign to what service and team. 

The service section of the file is used to tell the server which service is running on which host. In a competition environment, the topology is known.

The toplogy section tells the server how many teams exist, what IP and port to host the server on, and the IP format. The key-words, "TEAM", and "HOST", tell the file where it can find this information in the IP.

An example config file is below.

```
{
    "services": [
        {
        "ad":"10",
        "dns":"20",
        "icmp":"30",
        "winrm":"40",
        "rdp":"50",
        "ldap":"60",
        "ssh":"70,80",
        "http":"90,100",
        "ftp":"110"
        }
    ],
    "topology": [
       {
          "teams": "10",
          "serverIP": "127.0.0.1",
          "serverPort": "8080",
          "ipSyntax":"X.X.TEAM.HOST"
       }
    ]
 }
```

## How to Use
The server.py file can be run after the config.json file has been created.

1. Simply run the server.py file with python to start the server on the IP and port specified in the config.
```
python3 server.py
```

The client.py file can be run in the three different ways:
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

## About the Author

Drew Young - Second year CSEC student. This is my first security project and I am having a ton of fun making it! Discord: Youngster#8968