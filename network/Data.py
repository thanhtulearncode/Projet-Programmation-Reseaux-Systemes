import csv
import socket
import pickle
class PacketManager:
    def __init__(self, player):
        self.player = player
        self.package = ""
    def create_packet(self, object, update_type, amount=0, attaked_by=None):
        start_x = object.position[0]
        start_y = object.position[1]
        package_header = f"{self.player.id};{update_type};{object.id};{start_x};{start_y}"
        match(update_type):
            case "place_unit":
                self.package+=f"{package_header}\n"
                #print(package_header)
            case "remove_unit":
                self.package+=f"{package_header}\n"
                #print(package_header)
            case "place_building":
                self.package+=f"{package_header}\n"
                #print(package_header)
            case "remove_building":
                self.package+=f"{package_header}\n"
                #print(package_header)
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
                print(object_info) 
        if self.package:
            with open("spawner_test_output.csv", mode="a", newline="") as file:
                writer= csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL)
                writer.writerow(self.package.split(";"))"""

    def process_packet(player_id)-> list:
        pass

    def extract_package(self, row):
        package_header = f"{row[0]};{row[1]};{row[2]};{row[3]};{row[4]}"
        return package_header
    
    def process_csv(self, file_name):
        with open(file_name, mode="r") as file:
            reader = csv.reader(file, delimiter=';')
            next(reader)
            for row in reader:
                package_header = self.extract_package(row)
                print(package_header)