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
            self.socket = None
            self.server_address = "127.0.0.1"
            self.server_port = 8081
            self.resources_map = ""
            PacketManager._initialized = True
        
    def create_packet(self, object, update_type, amount=0, attacked_by=None):
        pass
        """start_x = object.position[0]
        start_y = object.position[1]
        PacketManager.package_header = f"{self.player.id};{update_type};{object.id};{start_x};{start_y}"
        
        match update_type:
            case "place_unit" | "remove_unit" | "place_building" | "remove_building":
                self.package += f"{PacketManager.package_header}\n"
        case "attacked":
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
        #print(map_packet)
        self.map = map_packet
    @classmethod
    def create_resource_map_packet(self, resource, x, y, type):
        resource_packet = f"{type};{resource.type};{x};{y};{resource.amount}"
        print(resource_packet)
        

    
    @classmethod
    def create_unit_packet(self, unit, type):
        unit_packet = f"{type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.player.id}"
        unit.player.package.package += f"{unit_packet}\n"
        #print(unit_packet) += f"{resource_packet}\n"
    
    @classmethod
    def create_building_packet(self, building, type):
        building_packet = f"{type};{building.name};{building.position[0]};{building.position[1]};{building.hp};{building.player.id}"
        building.player.package.package += f"{building_packet}\n"
        #print(building_packet)
                
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
        try:
            self.socket.sendto(self.package.encode(), (self.server_address, self.server_port))
            self.package = ""
        except Exception as e:
            pass
        pass
        
    def receive_packet(self)-> str:
        pass

print(PacketManager.process_packet('2;remove_unit;2.v.515;31.2;109.717*2;place_unit;2.v.516;31.28;109.7*2;remove_unit;2.v.516;31.56;109.43*2;place_unit;2.v.517;31.56476911874513;109.43523088125487*2;remove_unit;2.v.517;31.85568622330503;109.14431377669497'))
