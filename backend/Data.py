import pickle #on peut utiliser json 
import socket
from backend import Game_Engine
"""
def send_unit_info_as_packet(unit, server_address):
    if unit.task:
        unit_info = {
            'player': unit.player.id,
            'position': unit.position,
            'task': unit.task,
            'target_resource': unit.target_resource,
            'target_position': unit.target_position,
            'carrying': unit.carrying,
            'direction': unit.direction,
            'is_moving': unit.is_moving,
            'last_gather_time': getattr(unit, 'last_gather_time', None),
            'last_move_time': getattr(unit, 'last_move_time', None),
            'path': getattr(unit, 'path', None),
            'target_attack': getattr(unit, 'target_attack', None),
            'last_hit_time': getattr(unit, 'last_hit_time', None),
            'construction_type': getattr(unit, 'construction_type', None),
            'target_building': getattr(unit, 'target_building', None),
            'start_building': getattr(unit, 'start_building', None)
        }
        packet = pickle.dumps(unit_info)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(server_address)
            s.sendall(packet)
        print(f"Unit information sent to server at {server_address}")
    else:
        print("Unit task is empty, no information sent.")
"""
# Test (parce qu'il n'y a pas de serveur)
def send_unit_info_as_packet(unit):
    if unit.task:
        unit_info = {
            'player_id' : unit.player.id,
            'unit_name': unit.name, #chỉ có mỗi dân làng mới có name nên ta có thể thêm thuộc tính (id) để xác minh unit?
            'position': unit.position,
            'task': unit.task,
            'target_resource': unit.target_resource,
            'target_position': unit.target_position,
            'carrying': unit.carrying,
            'direction': unit.direction,
            'is_moving': unit.is_moving,
            'last_gather_time': getattr(unit, 'last_gather_time', None),
            'last_move_time': getattr(unit, 'last_move_time', None),
            'path': getattr(unit, 'path', None),
            'target_attack': getattr(unit, 'target_attack', None),
            'last_hit_time': getattr(unit, 'last_hit_time', None),
            'construction_type': getattr(unit, 'construction_type', None),
            'target_building': getattr(unit, 'target_building', None),
            'start_building': getattr(unit, 'start_building', None)
        }
        #packet = pickle.dumps(unit_info)
        #print(packet)
        print(unit_info)

def process_received_packet(packet): #chưa xong
    unit_info = pickle.loads(packet.decode('utf-8'))
    player_id = unit_info.get('player_id')
    unit_name = unit_info.get('unit_name')
    for player in Game_Engine.game_data.players:
        if player.id == player_id:
            for unit in player.units:
                if unit.name == unit_name:
                    unit.position = unit_info.get('position')
                    unit.task = unit_info.get('task')
                    unit.target_resource = unit_info.get('target_resource')
                    unit.target_position = unit_info.get('target_position')
                    unit.carrying = unit_info.get('carrying')
                    unit.direction = unit_info.get('direction')
                    unit.is_moving = unit_info.get('is_moving')
                    unit.last_gather_time = unit_info.get('last_gather_time')
                    unit.last_move_time = unit_info.get('last_move_time')
                    unit.path = unit_info.get('path')
                    unit.target_attack = unit_info.get('target_attack')
                    unit.last_hit_time = unit_info.get('last_hit_time')
                    unit.construction_type = unit_info.get('construction_type')
                    unit.target_building = unit_info.get('target_building')
                    unit.start_building = unit_info.get('start_building')
                    print("Unit information updated from received packet.")
class Packet:
    def __init__(self, this_player):
        self.this_player = this_player
        self.package = None
    def send_packet(self, server_address):
        pass
    def receive_packet(self):
        pass

    def create_packet(self,object, update_type, amount=0, attaked_by=None):
        package_header = f"{self.this_player},update_type:{update_type},object_id:{object.id}position:{object.position}"
        match(update_type):
            case "place_unit":
                print(package_header)
            case "remove_unit":
                print(package_header)
            case "move_unit":
                print(package_header)
            case "place_building":
                print(package_header)
            case "remove_building":
                print(package_header)
        """ case "attacked":
                object_info = {
                    'player_id': object.player.id,
                    'unit_name': object.name,
                    'attacked_by': attaked_by.name,
                    'amount': amount
                }
                print(object_info)
            case "resource_gathered":
                object_info = {
                    'player_id': object.player.id,
                    'unit_name': object.name,
                    'amount': amount
                }
                print(object_info)
            case  "food_gathered":
                object_info = {
                    'player_id': object.player.id,
                    'unit_name': object.name,
                    'amount': amount
                }
                print(object_info) """

    def process_packet(player_id)-> list:
        pass

class DataProcessor:
    def __init__(self, game_engine: Game_Engine):
        self.game_engine = game_engine
    def update_data(player):
        pass