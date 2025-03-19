#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#define BUF 512
#define PORT_UDP2 "8085"
#define PORT_CLIENT "8087"
#define FILE_DIR "./received_files/"  // Thư mục lưu trữ tệp

void stop(char* msg) {
    perror(msg);
    exit(1);
}

void save_file(int sockfd, struct sockaddr_in *udp1_addr, socklen_t udp1_len) {
    char buffer[BUF];
    int n, file_fd;
    char filename[100];
    sprintf(filename, "%sreceived_file_from_udp2.txt", FILE_DIR);

    // Mở tệp để ghi
    file_fd = open(filename, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (file_fd < 0) {
        stop("Erreur d'ouverture du fichier");
    }
    printf("Tệp sẽ được lưu tại %s\n", filename);

    // Nhận tệp từ client
    while (1) {
        memset(buffer, 0, BUF);
        n = recvfrom(sockfd, buffer, BUF, 0, (struct sockaddr*)udp1_addr, &udp1_len);
        if (n <= 0) break;  // Kết thúc khi không còn dữ liệu

        write(file_fd, buffer, n);
    }
    
    snprintf(buffer, BUF, "Le fichier reçu et traité par UDP2");
    if (sendto(sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp1_addr, udp1_len) < 0)
        perror("Erreur d'envoi de la réponse à UDP1");
    printf("Tệp đã được lưu thành công.\n");
    close(file_fd);
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <UDP1 IP>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        stop("WSAStartup failed");
    }

    SOCKET udp1_sockfd, client_sockfd;
    int n;
    char buffer[BUF];
    struct sockaddr_in udp1_addr, client_addr;
    struct addrinfo hints, *udp1_info;
    int udp1_len = sizeof(udp1_addr);
    int client_len = sizeof(client_addr);


    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET;
    hints.ai_socktype = SOCK_DGRAM;
    hints.ai_protocol = IPPROTO_UDP;

    if (getaddrinfo(argv[1], PORT_UDP2, &hints, &udp1_info) != 0) {
        stop("Error setting server UDP1 address");
    }

    // Create UDP socket
    if ((udp1_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        stop("Socket UDP creation failed");
    }
    if ((client_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        stop("Socket client creation failed");
    }
    memset(&udp1_addr, 0, sizeof(udp1_addr));
    memcpy(&udp1_addr, udp1_info->ai_addr, sizeof(struct sockaddr_in));
    freeaddrinfo(udp1_info);

    memset(&client_addr, 0, sizeof(client_addr));
    client_addr.sin_family = AF_INET;
    client_addr.sin_addr.s_addr = INADDR_ANY;
    client_addr.sin_port = htons(atoi(PORT_CLIENT));

    if (bind(client_sockfd, (struct sockaddr*)&client_addr, client_len) == SOCKET_ERROR) {
        stop("Bind failed for client");
    }

    // Send connection request to UDP1
    snprintf(buffer, BUF, "Connection request from UDP2");
    printf("Sending connection request to UDP1...\n");

    if (sendto(udp1_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp1_addr, udp1_len) == SOCKET_ERROR) {
        stop("Error sending connection request to UDP1");
    }

    printf("Connection request sent to UDP1.\n");

    fd_set readfds;
    int max_fd = (client_sockfd > udp1_sockfd) ? client_sockfd : udp1_sockfd;

    while (1) {
        FD_ZERO(&readfds);
        FD_SET(client_sockfd, &readfds);
        FD_SET(udp1_sockfd, &readfds);

        if (select(max_fd + 1, &readfds, NULL, NULL, NULL) == SOCKET_ERROR) {
            stop("Select error");
        }
        // Receive message from client
        if (FD_ISSET(client_sockfd, &readfds)) {
            memset(buffer, 0, BUF);
            n = recvfrom(client_sockfd, buffer, BUF, 0, (struct sockaddr*)&client_addr, &client_len);
            if (n == SOCKET_ERROR) {
                printf("Receive error: %d\n", WSAGetLastError());
                continue;
            } else printf("Message received from client: %s\n", buffer);
            if (sendto(udp1_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp1_addr, udp1_len) == SOCKET_ERROR) {
                printf("Send error: %d\n", WSAGetLastError());
                continue;
            } else printf("Message successfully sent to UDP1.\n");
        }
        // Receive message from UDP1
        if (FD_ISSET(udp1_sockfd, &readfds)) {
            memset(buffer, 0, BUF);
            n = recvfrom(udp1_sockfd, buffer, BUF, 0, (struct sockaddr*)&udp1_addr, &udp1_len);
            if (n == SOCKET_ERROR) {
                printf("Receive error: %d\n", WSAGetLastError());
                continue;
            } else printf("Message received from UDP1: %s\n", buffer);
            if (sendto(client_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&client_addr, client_len) == SOCKET_ERROR) {
                printf("Send error: %d\n", WSAGetLastError());
                continue;
            } else printf("Message successfully sent to client.\n");
        }
    }
    closesocket(udp1_sockfd);
    closesocket(client_sockfd);
    WSACleanup();
    return 0;
}