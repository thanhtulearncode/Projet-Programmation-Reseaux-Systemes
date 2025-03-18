import socket
import os

BUF = 512
SERVER_IP = "127.0.0.1"
SERVER_PORT = 8083  

def send_file(client_socket, file_path, server_address):
    try:
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(BUF)
                if not data:
                    break
                client_socket.sendto(data, server_address)
        print(f"Tệp '{file_path}' đã được gửi thành công.")
    except Exception as e:
        print(f"Không thể gửi tệp: {e}")

def main():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("Client UDP đã sẵn sàng. Bạn có thể gửi tin nhắn hoặc tệp.")
    except socket.error as e:
        print(f"Erreur lors de la création du socket : {e}")
        exit(1)

    while True:
        print("\nLựa chọn:")
        print("1. Gửi tin nhắn")
        print("2. Gửi tệp")
        print("3. Thoát")
        choice = input("Chọn 1, 2 hoặc 3: ")

        if choice == '1':
            message = input("Nhập tin nhắn để gửi: ")
            if message.lower() == "exit":
                print("Đóng kết nối...")
                break
            client_socket.sendto(message.encode(), (SERVER_IP, SERVER_PORT))
            print(f"Tin nhắn gửi tới Server UDP1: {message}")
            try:
                client_socket.settimeout(2)  # Timeout 2s để tránh block
                response, _ = client_socket.recvfrom(BUF)
                print(f"Phản hồi từ Server UDP1: {response.decode()}")
            except socket.timeout:
                print("Không nhận được phản hồi từ Server UDP1.")
        
        elif choice == '2':
            file_path = input("Nhập đường dẫn tệp văn bản để gửi: ")
            if os.path.isfile(file_path):
                client_socket.sendto(b"FILE", (SERVER_IP, SERVER_PORT))  # Gửi tín hiệu gửi tệp
                send_file(client_socket, file_path, (SERVER_IP, SERVER_PORT))
            else:
                print("Tệp không tồn tại. Thử lại.")
        
        elif choice == '3':
            print("Đóng kết nối...")
            break
        else:
            print("Lựa chọn không hợp lệ. Vui lòng thử lại.")
    
    client_socket.close()

if __name__ == "__main__":
    main()
