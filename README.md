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