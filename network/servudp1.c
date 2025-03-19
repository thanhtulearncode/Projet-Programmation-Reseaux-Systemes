#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define BUF 512
#define PORT_CLIENT 8083  // Port pour communiquer avec les clients
#define MAX_CLIENTS 10    // Nombre maximum de clients que le serveur peut gérer

void stop(char* msg) {
    perror(msg);
    exit(1);
}

int main() {
    int client_sockfd, n;
    char buffer[BUF];
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);
    struct sockaddr_in clients[MAX_CLIENTS];  // Tableau pour stocker les adresses des clients connectés
    int client_count = 0;  // Nombre actuel de clients connectés

    // Créer un socket UDP pour le serveur
    if ((client_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
        stop("Erreur de création du socket serveur");

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(PORT_CLIENT);

    if (bind(client_sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0)
        stop("Erreur de bind");

    printf("Serveur UDP en écoute sur le port %d...\n", PORT_CLIENT);

    // Boucle principale pour recevoir les demandes de connexion et transmettre les messages
    while (1) {
        memset(buffer, 0, BUF);
        n = recvfrom(client_sockfd, buffer, BUF, 0, (struct sockaddr*)&client_addr, &client_len);
        if (n < 0)
            stop("Erreur de réception");

        printf("Message reçu de %s:%d\n", inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));

        if (strncmp(buffer, "CONNECT", 7) == 0) {
            // Ajouter l'adresse du client dans la liste si le message est CONNECT
            int already_connected = 0;
            for (int i = 0; i < client_count; i++) {
                if (clients[i].sin_addr.s_addr == client_addr.sin_addr.s_addr &&
                    clients[i].sin_port == client_addr.sin_port) {
                    already_connected = 1;
                    break;
                }
            }

            if (!already_connected && client_count < MAX_CLIENTS) {
                clients[client_count] = client_addr;
                client_count++;
                snprintf(buffer, BUF, "Connexion acceptée par le serveur. Vous pouvez maintenant envoyer des messages.");
                if (sendto(client_sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&client_addr, client_len) < 0)
                    stop("Erreur d'envoi de la réponse au client");
                printf("Connexion acceptée et message envoyé au client.\n");
            }
        } else {
            // Si le message n'est pas CONNECT, le transférer à tous les clients sauf celui qui a envoyé le message
            for (int i = 0; i < client_count; i++) {
                if (clients[i].sin_addr.s_addr != client_addr.sin_addr.s_addr ||
                    clients[i].sin_port != client_addr.sin_port) {
                    if (sendto(client_sockfd, buffer, n, 0, (struct sockaddr*)&clients[i], sizeof(clients[i])) < 0)
                        stop("Erreur de transfert de message");
                }
            }
            printf("Message transféré à tous les clients.\n");
        }
    }

    close(client_sockfd);
    return 0;
}
