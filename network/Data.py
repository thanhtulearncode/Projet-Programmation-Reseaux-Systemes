import csv

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
    
    def __init__(self, player):
        if not PacketManager._initialized:
            self.player = player
            self.package = ""
            PacketManager._initialized = True
        
    def create_packet(self, object, update_type, amount=0, attacked_by=None):
        start_x = object.position[0]
        start_y = object.position[1]
        PacketManager.package_header = f"{self.player.id};{update_type};{object.id};{start_x};{start_y}"
        
        match update_type:
            case "place_unit" | "remove_unit" | "place_building" | "remove_building":
                self.package += f"{PacketManager.package_header}\n"
        """case "attacked":
                object_info = {
                    'player_id': object.player.id,
                    'unit_name': object.name,
                    'attacked_by': attacked_by.name if attacked_by else None,
                    'amount': amount
                }
                print(object_info)
            case "resource_gathered" | "food_gathered":
                object_info = {
                    'player_id': object.player.id,
                    'unit_name': object.name,
                    'amount': amount
                }
                print(object_info)"""
        
        if self.package:
            with open("spawner_test_output.csv", mode="a", newline="") as file:
                writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL)
                writer.writerow(self.package.strip().split(";"))
                
    @staticmethod
    def process_packet(data) -> list:
        result = []
        items = data.split('*')
    
        for item in items:
            if item.strip():  # Skip empty items
                result.append(item.strip().split(';'))
    
        return result
        
    def extract_package(self, row):
        PacketManager.package_header = f"{row[0]};{row[1]};{row[2]};{row[3]};{row[4]}"
        return PacketManager.package_header
        
    def process_csv(self, file_name):
        with open(file_name, mode="r") as file:
            reader = csv.reader(file, delimiter=';')
            next(reader, None) 
            for row in reader:
                package_header = self.extract_package(row)
                print(package_header)
                
    #send self.package to the server
    def send_packet(self):
        pass
        
    def receive_packet(self)-> str:
        pass

    def create_init_resource_request(self, target_player_id=0):
        return f"init_resource_request;{self.player.id};{target_player_id}"

    def create_init_resource_response(self, requesting_player_id, resources):
        if self.player.id == 0: 
            resource_values = [str(amount) for amount in resources.values()]
            resource_str = ";".join(resource_values)
            return f"{requesting_player_id}\n{requesting_player_id};{resource_str}"
        return None
import csv

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
    
    def __init__(self, player):
        if not PacketManager._initialized:
            self.player = player
            self.package = ""
            PacketManager._initialized = True
        
    def create_packet(self, object, update_type, amount=0, attacked_by=None):
        start_x = object.position[0]
        start_y = object.position[1]
        PacketManager.package_header = f"{self.player.id};{update_type};{object.id};{start_x};{start_y}"
        
        match update_type:
            case "place_unit" | "remove_unit" | "place_building" | "remove_building":
                self.package += f"{PacketManager.package_header}\n"
        """case "attacked":
                object_info = {
                    'player_id': object.player.id,
                    'unit_name': object.name,
                    'attacked_by': attacked_by.name if attacked_by else None,
                    'amount': amount
                }
                print(object_info)
            case "resource_gathered" | "food_gathered":
                object_info = {
                    'player_id': object.player.id,
                    'unit_name': object.name,
                    'amount': amount
                }
                print(object_info)"""
        
        if self.package:
            with open("spawner_test_output.csv", mode="a", newline="") as file:
                writer = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL)
                writer.writerow(self.package.strip().split(";"))
                
    @staticmethod
    def process_packet(data) -> list:
        result = []
        items = data.split('*')
    
        for item in items:
            if item.strip():  # Skip empty items
                result.append(item.strip().split(';'))
    
        return result
        
    def extract_package(self, row):
        PacketManager.package_header = f"{row[0]};{row[1]};{row[2]};{row[3]};{row[4]}"
        return PacketManager.package_header
        
    def process_csv(self, file_name):
        with open(file_name, mode="r") as file:
            reader = csv.reader(file, delimiter=';')
            next(reader, None) 
            for row in reader:
                package_header = self.extract_package(row)
                print(package_header)
                
    #send self.package to the server
    def send_packet(self):
        pass
        
    def receive_packet(self)-> str:
        pass

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

    def create_init_resource_request(self, target_player_id=0):
        return f"{self.player.id};{target_player_id}"

    def create_init_resource_response(self, requesting_player_id, resources):
        if self.player.id == 0: 
            resource_values = [str(amount) for amount in resources.values()]
            resource_str = ";".join(resource_values)
            return f"{requesting_player_id};{resource_str}"
        return None

print(PacketManager.process_packet('2;remove_unit;2.v.515;31.2;109.717*2;place_unit;2.v.516;31.28;109.7*2;remove_unit;2.v.516;31.56;109.43*2;place_unit;2.v.517;31.56476911874513;109.43523088125487*2;remove_unit;2.v.517;31.85568622330503;109.14431377669497'))
