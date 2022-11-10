import threading
import time

class Hostname:
    def __init__(self,hostname, ipFormat, TEAMS_INT):
        self.clients = list()
        self.hostname = hostname
        self.ipFormat = ipFormat
        self.expectedIPs = set()
        for i in range(TEAMS_INT): #for the amount of teams
            tempIP = self.ipFormat
            self.expectedIPs.add(tempIP.replace("TEAM",str(i))) #add all expected IP's to a list
    
    def addClient(self,client):
        if client.IP in self.expectedIPs:
            self.clients.append(client)
            client.setHost(self)
    
    def removeClient(self,client):
        self.clients.remove(client)
        client.setHost(None)
    
    def listHosts(self):
        print(f"{self.hostname} ({self.ipFormat}):")
        for client in self.clients:
            if client.isUp():
                print("  >>" + str(client.IP))
            else:
                continue
    
    def sendToAll(self,command):
        for client in self.clients:
            try:
                client.send(command)
                print("Successfully sent command to: " + str(client.IP))
                resp = threading.Thread(target=client.receiveResp)
                resp.start() #server needs to receive response or it will just hang
            except:
                print("Failed to send command to client: " + str(client.getAddr()))
        print("Command sent to " + str(len(self.clients)) + " clients.")
        time.sleep(.2 * len(self.clients)) #wait .2 seconds for each client 

    def __str__(self) -> str:
        return self.hostname