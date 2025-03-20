import csv
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
            PacketManager._initialized = True
    
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
