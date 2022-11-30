import json
import threading
import time

class Service():
    def __init__(self, name):
        self.name = name
        self.clients = []
        self.identifier = list()
        self.cloudIdentifier = list() #Identifiers are IP's with placeholders for team number
        self.breaks = dict()
        self.expectedClients = list()
    
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
                            client.send(self.breaks[selected])
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
                        client.send(userIn)
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
                    pass
            except:
                pass

    def assign(self, client):
        self.clients.append(client) #Append the client to the clients list