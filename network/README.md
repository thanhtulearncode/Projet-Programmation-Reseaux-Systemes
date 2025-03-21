SERVEUR UPD BROADCAST sur WINDOWS: 
broadserv.c

Compiler:
gcc -o broadserv broadserv.c

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