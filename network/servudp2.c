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
#define PORT_UDP2 "8085"
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

int main( int argc, char* argv[] ) {
    int sockfd, n;
    char buffer[BUF];
    struct sockaddr_in udp1_addr;
    struct addrinfo hints, *udp1_info;
    socklen_t udp1_len = sizeof(udp1_addr);
    memset(&hints, 0, sizeof hints);
    hints.ai_family = AF_INET; 
    hints.ai_socktype = SOCK_DGRAM;
    if (getaddrinfo(argv[1], PORT_UDP2, &hints, &udp1_info) != 0)
        stop("Erreur de configuration de l'adresse du serveur UDP1");

    // Création du socket UDP sans bind
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0)
        stop("Erreur de création du socket");

    memset(&udp1_addr, 0, sizeof(udp1_addr));
    udp1_addr = *(struct sockaddr_in*)udp1_info->ai_addr;
    //udp1_addr.sin_family = AF_INET;
    //udp1_addr.sin_port = htons(PORT_UDP2);
    //if(inet_aton(argv[1], &udp1_addr.sin_addr) == 0)
	//	printf("inet_aton server failed\n");

    // Envoyer la demande de connexion à UDP1
    snprintf(buffer, BUF, "Demande de connexion de UDP2");
    printf("Envoi de la demande de connexion à Serveur UDP1...\n");
    if (sendto(sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp1_addr, udp1_len) < 0)
        stop("Erreur d'envoi de la demande de connexion à UDP1");

    printf("Demande de connexion envoyée à UDP1.\n");
    // Xử lý dữ liệu từ client (tệp hoặc tin nhắn)
    while (1) {
        memset(buffer, 0, BUF);
        n = recvfrom(sockfd, buffer, BUF, 0, (struct sockaddr*)&udp1_addr, &udp1_len);
        if (n < 0) {
            perror("Erreur de réception");
        } else {
            if (strncmp(buffer, "FILE", 4) == 0) {
                // Nhận tệp từ udp1
                printf("Le UDP 1 envoie un fichier...\n");
                save_file(sockfd, &udp1_addr, udp1_len);
            } else {
                printf("Message reçu de UDP1 : %s\n", buffer);
                // Répondre à UDP1
                snprintf(buffer, BUF, "le message reçu et traité par UDP2");
                if (sendto(sockfd, buffer, strlen(buffer), 0, (struct sockaddr*)&udp1_addr, udp1_len) < 0)
                    perror("Erreur d'envoi de la réponse à UDP1");

            }
        }
    }

    close(sockfd);
    return 0;
}
