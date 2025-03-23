INSTALLER GCC AND MINGW-W64 FOR WINDOWS:

1. Accéder au site: https://winlibs.com/ et télécharger la version 14 x64x64

2. Choisir le chemin et décompresser 

3. Chercher le chemin du dossier contenant mingw64\bin ( parEX: D:\winlibs-x86_64-posix-seh-gcc-14.2.0-llvm-19.1.7-mingw-w64ucrt-12.0.0-r3\mingw64\bin )

4. Copier ce chemin et ajouter au variable d'environnement par la commande sur powershell: 
parex:
$env:Path += ";D:\winlibs-x86_64-posix-seh-gcc-14.2.0-llvm-19.1.7-mingw-w64ucrt-12.0.0-r3\mingw64\bin"

si non
Ouvrez le Contraol pannel > Systeme et srcurity > Systeme > Advanced system setting
Sélectionnez Environnement Variables.
Dans la fenêtre Variables système, recherchez et sélectionnez PathPath, puis cliquez sur Modifier.
Dans la fenêtre Modifier la variable d'environnement, sélectionnez Nouveau et ajoutez ton chemin

5. Verifier le chemin  sur VScode ou PowerShell: $env:Path -split ';'

6. Redémarrez tonton ordinateur et vscode


SERVEUR UPD BROADCAST sur WINDOWS: 
broadserv.c 
broadserv.c

Compiler:
gcc -o broadserv broadserv.c -lws2_32 -liphlpapi    

Communication inter-server:  port 8080
Communication server-client: port 8081

Ajoute règle pour par-feu Window:
Cmd: 
netsh advfirewall firewall add rule name="Allow UDP Port" protocol=UDP dir=in localport=8080 action=allow profile=private
Powershell:
New-NetFirewallRule -DisplayName "Allow UDP Port" -Direction Inbound -Protocol UDP -Action Allow -LocalPort 8080 -Profile Private

!!!REMARQUE: 
le client doit envoyer un message au server pour etablir une connection
UNE SEULE broadcast serveur sur un ordinateur

SERVEUR SUR 1 MACHINE
servudp.c
gcc -o udp servudp.c -lws2_32

Execute:
.\udp.exe ID

Serveur ecoute sur 2 ports: Port 808x (pour processus python) 
                            Port 809x (pour processus C)
                            x: ID
Exemple: .\udp.exe 1 écoute sur 2 port 8081 et 8091

!!!REMARQUE:
 - Le client python doit envoyer le message au bon port c.a.d 808x
 - Si le message dépasse le buffer, le serveur ne peut pas le recevoir. Meme principle pour le client
    Pour le recevoir il faut augmenter la taille de buffer