# AIge of EmpAIre

**AIge of EmpAIre** est un clone de jeu de stratégie en temps réel (RTS) inspiré d'Age of Empires. Développé principalement en Python avec Pygame pour le moteur graphique et certaines logiques, il intègre également des composants en C pour la gestion réseau haute performance (UDP/Broadcast).

## 📋 Fonctionnalités

- **Moteur isométrique** : Vue en 2.5D avec gestion de la caméra et mini-map.
- **Unités et Bâtiments** : Gestion de différents types d'unités (Villageois, Épéistes, Archers, Cavaliers) avec animations (marche, attaque, mort, travail).
- **Ressources** : Collecte de bois, or et nourriture.
- **Multijoueur** : Architecture client-serveur hybride Python/C pour le jeu en réseau.
- **IA** : Présence de composants d'intelligence artificielle (indiqués par la structure du projet).

## ⚙️ Prérequis

### Python (Client & Logique)

Le jeu nécessite **Python 3.x** et les bibliothèques suivantes :

- `pygame` (moteur graphique)
- `numpy` (calculs matriciels/numériques)
- `pillow` (gestion avancée d'images, PIL)

Vous pouvez installer les dépendances via pip :

```bash
pip install pygame numpy pillow
```

### C (Serveur Réseau - Windows)

Pour héberger des parties multijoueurs, vous devez compiler les serveurs C.

- **Compilateur** : GCC (MinGW-w64 recommandé pour Windows).
- Voir la section [Configuration Réseau](https://www.google.com/search?q=%23-configuration-r%C3%A9seau-windows) pour les détails.

## 🚀 Démarrage

Le point d'entrée principal du jeu est situé dans `backend/main.py`.

### Lancement standard

Depuis la racine du projet :

```bash
python "AIge of EmpAIre/backend/main.py"
```

### Options de lancement

Le jeu supporte des arguments en ligne de commande :

- **Mode Debug** : Active les fonctionnalités de débogage.
  ```bash
  python "AIge of EmpAIre/backend/main.py" -d
  # ou
  python "AIge of EmpAIre/backend/main.py" --debug
  ```
- **Charger une sauvegarde** : Lance le jeu directement depuis un fichier de sauvegarde spécifique.
  ```bash
  python "AIge of EmpAIre/backend/main.py" -s "chemin/vers/sauvegarde.save"
  ```

## 🎮 Contrôles

### Clavier

| Touche                      | Action                                 |
| :-------------------------- | :------------------------------------- |
| **Flèches directionnelles** | Déplacer la caméra                     |
| **F1**                      | Afficher/Masquer les ressources        |
| **F2**                      | Afficher/Masquer les unités            |
| **F3**                      | Afficher/Masquer la mini-map           |
| **F4**                      | Activer/Désactiver le "Code de triche" |
| **F8**                      | Basculer en plein écran                |
| **F9**                      | Quitter le jeu                         |

### Souris

- **Clic Gauche** : Sélectionner des unités, interagir avec l'interface.
- **Maintenir Clic Gauche sur Mini-map** : Déplacement rapide de la caméra.

## 🌐 Configuration Réseau (Windows)

Le multijoueur repose sur deux composants C à compiler : un serveur de broadcast et un serveur UDP par machine.

### 1\. Installation du compilateur (GCC/MinGW-w64)

1.  Téléchargez la version 14 x64 de MinGW-w64 sur [winlibs.com](https://winlibs.com/).
2.  Extrayez l'archive.
3.  Ajoutez le chemin du dossier `bin` (ex: `...\mingw64\bin`) à votre variable d'environnement `PATH` Windows.
4.  Vérifiez l'installation dans un terminal avec `gcc --version`.

### 2\. Compilation des serveurs

Naviguez dans le dossier `AIge of EmpAIre/network/` et compilez les fichiers C :

**Serveur Broadcast (broadserv) :**

```bash
gcc -o broadserv broadserv.c -lws2_32 -liphlpapi
```

_Utilise le port 8080 (inter-serveur) et 8081 (serveur-client)._

**Serveur UDP Machine (servudp) :**

```bash
gcc -o udp servudp.c -lws2_32
```

### 3\. Configuration du Pare-feu

Autorisez le trafic UDP sur les ports nécessaires (exemple pour le port 8080) :

- **PowerShell** :
  ```powershell
  New-NetFirewallRule -DisplayName "Allow UDP Port" -Direction Inbound -Protocol UDP -Action Allow -LocalPort 8080 -Profile Private
  ```
- **CMD** :
  ```cmd
  netsh advfirewall firewall add rule name="Allow UDP Port" protocol=UDP dir=in localport=8080 action=allow profile=private
  ```

### 4\. Exécution des serveurs

- Lancez `broadserv.exe` (une seule instance par réseau local).
- Sur chaque machine jouant, lancez `udp.exe` avec un ID unique :
  ```bash
  .\udp.exe 1
  # La machine 1 écoutera sur les ports 8081 (Python) et 8091 (C)
  ```
