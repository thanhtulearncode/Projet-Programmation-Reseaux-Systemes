#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iphlpapi.h>
#include <openssl/ssl.h>
#include <openssl/err.h>

#define BUF 512
#define UDP_PORT 8080
#define CLIENT_PORT 8081

#pragma comment(lib, "Ws2_32.lib")
#pragma comment(lib, "iphlpapi.lib")

void stop(char* msg) {
    printf("Error: %s (code %d)\n", msg, WSAGetLastError());
    exit(1);
}

BOOL CtrlHandler(DWORD fdwCtrlType) {
    if (fdwCtrlType == CTRL_C_EVENT) {
        printf("\nCtrl+C detected, cleaning up and exiting...\n");
        WSACleanup();
        exit(0);
    }
    return FALSE;
}

void getBroadcastAddress(struct sockaddr_in* broadcastAddr) {
    IP_ADAPTER_ADDRESSES *adapterInfo = NULL, *adapter = NULL;
    ULONG outBufLen = 0;
    
    // First call to get the required buffer size
    GetAdaptersAddresses(AF_INET, GAA_FLAG_INCLUDE_PREFIX, NULL, adapterInfo, &outBufLen);
    
    adapterInfo = (IP_ADAPTER_ADDRESSES*)malloc(outBufLen);
    if (GetAdaptersAddresses(AF_INET, GAA_FLAG_INCLUDE_PREFIX, NULL, adapterInfo, &outBufLen) != NO_ERROR) {
        free(adapterInfo);
        printf("Failed to retrieve network adapters.\n");
        return;
    }

    // Iterate through network adapters
    for (adapter = adapterInfo; adapter; adapter = adapter->Next) {
        if (adapter->OperStatus != IfOperStatusUp) continue;  // Skip disabled interfaces
        
        IP_ADAPTER_UNICAST_ADDRESS* addr = adapter->FirstUnicastAddress;
        if (addr && addr->Address.lpSockaddr->sa_family == AF_INET) {
            struct sockaddr_in* sa = (struct sockaddr_in*)addr->Address.lpSockaddr;
            ULONG ip = sa->sin_addr.S_un.S_addr;  // Get IP address

            // Convert PrefixLength (e.g., /24) to Subnet Mask
            ULONG mask = htonl(0xFFFFFFFF << (32 - adapter->FirstPrefix->PrefixLength));

            // Compute Broadcast Address
            ULONG broadcast = ip | ~mask;

            // Store in result
            broadcastAddr->sin_family = AF_INET;
            broadcastAddr->sin_addr.S_un.S_addr = broadcast;
            broadcastAddr->sin_port = 0;  // Port is set elsewhere

            printf("Broadcast Address: %s\n", inet_ntoa(broadcastAddr->sin_addr));
            break;  // Found the first valid interface, exit loop
        }
    }

    free(adapterInfo);
}

void init_openssl() {
    SSL_load_error_strings();
    OpenSSL_add_ssl_algorithms();
}

void cleanup_openssl() {
    EVP_cleanup();
}

SSL_CTX* create_context() {
    const SSL_METHOD* method;
    SSL_CTX* ctx;

    method = DTLS_server_method(); // Utiliser DTLS
    ctx = SSL_CTX_new(method);
    if (!ctx) {
        perror("Unable to create SSL context");
        ERR_print_errors_fp(stderr);
        exit(EXIT_FAILURE);
    }

    return ctx;
}

void configure_context(SSL_CTX* ctx) {
    // Charger le certificat et la clé privée
    if (SSL_CTX_use_certificate_file(ctx, "cert.pem", SSL_FILETYPE_PEM) <= 0) {
        ERR_print_errors_fp(stderr);
        exit(EXIT_FAILURE);
    }

    if (SSL_CTX_use_PrivateKey_file(ctx, "key.pem", SSL_FILETYPE_PEM) <= 0) {
        ERR_print_errors_fp(stderr);
        exit(EXIT_FAILURE);
    }
}

int main(int argc, char* argv[]) {
    if (!SetConsoleCtrlHandler((PHANDLER_ROUTINE)CtrlHandler, TRUE)) {
        stop("SetConsoleCtrlHandler failed");
    }

    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        stop("WSAStartup failed");
    }

    init_openssl();
    SSL_CTX* ctx = create_context();
    configure_context(ctx);

    SOCKET udp_sockfd, client_sockfd;
    int n;
    char buffer[BUF];
    struct sockaddr_in udp_addr, client_addr, broadcast_addr, local_addr;
    int udp_len = sizeof(udp_addr);
    int client_len = sizeof(client_addr);
    int broadcast_len = sizeof(broadcast_addr);
    int local_len = sizeof(local_addr);

    // Create UDP socket
    if ((udp_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        stop("UDP socket creation failed");
    }

    int enable = 65535;
    if (setsockopt(udp_sockfd, SOL_SOCKET, SO_BROADCAST, (char*)&enable, sizeof(enable)) == SOCKET_ERROR) {
        stop("Failed to enable broadcast");
    }

    // Create client socket
    if ((client_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) == INVALID_SOCKET) {
        stop("Client socket creation failed");
    }

    // Bind UDP socket to port
    memset(&udp_addr, 0, sizeof(udp_addr));
    udp_addr.sin_family = AF_INET;
    udp_addr.sin_addr.s_addr = INADDR_ANY;
    udp_addr.sin_port = htons(UDP_PORT);
    if (bind(udp_sockfd, (struct sockaddr*)&udp_addr, udp_len) == SOCKET_ERROR) {
        stop("Bind failed for UDP");
    }

    // Bind client socket to port
    memset(&client_addr, 0, sizeof(client_addr));
    client_addr.sin_family = AF_INET;
    client_addr.sin_addr.s_addr = INADDR_ANY;
    client_addr.sin_port = htons(CLIENT_PORT);
    if (bind(client_sockfd, (struct sockaddr*)&client_addr, client_len) == SOCKET_ERROR) {
        stop("Bind failed for client");
    }

    // Get local IP address
    getsockname(udp_sockfd, (struct sockaddr*)&local_addr, &local_len);
    printf("Local IP address: %s\n", inet_ntoa(local_addr.sin_addr));

    // Set broadcast address
    memset(&broadcast_addr, 0, sizeof(broadcast_addr));
    broadcast_addr.sin_family = AF_INET;
    getBroadcastAddress(&broadcast_addr);
    broadcast_addr.sin_port = htons(UDP_PORT);
    printf("Broadcast address: %s\n", inet_ntoa(broadcast_addr.sin_addr));

    snprintf(buffer, BUF, "Broadcast message");
    if (sendto(udp_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&broadcast_addr, broadcast_len) == SOCKET_ERROR) {
            stop("Broadcast message failed");
    }

    fd_set readfds;
    int max_fd = (client_sockfd > udp_sockfd) ? client_sockfd : udp_sockfd;

    // Configurer DTLS
    BIO* bio = BIO_new_dgram(udp_sockfd, BIO_NOCLOSE);
    if (!bio) {
        perror("Failed to create BIO");
        exit(EXIT_FAILURE);
    }

    SSL* ssl = SSL_new(ctx);
    if (!ssl) {
        perror("Unable to create SSL structure");
        ERR_print_errors_fp(stderr);
        exit(EXIT_FAILURE);
    }

    SSL_set_bio(ssl, bio, bio);

    printf("Server is running and waiting for messages...\n");

    while (1) {
        FD_ZERO(&readfds);
        FD_SET(client_sockfd, &readfds);
        FD_SET(udp_sockfd, &readfds);

        if (select(max_fd + 1, &readfds, NULL, NULL, NULL) == SOCKET_ERROR) {
            stop("Select error");
        }

        // Check if there is a message from the client
        if (FD_ISSET(client_sockfd, &readfds)) {
            memset(buffer, 0, BUF);
            n = recvfrom(client_sockfd, buffer, BUF, 0, (struct sockaddr*)&client_addr, &client_len);
            if (n == SOCKET_ERROR) {
                printf("Receive error: %d\n", WSAGetLastError());
                continue;
            } 
            printf("Message received from client: %s\n", buffer);
            if (sendto(udp_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&broadcast_addr, broadcast_len) == SOCKET_ERROR) {
                printf("Broadcast error: %d\n", WSAGetLastError());
                continue;
            } 
            printf("Message sent to SERVER C\n");
            
        }

        // Check if there is a message from SERVER C
        if (FD_ISSET(udp_sockfd, &readfds)) {
            memset(buffer, 0, BUF);

            // Recevoir un message via DTLS
            int n = SSL_read(ssl, buffer, BUF);
            if (n <= 0) {
                int err = SSL_get_error(ssl, n);
                if (err == SSL_ERROR_WANT_READ || err == SSL_ERROR_WANT_WRITE) {
                    continue;
                }
                ERR_print_errors_fp(stderr);
                break;
            }

            buffer[n] = '\0'; // Terminer la chaîne reçue
            printf("Message reçu : %s\n", buffer);

            // Traiter le message reçu
            if (strncmp(buffer, "1;scan_rooms", 12) == 0) {
                snprintf(buffer, BUF, "3;Utopia;120;120;0;Means;aggressive");
            } else {
                snprintf(buffer, BUF, "Unknown command");
            }

            // Envoyer une réponse via DTLS
            if (SSL_write(ssl, buffer, strlen(buffer)) <= 0) {
                ERR_print_errors_fp(stderr);
                break;
            }
            printf("Réponse envoyée : %s\n", buffer);

            printf("Message received from SERVER C: %s, address: %s\n", buffer, inet_ntoa(udp_addr.sin_addr));
            if (strcmp(inet_ntoa(udp_addr.sin_addr), inet_ntoa(local_addr.sin_addr)) == 0) {
                printf("Ignored own broadcast from %s\n", inet_ntoa(udp_addr.sin_addr));
                continue;
            }
            if (sendto(client_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&client_addr, client_len) == SOCKET_ERROR) {
                printf("Send error: %d\n", WSAGetLastError());
                continue;
            } 
            printf("Message sent to client.\n");
        }
    }

    SSL_shutdown(ssl);
    SSL_free(ssl);
    BIO_free(bio);
    closesocket(udp_sockfd);
    closesocket(client_sockfd);
    SSL_CTX_free(ctx);
    cleanup_openssl();
    WSACleanup();
    return 0;
}
