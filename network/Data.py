import csv
from ctypes import WinError
import socket
import select
import sys
import subprocess
from time import sleep

BUF = 512
SERVER_IP = "127.0.0.1"
class PacketManager:
    _instance = None 
    package_header = ""   
    _initialized = False  
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PacketManager, cls).__new__(cls)
            cls._instance.player = None
            cls._instance.package = ""
        return cls._instance
    
    def __init__(self):
        if not PacketManager._initialized:
            self.player = None
            self.package = ""
            self.map = None
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_address = ("127.0.0.1")
            try:
                with open("../network/current_players.txt", "r") as file:
                    current_number = int(file.read().strip())
                port_id = current_number % 8
                self.server_port = 8080 + port_id
                process = subprocess.Popen(["..\\network\\udp.exe", str(port_id)], creationflags=subprocess.CREATE_NEW_CONSOLE)
                current_number += 1
                with open("../network/current_players.txt", "w") as file:
                    file.write(str(current_number))
                sleep(1.5)
            except (FileNotFoundError, ValueError) as e:
                print(f"Error reading or updating current_players.txt: {e}")
                self.server_port = 8080
            PacketManager._initialized = True
    @classmethod
    def create_unit_packet(self, unit, type):
        unit_packet = f"{type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.player.id}"
        unit.player.package.package += f"{unit_packet}\n"
        print(unit_packet)
                
    @staticmethod
    def process_packet(data) -> list:
        result = []
        # Remove trailing asterisk if only one message
        if data.count('*') <= 1:
            data = data.rstrip('*')
            
        items = data.split('*')

        for item in items:
            if item.strip():  # Skip empty items
                parts = item.strip().split(';')
                # Check if first element is a number
                if parts and parts[0].isdigit():
                    result.append(parts)
                else:
                    result.append(['None'])
        
        return result
        
    @classmethod
    def create_map_packet(self, map):
        map_packet = ""
        for row in map:
            for cell in row:
                if cell:
                    if cell.resource:
                        map_packet += cell.resource.symbol
                    elif cell.unit:
                        map_packet += cell.unit.symbol
                    elif cell.building:
                        map_packet += cell.building.symbol
                    elif cell.rubble:
                        map_packet += cell.rubble.symbol
                    else:
                        map_packet += "."
            map_packet += "\n"
        print(map_packet)
        self.map = map_packet

    @classmethod
    def create_unit_packet(self, unit, type):
        unit_packet = f"{type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.player.id}"
        unit.player.package.package += f"{unit_packet}\n"
        print(unit_packet)
    
    
    @classmethod
    def create_building_packet(self, building, type):
        building_packet = f"{type};{building.name};{building.position[0]};{building.position[1]};{building.hp};{building.player.id}"
        building.player.package.package += f"{building_packet}\n"
        print(building_packet)
                

        
    def extract_package(self, row):
        PacketManager.package_header = f"{row[0]};{row[1]};{row[2]};{row[3]};{row[4]}"
        return PacketManager.package_header
        
    def process_csv(self, file_name):
        with open(file_name, mode="r") as file:
            reader = csv.reader(file, delimiter=';')
            next(reader, None) 
            next(reader, None) 
            for row in reader:
                package_header = self.extract_package(row)
                print(package_header)
                
    #send self.package to the server
    def send_packet(self):
        self.socket.setblocking(False)
        try:
            self.socket.sendto(self.package.encode('utf-8'), (SERVER_IP, self.server_port))
            print(f"Message envoyé au serveur")
        except socket.error as e:
            print(f"Erreur lors de l'envoi du message: {e}")

    def receive_packet(self)-> str:
        try:
            self.socket.setblocking(False)  
        except socket.error as e:
            sys.exit(1)

        while True:    
            readable, _, _ = select.select([self.socket], [], [],0)
            received_packets = None
            for sock in readable:
                if sock == self.socket:
                    
                    received_packets,_= self.socket.recvfrom(BUF)

            return received_packets.decode('utf-8') if received_packets else None
    
class Resource_manager:
    _instance = None

    def __new__(cls, player):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.player = player
        return cls._instance
    
    def __init__(self, player):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.player = player
        else:
            self.player = player  # Ensure self.player is updated if already initialized
        print("Resource Manager initialized for player", self.player)
    @classmethod
    def create_init_resource_request(self, target_player_id=0):
        return f"{self._instance.player};{target_player_id}"
    @classmethod
    def create_init_resource_response(self, requesting_player_id, resources):
        if self._instance.player.id == 0: 
            resource_values = [str(amount) for amount in resources.values()]
            resource_str = ";".join(resource_values)
            return f"{requesting_player_id};{resource_str}"
        return None

print(PacketManager.process_packet(';remove_unit;2.v.515;31.2;109.717*;remove_unit;2.v.515;31.2;109.717*'))
