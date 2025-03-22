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


SERVEUR UPD sur WINDOWS:
broadserv.c

Compiler:
gcc -o broadserv broadserv.c -lws2_32 -liphlpapi

Communication inter-server: port 8080
             client-server: port 8081

Avant execute:
Ajoute nouvelle regle pour le pare-feu Window

1. Execute Powershell en tant qu'administrateur

2. New-NetFirewallRule -DisplayName "Allow UDP Ports" -Direction Inbound -Profile Private -Protocol UDP -LocalPort 8080 -Action Allow


!!! REMARQUE:
UNE SEULE serveur sur une machine
la client doit envoyer un message au server pour etablir une connection

For test sur le branche test_netwwork: broadserv.c > listen.py > test.py
For le test sur main : broadserv.c ( si local network) ou si localhost udpserv.c