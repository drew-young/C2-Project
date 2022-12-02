class Team():
    def __init__(self, identity):
        self.identity = identity
        self.clients = []
        self.expectedHosts = list() #Set of expected hosts
    
    def assign(self, client):
        self.clients.append(client) #Append the client to the clients list

    def unassign(self, client):
        try: #try to remove the client since this might be called twice
            self.clients.remove(client) #Append the client to the clients list
        except: pass

    def listClients(self):
        print("> Team " + self.identity + ":")
        for client in self.clients:
            if client.isUp():
                print("    >> " + client.IP)
    
    def listExpectedClients(self):
        print("> Team " + self.identity + ":")
        for host in self.expectedHosts: #for each expected host
            printed = False
            for client in self.clients: #see if active clients match
                if host == client.IP: #if the host matches the IP
                    if client.isUp(): #if the client is up
                        print("    >> " + host) #print the host if all is true
                        printed = True
            if not printed:
                print("    >> " + host + " [X]") #print the host if it's down
    
    def isExpectedHost(self,IP):
        return True if IP in self.expectedHosts else False