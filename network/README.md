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