import socket
import select
import sys

BUF = 512
SERVER_PORT = 8087  # Port fixe pour communiquer avec le serveur
SERVER_IP="127.0.0.1"
def main():
    # Demander l'adresse IP du serveur à l'utilisateur

    try:
        # Créer un socket UDP
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"Client UDP prêt. Connecté au serveur {SERVER_IP}:{SERVER_PORT}.")
    except socket.error as e:
        print(f"Erreur lors de la création du socket : {e}")
        exit(1)

    # Envoyer une demande de connexion au serveur
    try:
        connect_message = "CONNECT"
        client_socket.sendto(connect_message.encode(), (SERVER_IP, SERVER_PORT))
        print(f"Demande de connexion envoyée au serveur : {connect_message}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de la demande de connexion : {e}")
        client_socket.close()
        exit(1)

    while True:
        # Utiliser select pour surveiller l'entrée utilisateur et les messages du serveur
        readable, _, _ = select.select([client_socket], [], [])

        for sock in readable:
            if sock == client_socket:
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