import random
import csv
import string
import time

def spawner_test():
    player_id = random.randint(0, 10)
    start_x = str(random.randint(0, 10))
    start_y = str(random.randint(0, 10))
    update_types = ["place_unit", "remove_unit", "move_unit", "place_building", "remove_building"]
    update_type = random.choice(update_types)
    symbols = ["v", "s", "h", "a", "T", "H", "C", "F", "B", "S", "A", "K"]
    object_id = f"{player_id}.{random.choice(symbols)}.{random.randint(0, 100)}"
    object_position = f"{start_x};{start_y}"
    package_header = f"{player_id};{update_type};{object_id};{start_x};{start_y}"
    return package_header

class Spawner:
    def __init__(self):
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

spawner = Spawner()
spawner.process_csv("spawner_test_output.csv")

print(spawner_test())

print(time.time())
