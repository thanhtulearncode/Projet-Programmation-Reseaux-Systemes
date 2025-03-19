import socket
import select
import sys

BUF = 512
SERVER_PORT = 8083  # Port fixe pour communiquer avec le serveur

def main():
    # Demander l'adresse IP du serveur à l'utilisateur
    server_ip = input("Entrez l'adresse IP du serveur : ").strip()

    try:
        # Créer un socket UDP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"Client UDP prêt. Connecté au serveur {server_ip}:{SERVER_PORT}.")
    except socket.error as e:
        print(f"Erreur lors de la création du socket : {e}")
        exit(1)

    # Envoyer une demande de connexion au serveur
    try:
        connect_message = "CONNECT"
        client_socket.sendto(connect_message.encode(), (server_ip, SERVER_PORT))
        print(f"Demande de connexion envoyée au serveur : {connect_message}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de la demande de connexion : {e}")
        client_socket.close()
        exit(1)

    while True:
        # Utiliser select pour surveiller l'entrée utilisateur et les messages du serveur
        readable, _, _ = select.select([sys.stdin, client_socket], [], [])

        for sock in readable:
            if sock == sys.stdin:
                # Lire l'entrée utilisateur pour envoyer un message
                message = input()
                if message.lower() == "exit":
                    print("Fermeture de la connexion...")
                    client_socket.close()
                    exit(0)
                client_socket.sendto(message.encode(), (server_ip, SERVER_PORT))
                print(f"Message envoyé au serveur : {message}")
            elif sock == client_socket:
                # Recevoir un message du serveur
                data, addr = client_socket.recvfrom(BUF)
                received_message = data.decode()

                # Vérifier si le message reçu est une confirmation de connexion
                if received_message == "Connexion acceptée par le serveur. Vous pouvez maintenant envoyer des messages.":
                    print("Message du serveur : Connexion acceptée. Vous pouvez maintenant envoyer des messages.")
                else:
                    # Afficher les messages normaux reçus d'autres clients
                    print(f"Message reçu de autre client : {received_message}")

if __name__ == "__main__":
    main()