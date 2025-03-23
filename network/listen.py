import socket
import sys
import select

SERVER_IP="127.0.0.1"
BUF = 1024
def main():
    server_port = int(sys.argv[1])
    
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except:
        print("Failed to create server socket")
        server_socket.close()
        sys.exit()
    
    message = "Hello from listener"
    server_socket.sendto(message.encode(), (SERVER_IP, server_port))
        
    while True:
        ready = select.select([server_socket], [], [], 0)
        if ready[0]:
            data, addr = server_socket.recvfrom(BUF)
            print("Received message from server")
            print(data.decode())

    
if __name__ == "__main__":
    main()