#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#define BUF 12000



void stop(char* msg) {
    printf("Error: %s (code %d)\n", msg, WSAGetLastError());
    exit(1);
}

BOOL CtrlHandler(DWORD fdwCtrlType) {
    // Check the type of control event
    switch (fdwCtrlType) {
        case CTRL_C_EVENT:
            printf("\nCtrl+C detected, cleaning up and exiting...\n");
            WSACleanup(); // Cleanup Winsock
            exit(0);      // Exit the program
            return TRUE;  // Indicate successful handling

        // Other control events can be added here if needed
        default:
            return FALSE;
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <ID>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    // Set console control handler to handle Ctrl+C
    if (!SetConsoleCtrlHandler((PHANDLER_ROUTINE)CtrlHandler, TRUE)) {
        stop("SetConsoleCtrlHandler failed");
    }

    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        stop("WSAStartup failed");
    }
    
    SOCKET udp_sockfd, client_sockfd;
    int n;
    char buffer[BUF];
    struct sockaddr_in udp_addr, client_addr, broadcast_addr, local_addr;
    int udp_len = sizeof(udp_addr);
    int client_len = sizeof(client_addr);
    int broadcast_len = sizeof(broadcast_addr);
    int local_len = sizeof(local_addr);
    int client_port = 8080 + atoi(argv[1]);
    int udp_port = 8090 + atoi(argv[1]);

    // Create UDP socket
    if ((udp_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        stop("Socket UDP creation failed");
    }
    char *enable = "65535";
    if (setsockopt(udp_sockfd, SOL_SOCKET, SO_BROADCAST, enable, sizeof(enable)) < 0) 
        stop("Failed to enable broadcast");

    // Create client socket
    if ((client_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        stop("Socket client creation failed");
    }

    // Bind udp socket to port
    memset(&udp_addr, 0, sizeof(udp_addr));
    udp_addr.sin_family = AF_INET;
    udp_addr.sin_addr.s_addr = INADDR_ANY;
    udp_addr.sin_port = htons(udp_port);
    if (bind(udp_sockfd, (struct sockaddr*)&udp_addr, udp_len) == SOCKET_ERROR) {
        stop("Bind failed for UDP");
    }
    
    // Bind client socket to port
    memset(&client_addr, 0, sizeof(client_addr));
    client_addr.sin_family = AF_INET;
    client_addr.sin_addr.s_addr = INADDR_ANY;
    client_addr.sin_port = htons(client_port);
    if (bind(client_sockfd, (struct sockaddr*)&client_addr, client_len) == SOCKET_ERROR) {
        stop("Bind failed for client");
    }

    // Get local IP address 
    getsockname(udp_sockfd, (struct sockaddr*)&local_addr, &local_len);
    printf("Local IP address: %s\n", inet_ntoa(local_addr.sin_addr));

    // Set broadcast address
    memset(&broadcast_addr, 0, sizeof(broadcast_addr));
    broadcast_addr.sin_family = AF_INET;
    broadcast_addr.sin_addr.s_addr = inet_addr("255.255.255.255");
    broadcast_addr.sin_port = htons(udp_port);

    // Send broadcast message to UDP1
    snprintf(buffer, BUF, "Broadcast message");
    for (int i = 8090; i < 8099; i++) {
        broadcast_addr.sin_port = htons(i);
        if (sendto(udp_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&broadcast_addr, broadcast_len) == SOCKET_ERROR) {
            stop("Send broadcast message failed");
        }
    }
    
    
    fd_set readfds;
    int max_fd = (client_sockfd > udp_sockfd) ? client_sockfd : udp_sockfd;

    while (1) {
        FD_ZERO(&readfds);
        FD_SET(client_sockfd, &readfds);
        FD_SET(udp_sockfd, &readfds);

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
            // Broadcast message
            for (int i = 8090; i < 8099; i++) {
                broadcast_addr.sin_port = htons(i);
                if (sendto(udp_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&broadcast_addr, broadcast_len) == SOCKET_ERROR) {
                    printf("Broadcast error: %d\n", WSAGetLastError());
                    continue;
                } else printf("Message successfully sent to SERVER %i.\n", i - 8089);
            }
        }
        // Receive message from UDP1
        if (FD_ISSET(udp_sockfd, &readfds)) {
            memset(buffer, 0, BUF);
            n = recvfrom(udp_sockfd, buffer, BUF, 0, (struct sockaddr*)&udp_addr, &udp_len);
            if (n == SOCKET_ERROR) {
                printf("Receive error: %d\n", WSAGetLastError());
                continue;
            } else printf("Message received from UDP1: %s, address: %s\n", buffer, inet_ntoa(udp_addr.sin_addr));
            // Check if Ip address is the same
            if (ntohs(udp_addr.sin_port) == udp_port) {
                printf("Ignored own broadcast from %s\n", inet_ntoa(udp_addr.sin_addr));
                continue;
            }

            if (sendto(client_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&client_addr, client_len) == SOCKET_ERROR) {
                printf("Send error: %d\n", WSAGetLastError());
                continue;
            } else printf("Message successfully sent to client.\n");
        }
    }
    closesocket(udp_sockfd);
    closesocket(client_sockfd);
    WSACleanup();
    return 0;
}