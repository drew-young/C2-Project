#Run this script to install dependencies, pipe to dev/null to disable output



#Make script not need sudo acccess. Maybe clone the repo then use the setup.py script?
sudo apt install python3-pip -y > /dev/null

pip install pynput > /dev/null

python3 -m pip install pynput > /dev/null
