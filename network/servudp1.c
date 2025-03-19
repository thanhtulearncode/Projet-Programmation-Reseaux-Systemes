#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#pragma comment(lib, "Ws2_32.lib")  // Link against Winsock library

#define BUF 512
#define PORT_CLIENT 8083
#define PORT_UDP2 8085

void stop(const char* msg) {
    printf("Error: %s (code %d)\n", msg, WSAGetLastError());
    exit(1);
}

int main() {
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        stop("WSAStartup failed");
    }

    SOCKET client_sockfd, udp2_sockfd;
    int n;
    char buffer[BUF];
    struct sockaddr_in client_addr, udp2_addr;
    int client_len = sizeof(client_addr);
    int udp2_len = sizeof(udp2_addr);

    // Create UDP socket for client
    if ((client_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET)
        stop("Client socket creation failed");

    memset(&client_addr, 0, client_len);
    client_addr.sin_family = AF_INET;
    client_addr.sin_addr.s_addr = INADDR_ANY;
    client_addr.sin_port = htons(PORT_CLIENT);

    if (bind(client_sockfd, (struct sockaddr*)&client_addr, client_len) == SOCKET_ERROR)
        stop("Bind failed for client");

    printf("UDP1 server listening on port %d for client...\n", PORT_CLIENT);

    // Create UDP socket for UDP2
    if ((udp2_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET)
        stop("UDP2 socket creation failed");

    memset(&udp2_addr, 0, udp2_len);
    udp2_addr.sin_family = AF_INET;
    udp2_addr.sin_addr.s_addr = INADDR_ANY;
    udp2_addr.sin_port = htons(PORT_UDP2);

    if (bind(udp2_sockfd, (struct sockaddr*)&udp2_addr, udp2_len) == SOCKET_ERROR)
        stop("Bind failed for UDP2");

    fd_set readfds;
    int max_fd = (client_sockfd > udp2_sockfd) ? client_sockfd : udp2_sockfd;
    
    printf("UDP1 server listening on port %d for UDP2...\n", PORT_UDP2);

    // Receive connection request from UDP2
    memset(buffer, 0, BUF);
    n = recvfrom(udp2_sockfd, buffer, BUF, 0, (struct sockaddr*)&udp2_addr, &udp2_len);
    if (n == SOCKET_ERROR)
        stop("Failed to receive connection request from UDP2");

    printf("Connection request received from UDP2: %s\n", buffer);

    // Send acknowledgment to UDP2
    snprintf(buffer, BUF, "Connection accepted by UDP1");
    if (sendto(udp2_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp2_addr, udp2_len) == SOCKET_ERROR)
        stop("Failed to send acknowledgment to UDP2");

    printf("Connection with UDP2 established.\n");

    // Message handling loop
    while (1) {
        FD_ZERO(&readfds);
        FD_SET(client_sockfd, &readfds);
        FD_SET(udp2_sockfd, &readfds);

        int activity = select(max_fd + 1, &readfds, NULL, NULL, NULL);
        if (activity < 0) {
            stop("Select error");
        }
        // Receive message from client
        if (FD_ISSET(client_sockfd, &readfds)) {
            memset(buffer, 0, BUF);
            n = recvfrom(client_sockfd, buffer, BUF, 0, (struct sockaddr*)&client_addr, &client_len);
            if (n == SOCKET_ERROR) {
                printf("Receive error from client: %d\n", WSAGetLastError());
                continue;
            }
            printf("Message received from client...\n");
            if (sendto(udp2_sockfd, buffer, n, 0, (struct sockaddr*)&udp2_addr, udp2_len) == SOCKET_ERROR) {
                printf("Message send error to UDP2: %d\n", WSAGetLastError());
                continue;
            } else printf("Message successfully sent to UDP2.\n");
        }
        // Receive message from UDP2

        if (FD_ISSET(udp2_sockfd, &readfds)) {
            memset(buffer, 0, BUF);
            n = recvfrom(udp2_sockfd, buffer, BUF, 0, NULL, NULL);
            if (n == SOCKET_ERROR) {
                printf("Receive error from UDP2: %d\n", WSAGetLastError());
                continue;
            } else printf("Message received from UDP2...\n");
            if (sendto(client_sockfd, buffer, n, 0, (struct sockaddr*)&client_addr, client_len) == SOCKET_ERROR) {
                printf("Message send error to client: %d\n", WSAGetLastError());
                continue;
            } else printf("Message successfully sent to client.\n");            
        }
    }

    closesocket(client_sockfd);
    closesocket(udp2_sockfd);
    WSACleanup();
    return 0;
}
