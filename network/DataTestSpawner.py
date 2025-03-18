import random

def spawner_test():
    start_x = random.randint(0, 10)
    start_y = random.randint(0, 10)
    
    update_types = ["place_unit", "remove_unit", "move_unit", "place_building", "remove_building"]
    update_type = random.choice(update_types)

    object_id = random.randint(0, 10)
    object_position = (start_x, start_y)
    
    package_header = f"{random.randint(0, 10)},update_type:{update_type},object_id:{object_id}position:{object_position}"
    return package_header

