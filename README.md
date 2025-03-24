# Projet Python : Alge of EmpAlres

## 📜 Introduction

Ce projet consiste à implémenter un moteur de jeu de stratégie en temps réel (RTS) simplifié, inspiré par *Age of Empires*. L'objectif est de créer un environnement où des intelligences artificielles (IA) s'affrontent dans des batailles stratégiques. Le projet se concentre sur le développement du moteur de jeu et la création de profils d'IA variés (défensifs, offensifs, etc.).

Le jeu se déroule sur une carte générée aléatoirement, avec des ressources limitées et des unités spécifiques. Les joueurs (IA) doivent gérer leurs ressources, construire des bâtiments, et entraîner des unités pour vaincre leurs adversaires.

## 🎯 Objectifs du Projet

- **Implémenter un moteur de jeu RTS simplifié**.
- **Développer des profils d'IA** pour des stratégies variées.
- **Générer des cartes aléatoires** avec des ressources stratégiquement placées.
- **Visualiser le jeu** en mode terminal et en 2.5D (isométrique).
- **Permettre la sauvegarde et le chargement** des parties.

## 🛠️ Fonctionnalités

### 🗺️ Génération de Carte
- **Carte aléatoire** de taille minimale 120x120.
- **Deux types de cartes** : ressources dispersées ou concentrées au centre.

### 🏗️ Bâtiments et Unités
- **Bâtiments** : Town Centre, House, Camp, Farm, Barracks, Stable, Archery Range, Keep.
- **Unités** : Villager, Swordsman, Horseman, Archer.

### 🤖 Intelligence Artificielle
- **Profils d'IA** : Défensif, Offensif, Équilibré.
- **Stratégies** : Gestion des ressources, attaques coordonnées, défense.

### 🎮 Visualisation
- **Mode Terminal** : Affichage simplifié pour suivre le déroulement du jeu.
- **Mode 2.5D** : Vue isométrique avec des sprites pour une expérience immersive.

### 💾 Sauvegarde et Chargement
- **Sauvegarde rapide** (F10) et **chargement rapide** (F12).
- **Gestion de fichiers** : Nombre illimité de sauvegardes.

## 📊 Schémas

### Architecture du Moteur de Jeu
```mermaid
graph TD
    A[Game Engine] --> B[Map Generation]
    A --> C[AI Logic]
    A --> D[Unit Management]
    A --> E[Resource Management]
    A --> F[Visualization]
    F --> G[Terminal View]
    F --> H[2.5D View]

# Projet-Programmation-Reseaux-Systemes
1. créer des paquets:
Data.py
1.1. create_map_packet(self, map):
    map : Map Object
    output : paquet de type string
    Exemple: 
    "
    ...WWW...G
    ....W..G..
    ..........
    ..GG......
    WWWW......
    "
1.2. create_unit_packet(self, unit, type): 
    input:
        unit : Unit Object
        type : "spawn_unit", "place_unit", "remove_unit", "kill_unit"
    output : string f"{type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.player.id}"
    Exemple: "place_unit;Thibaud;35;106;25;2"
1.3. create_building_packet(self, building, type):
    input:
        building : Building Object
        type : "spawn_building", "kill_building"
    output : string f"{type};{building.name};{building.position[0]};{building.position[1]};{building.hp};{building.player.id}"
    Exemple: "spawn_building;Town Center;34;106;1000;2"
2. mettre à jour le jeu à partir des paquets:
Terrain.py
2.1. update_initial_map(self, map_packet):
    input:
        map_packet : packet de type string (actuel, on peut optimiser le type de map_packet) 
    output : ressources initiales du jeu
Game_Engine.py
2.2. update_units(self, unit_packet):
    input:
        unit_packet : packet de type string (actuel) #on peut l'optimiser
    output : état actuel des unités
2.3. update_buildings(self, building_packet):
    input:
        unit_packet : packet de type string (actuel) #on peut l'optimiser
    output : état actuel des bâtiments
2.4. update_map(self, packet):
    input:
        unit_packet : grand paquet de type string contenant les état des bâtiment et des unités (mixe)
    output : état actuel du jeu

### thiếu cập nhật resource hiện tại, đợi Trí cmt readme ###


######################################
1. packet = creat_blabla_packet(): tạo packet và cộng dồn vào Packetmanager, trả về packet đại diện cho thay đổi bên dưới
2. processing() :
2.1. gửi packet từ PacketManager, sau đó nhận packet và lại cộng dồn vào, ta được packets của toàn bộ players
2.2. lọc
3. kiểm tra packet còn nằm trong PacketManager.package không, nếu có thì update_game()

Ví dụ packet:
"""unit_packet = f"{current_time_call};{unit.player.id};{type};{target.position[0]};{target.position[1]};"
        unit_packet += f"{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.task};{unit.direction};"   
        self.package += f"{unit_packet}*""""

"""def create_building_packet(self, building, type, target, current_time_call):
        building_packet = f"{current_time_call};{building.player.id};{type};{target.position[0]};{target.position[1]};{ta}"
        building_packet += f"{building.name};{building.position[0]};{building.position[1]};{building.hp}"
        return f"{building_packet}*""""
"1742843162.730921;1;_attack;45;45;20;Mbappé;34;44;20;going_to_battle;southwest"
"1742843162.730921;1;spawn_building;45;45;20;House;None;None;None"
"1742843162.730921;1;kill_building;None;None;House;45;45;0"