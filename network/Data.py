import csv
from ctypes import WinError
import socket
import select
import sys
import subprocess
from time import sleep
from network.Game_Room import GameRoomManager
import os
from ctypes import WinError
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64

BUF = 12000
SERVER_IP = "127.0.0.1"
SECRET_KEY = GameRoomManager.get_aes_key()
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
                process = subprocess.Popen(["..\\network\\udp.exe", str(port_id)])
                current_number += 1
                with open("../network/current_players.txt", "w") as file:
                    file.write(str(current_number))
                sleep(2)
            except (FileNotFoundError, ValueError) as e:
                print(f"Error reading or updating current_players.txt: {e}")
                self.server_port = 8080
            PacketManager._initialized = True


    @staticmethod
    def process_packet(data) -> list:
        result = []
        # Remove trailing asterisk if only one message
        if data[-1] == '*':
            data = data[:-1]
            
        items = data.split('*')

        for item in items:
            if item.strip():  # Skip empty items
                parts = item.strip().split(';')
                # Check if first element is a number
                if parts and parts[0].isdigit():
                    result.append(parts)
                else:
                    result.append(['None'])
        print(result)
        return result
    
    @classmethod
    def create_map_packet(self, map):
        map_packet = map.map_encoding()
        return f"{0};map;{map_packet}"
        
    @classmethod
    def create_resource_map_packet(self, resource, x, y, type):
        resource_packet = f"{type};{resource.type};{x};{y};{resource.amount}"
        #print(resource_packet)
        
    @classmethod
    def create_unit_packet(self, unit, type):
        unit_packet = f"{unit.player.id};{type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.task};{unit.direction}"   
        return f"{unit_packet}*"

    @classmethod     
    def create_building_packet(self, building, type):
        building_packet = f"{building.player.id};{type};{building.name};{building.position[0]};{building.position[1]};{building.hp}"
        return f"{building_packet}*"

    @classmethod
    def create_current_state_packet(self, players):
        packet = ""
        for player in players:
            for unit in player.units:
                packet += self.create_unit_packet(unit, "current_unit")
            for building in player.buildings:
                packet += self.create_building_packet(building, "current_building")
        
        return packet

    def encrypt_message(self, message: str) -> str:
        """Chiffre un message avec AES en mode CFB et retourne une chaîne encodée en base64."""
        backend = default_backend()
        iv = os.urandom(16)  # Generate a random 16-byte IV
        cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CFB(iv), backend=backend)
        encryptor = cipher.encryptor()

        # Encrypt the message
        encrypted_message = encryptor.update(message.encode('utf-8')) + encryptor.finalize()

        # Prefix the IV and convert to base64
        encrypted_message_with_iv = iv + encrypted_message
        return base64.b64encode(encrypted_message_with_iv).decode('utf-8')  # Return as base64 string

    def decrypt_message(self, encrypted_message_base64: str) -> str:
        """Déchiffre un message avec AES en mode CFB à partir d'une chaîne base64."""
        backend = default_backend()

        # Decode the base64 message
        encrypted_message = base64.b64decode(encrypted_message_base64)

        # Extract the IV
        iv = encrypted_message[:16]
        encrypted_data = encrypted_message[16:]

        cipher = Cipher(algorithms.AES(SECRET_KEY), modes.CFB(iv), backend=backend)
        decryptor = cipher.decryptor()

        # Decrypt the message
        data = decryptor.update(encrypted_data) + decryptor.finalize()
        return data.decode('utf-8')  # Decode the decrypted message back to string
    
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
        """Chiffre et envoie un message au serveur."""
        self.socket.setblocking(False)
        passroom = GameRoomManager._room_password
        try:
            
            self.package += f";{passroom}"
            print(f"Message à chiffrer: {self.package}")
            encrypted_message = self.encrypt_message(self.package)
            #encrypted_message = self.package.encode("utf-8")
            self.socket.sendto(encrypted_message.encode('utf-8'), (SERVER_IP, self.server_port))
            print(f"Message chiffré envoyé au serveur")
        except socket.error as e:
            print(f"Erreur lors de l'envoi du message: {e}")
        self.package = ""

    def receive_packet(self, time_out = 0)-> str:
        """Reçoit et déchiffre un message du serveur."""
        try:
            self.socket.setblocking(False)  
        except socket.error as e:
            sys.exit(1)

        passroom = GameRoomManager._room_password

        while True:    
            readable, _, _ = select.select([self.socket], [], [], time_out)
            received_packets = None
            for sock in readable:
                if sock == self.socket:
                    
                    received_packets,_= self.socket.recvfrom(BUF)

                if received_packets:
                    try:
                        decrypted_message = self.decrypt_message(received_packets)
                        #decrypted_message = received_packets.decode("utf-8")
                        print(f"Message déchiffré: {decrypted_message}")
                        if decrypted_message.endswith(f";{passroom}"):
                            decrypted_message = decrypted_message[:-len(f";{passroom}")]
                        return decrypted_message
                    except Exception as e:
                        print(f"Erreur lors du déchiffrement : {e}")
                        return None
                    #if decrypted_message.endswith(f";{passroom}"):
                        decrypted_message = decrypted_message[:-len(f";{passroom}")]
                        
                        return decrypted_message
            return None
    
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
        return f"{self._instance.player.id};{target_player_id}"
    @classmethod
    def create_init_resource_response(self, requesting_player_id, resources):
        if self._instance.player.id == 0: 
            resource_values = [str(amount) for amount in resources.values()]
            resource_str = ";".join(resource_values)
            return f"{requesting_player_id};{resource_str}"
        return None

print(PacketManager.process_packet(';remove_unit;2.v.515;31.2;109.717*;remove_unit;2.v.515;31.2;109.717*'))
