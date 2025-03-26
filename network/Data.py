import csv
import socket
import select
import sys
import subprocess
import threading
import zlib
from time import sleep

BUF = 12000
SERVER_IP = "127.0.0.1"

class PacketManager:
    _instance = None 
    package_header = ""   
    _initialized = False  
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PacketManager, cls).__new__(cls)
            cls._instance.package = ""
        return cls._instance
    
    def __init__(self):
        if not PacketManager._initialized:
            self.player = None
            self.package = ""
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_address = SERVER_IP
            try:
                with open("../network/current_players.txt", "r") as file:
                    current_number = int(file.read().strip())
                port_id = current_number % 8
                self.server_port = 8080 + port_id
                subprocess.Popen(["..\\network\\udp.exe", str(port_id)], creationflags=subprocess.CREATE_NEW_CONSOLE)
                with open("../network/current_players.txt", "w") as file:
                    file.write(str(current_number + 1))
                sleep(2)
            except (FileNotFoundError, ValueError) as e:
                print(f"Error handling current_players.txt: {e}")
                self.server_port = 8080
            PacketManager._initialized = True

    @staticmethod
    def process_packet(data):
        if not data:
            return []
        data = data.rstrip('*')  # Remove trailing asterisk
        return [item.strip().split(';') for item in data.split('*') if item.strip()]
    
    @classmethod
    def create_map_packet(cls, game_map):
        return f"0;map;{game_map.map_encoding()}"
    
    @classmethod
    def create_unit_packet(cls, unit, action_type):
        return f"{unit.player.id};{action_type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.task};{unit.direction}*"
    
    @classmethod     
    def create_building_packet(cls, building, action_type):
        return f"{building.player.id};{action_type};{building.name};{building.position[0]};{building.position[1]};{building.hp}*"
    
    @classmethod
    def create_current_state_packet(cls, players):
        return "".join(cls.create_unit_packet(unit, "current_unit") for p in players for unit in p.units) + "".join(cls.create_building_packet(building, "current_building") for p in players for building in p.buildings)

    def send_packet(self):
        self.socket.setblocking(False)
        try:
            self.socket.sendto(self.package.encode('utf-8'), (SERVER_IP, self.server_port))
            print("Packet sent to server.")
        except socket.error as e:
            print(f"Error sending packet: {e}")
        self.package = ""

    def receive_packet(self, timeout=0):
        self.socket.setblocking(False)
        readable, _, _ = select.select([self.socket], [], [], timeout)
        for sock in readable:
            if sock == self.socket:
                received_packets, _ = self.socket.recvfrom(BUF)
                return received_packets.decode('utf-8')
        return None

class ResourceManager:
    _instance = None
    
    def __new__(cls, player):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.player = player
        return cls._instance
    
    def __init__(self, player):
        self.player = player
        print(f"Resource Manager initialized for player {self.player}")

    @classmethod
    def create_init_resource_request(cls, target_player_id=0):
        return f"{cls._instance.player.id};{target_player_id}"
    
    @classmethod
    def create_init_resource_response(cls, requesting_player_id, resources):
        if cls._instance.player.id == 0: 
            return f"{requesting_player_id};{';'.join(map(str, resources.values()))}"
        return None

if __name__ == "__main__":
    test_packet = ';remove_unit;2.v.515;31.2;109.717*;remove_unit;2.v.515;31.2;109.717*'
    print(PacketManager.process_packet(test_packet))