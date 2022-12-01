import socket

class Connection:
    def __init__(self, addr, socket, IP, BUFFER_SIZE):
        self.socket = socket
        self.IP = IP
        self.addr = addr
        self.port = addr[1]
        self.BUFFER_SIZE = BUFFER_SIZE
        self.connected = True
        self.hostname = None

    def getHostname(self):
        return self.hostname

    def getSocket(self):
        return self.socket
    
    def getAddr(self):
        return self.addr

    def setIP(self, IP):
        self.IP = IP

    def sendCommand(self,command): 
        try:
            self.socket.send(str(command).encode())
        except:
            print("[FAILURE] Command " + command + " could not be sent to " + self.IP)
    
    def send(self,command): 
        try:
            self.socket.send(str(command).encode())
        except:
            print("[FAILURE] Command ''" + command + "'' could not be sent to: " + self.IP)

    def receiveResp(self):
        try:
            print("\tClient (" + str(self.IP) + ") response: '" + str(self.socket.recv(self.BUFFER_SIZE).decode()).strip() + "'")
            return 
        except:
            print("[FAILURE] Response failed from: " + self.IP)

    def getResponse(self):
        try:
            self.socket.settimeout(1.5) #timeout after 3 seconds of no recv
            serv_resp = self.socket.recv(self.BUFFER_SIZE).decode()
            self.socket.settimeout(None) #reset timeout
            return serv_resp
        except socket.timeout as e:
            print("Process did not return anything. \n")
        
    def recv(self):
        try:
            self.socket.settimeout(3.0) #timeout after 3 seconds of no recv
            serv_resp = self.socket.recv(self.BUFFER_SIZE).decode()
            self.socket.settimeout(None) #reset timeout
            return serv_resp
        except socket.timeout as e:
            print("Process did not return anything. \n" + str(e))
    
    def isUp(self):
        return self.connected

    #returns true if client is up
    def isUpCheck(self):
        try:
            self.socket.send("beacon_ping".encode())
            if self.socket.recv(self.BUFFER_SIZE).decode() == "beacon_pong": #send ping and if the response doesn't exist, it's not up
                self.connected = True
                return True
            self.connected = False
            return False
        except:
            self.connected = False
            return False
    
    def getIP(self):
        return self.IP
    
    def getIpFromClient(self):
        self.socket.send("getIP".encode())
        self.IP = self.socket.recv(self.BUFFER_SIZE).decode()
        return self.IP