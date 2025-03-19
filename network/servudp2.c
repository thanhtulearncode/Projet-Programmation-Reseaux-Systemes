#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/stat.h>

#define BUF 512
#define PORT_UDP2 "8085"  // Port pour communiquer avec UDP1
#define PORT_CLIENT 8086  // Port pour communiquer avec le client

void stop(char* msg) {
    perror(msg);
    exit(1);
}

void forward_file_to_client(int sockfd, struct sockaddr_in *udp1_addr, socklen_t udp1_len, struct sockaddr_in *client_addr, socklen_t client_len) {
    char buffer[BUF];
    int n;

    printf("Transfert du fichier de UDP1 vers le client...\n");

    // Recevoir les données de UDP1 et les transférer au client
    while (1) {
        memset(buffer, 0, BUF);
        n = recvfrom(sockfd, buffer, BUF, 0, (struct sockaddr*)udp1_addr, &udp1_len);
        if (n <= 0) break;  // Fin de la réception si aucune donnée

        // Vérifier si c'est la fin de la transmission
        if (strncmp(buffer, "END", 3) == 0) {
            printf("Fin de la transmission du fichier.\n");
            sendto(sockfd, buffer, n, 0, (struct sockaddr*)client_addr, client_len);  // Transférer "END" au client
            break;
        }

        // Transférer les données au client
        if (sendto(sockfd, buffer, n, 0, (struct sockaddr*)client_addr, client_len) < 0) {
            perror("Erreur lors du transfert des données au client");
            break;
        }
    }

    printf("Fichier transféré avec succès au client.\n");
}

int main(int argc, char* argv[]) {
    int sockfd, client2_sockfd, n;
    char buffer[BUF];
    struct sockaddr_in udp1_addr, client2_addr, client2_listen_addr, server_addr;
    struct addrinfo hints, *udp1_info;
    socklen_t udp1_len = sizeof(udp1_addr), client2_len = sizeof(client2_addr);

    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET; 
    hints.ai_socktype = SOCK_DGRAM;

    if (getaddrinfo(argv[1], PORT_UDP2, &hints, &udp1_info) != 0)
        stop("Erreur de configuration de l'adresse du serveur UDP1");

    // Création du socket pour communiquer avec UDP1
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
        stop("Erreur de création du socket");

    // Création du socket pour communiquer avec le client
    if ((client2_sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
        stop("Erreur de création du socket client");

    // Associer le socket client à un port spécifique (PORT_CLIENT)
    memset(&client2_listen_addr, 0, sizeof(client2_listen_addr));
    client2_listen_addr.sin_family = AF_INET;
    client2_listen_addr.sin_addr.s_addr = INADDR_ANY;  // Écouter sur toutes les interfaces réseau
    client2_listen_addr.sin_port = htons(PORT_CLIENT);

    if (bind(client2_sockfd, (struct sockaddr*)&client2_listen_addr, sizeof(client2_listen_addr)) < 0) {
        stop("Erreur de liaison (bind) du socket client");
    }
    printf("Serveur UDP2 en écoute sur le port %d pour le client...\n", PORT_CLIENT);

    // Configurer l'adresse de UDP1
    memset(&udp1_addr, 0, sizeof(udp1_addr));
    udp1_addr = *(struct sockaddr_in*)udp1_info->ai_addr;

    // Envoyer la demande de connexion à UDP1
    snprintf(buffer, BUF, "Demande de connexion de UDP2");
    printf("Envoi de la demande de connexion à Serveur UDP1...\n");
    if (sendto(sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp1_addr, udp1_len) < 0)
        stop("Erreur d'envoi de la demande de connexion à UDP1");

    printf("Demande de connexion envoyée à UDP1.\n");

    // Traiter les données reçues (fichiers ou messages)
    while (1) {
        memset(buffer, 0, BUF);
        n = recvfrom(sockfd, buffer, BUF, 0, (struct sockaddr*)&udp1_addr, &udp1_len);
        if (n < 0) {
            perror("Erreur de réception");
        } else {
            if (strncmp(buffer, "FILE", 4) == 0) {
                // Recevoir un fichier de UDP1
                printf("Le UDP1 envoie un fichier...\n");

                // Attendre une requête READY du client
                printf("En attente de la requête du client...\n");
                memset(buffer, 0, BUF);
                n = recvfrom(client2_sockfd, buffer, BUF, 0, (struct sockaddr*)&client2_addr, &client2_len);
                if (n > 0 && strncmp(buffer, "READY", 5) == 0) {
                    printf("Requête READY reçue du client.\n");
                    forward_file_to_client(sockfd, &udp1_addr, udp1_len, &client2_addr, client2_len);
                }
            } else {
                printf("Message reçu de UDP1 : %s\n", buffer);
                // Répondre à UDP1
                snprintf(buffer, BUF, "Le message reçu et traité par UDP2");
                if (sendto(sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp1_addr, udp1_len) < 0)
                    perror("Erreur d'envoi de la réponse à UDP1");
            }
        }
    }

    close(sockfd);
    close(client2_sockfd);
    return 0;
}
