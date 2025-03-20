import csv
import socket
import select
import sys

BUF = 512
SERVER_IP = "127.0.0.1"
class PacketManager:
    _instance = None 
    package_header = ""   
    _initialized = False  
    def __new__(cls, player):
        if cls._instance is None:
            cls._instance = super(PacketManager, cls).__new__(cls)
            cls._instance.player = player
            cls._instance.package = ""
        return cls._instance
    
    def __init__(self, player, socket):
        if not PacketManager._initialized:
            self.player = player
            self.package = ""
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_address = ("127.0.0.1")
            self.server_port = 8080 + self.player.id
            PacketManager._initialized = True

    @classmethod
    def create_unit_packet(self, unit, type):
        unit_packet = f"{type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.player.id}"
        unit.player.package.package += f"{unit_packet}\n"
        print(unit_packet)
                
    @staticmethod
    def process_packet(data) -> list:
        result = []
        items = data.split('\n')
    
        for item in items:
            if item.strip():  # Skip empty items
                result.append(item.strip().split(';'))
    
        return result
        
        writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writerow(self.package.strip().split(";"))
    
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
                
    @staticmethod
    def process_packet(data) -> list:
        result = []
        items = data.split('\n')
    
        for item in items:
            if item.strip():  # Skip empty items
                result.append(item.strip().split(';'))
    
        return result
        
    def extract_package(self, row):
        PacketManager.package_header = f"{row[0]};{row[1]};{row[2]};{row[3]};{row[4]}"
        return PacketManager.package_header
        
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
        self.socket.setblocking(False) 
        try:
            self.socket.setblocking(False)  
        except socket.error as e:
            sys.exit(1)

        while True:    
            readable, _, _ = select.select([self.socket], [], [])

            for sock in readable:
                if sock == self.socket:
                    
                    received_packets, server_address = self.socket.recvfrom(BUF)

            return received_packets.decode('utf-8')
    


print(PacketManager.process_packet('2;remove_unit;2.v.515;31.2;109.717*2;place_unit;2.v.516;31.28;109.7*2;remove_unit;2.v.516;31.56;109.43*2;place_unit;2.v.517;31.56476911874513;109.43523088125487*2;remove_unit;2.v.517;31.85568622330503;109.14431377669497'))
