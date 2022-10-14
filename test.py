import subprocess
import re

regex = re.compile(r'(10\.\d{1,2}\.\d{1,3}\.\d{1,3})')

IP = subprocess.run("ifconfig | grep inet", shell=True,stdout=subprocess.PIPE)
IP = str(IP)

X = regex.search(IP)[0]


print(X)