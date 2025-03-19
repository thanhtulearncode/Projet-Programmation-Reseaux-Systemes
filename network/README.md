SERVEUR UPD sur WINDOWS:

Compiler:
gcc -o udp1 servudp1.c -lws2_32
gcc -o udp2 servudp2.c -lws2_32

Avant execute: udp1.exe et udp2.exe
Ajoute nouvelle regle pour le pare-feu Window

1. Execute Powershell en tant qu'administrateur

2. New-NetFirewallRule -DisplayName "Allow UDP Ports" -Direction Inbound -Profiles Private -Protocol UDP -LocalPort 8083,8085,8087 -Action Allow
