#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <fcntl.h>

#define BUF 512
#define PORT_CLIENT 8083
#define PORT_UDP2 8085


void stop(char* msg) {
    perror(msg);
    exit(1);
}


int main() {
    int client_sockfd, udp2_sockfd, n;
    char buffer[BUF];
    struct sockaddr_in client_addr, udp2_addr, client_listen_addr, udp2_listen_addr;
    socklen_t client_len = sizeof(client_addr);
    socklen_t udp2_len = sizeof(udp2_addr);

    // Tạo socket UDP cho client
    if ((client_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
        stop("Erreur de création du socket client");

    memset(&client_listen_addr, 0, sizeof(client_listen_addr));
    client_listen_addr.sin_family = AF_INET;
    client_listen_addr.sin_addr.s_addr = INADDR_ANY;
    client_listen_addr.sin_port = htons(PORT_CLIENT);

    if (bind(client_sockfd, (struct sockaddr*)&client_listen_addr, sizeof(client_listen_addr)) < 0)
        stop("Erreur de bind pour client");

    printf("Serveur UDP1 en écoute sur le port %d pour client...\n", PORT_CLIENT);

    // Tạo socket UDP cho server UDP2
    if ((udp2_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
        stop("Erreur de création du socket UDP2");

    memset(&udp2_listen_addr, 0, sizeof(udp2_listen_addr));
    udp2_listen_addr.sin_family = AF_INET;
    udp2_listen_addr.sin_addr.s_addr = INADDR_ANY;
    udp2_listen_addr.sin_port = htons(PORT_UDP2);

    if (bind(udp2_sockfd, (struct sockaddr*)&udp2_listen_addr, sizeof(udp2_listen_addr)) < 0)
        stop("Erreur de bind pour UDP2");

    printf("Serveur UDP1 en écoute sur le port %d pour UDP2...\n", PORT_UDP2);

    // Nhận yêu cầu từ UDP2
    memset(buffer, 0, BUF);
    n = recvfrom(udp2_sockfd, buffer, BUF, 0, (struct sockaddr*)&udp2_addr, &udp2_len);
    if (n < 0)
        stop("Erreur de réception de la demande de connexion de UDP2");

    printf("Demande de connexion reçue de UDP2 : %s\n", buffer);

    // Gửi lại kết quả cho UDP2
    snprintf(buffer, BUF, "Connexion acceptée par UDP1");
    if (sendto(udp2_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp2_addr, udp2_len) < 0)
        stop("Erreur d'envoi de la réponse à UDP2");

    printf("Connexion avec UDP2 établie.\n");

    // Vòng lặp nhận tin nhắn hoặc tệp
    while (1) {
        memset(buffer, 0, BUF);
        n = recvfrom(client_sockfd, buffer, BUF, 0, (struct sockaddr*)&client_addr, &client_len);
        if (n < 0) {
            perror("Erreur de réception du client");
        } else {

            if (strncmp(buffer, "FILE", 4) == 0) {
                printf("Transfert du fichier à Serveur UDP2...\n");
                if (sendto(udp2_sockfd, buffer, n, 0, (struct sockaddr*)&udp2_addr, udp2_len) < 0) {
                    perror("Erreur d'envoi du fichier à UDP2");
                    continue;
                }
                printf("Fichier transféré à Serveur UDP2 avec succès.\n");
                
            } else {
                printf("Message reçu du client : %s\n", buffer);
                // Xử lý tin nhắn
                if (sendto(udp2_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp2_addr, udp2_len) < 0)
                    perror("Erreur d'envoi messages à UDP2");

                // Recevoir la réponse de UDP2
                memset(buffer, 0, BUF);
                n = recvfrom(udp2_sockfd, buffer, BUF, 0, NULL, NULL);
                if (n > 0) {
                    printf("Réponse de UDP2 : %s\n", buffer);

                    // Répondre au client avec la réponse de UDP2
                    if (sendto(client_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&client_addr, client_len) < 0)
                        perror("Erreur d'envoi au client");
                }
            }
        }
    }

    close(client_sockfd);
    close(udp2_sockfd);
    return 0;
}
