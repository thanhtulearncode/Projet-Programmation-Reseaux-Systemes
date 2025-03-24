from time import sleep

class GameRoomManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GameRoomManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, data_processor):
        if not hasattr(self, 'initialized'):  # Ensure __init__ runs only once
            self.data_processor = data_processor
            self.player_id= None
            self.initialized = True

    def scan_rooms(self):
        packet_manager = self.data_processor.packet_manager
        packet_manager.package = f"1;scan_rooms"
        packet_manager.send_packet()
        sleep(0.05)
        respond = self.data_processor.update_data(True)
        print("The respond: ",respond)
        if not respond:
            return None
        else:
            number_of_players, game_mode, map_size_x, map_size_y, player_count, civilization, ai_mode = respond
            map_size = (int(map_size_x), int(map_size_y))
            gameroom = GameRoom(int(number_of_players), game_mode, map_size, civilization, ai_mode)
            gameroom.player_count = int(player_count)
            return gameroom
        
class GameRoom:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GameRoom, cls).__new__(cls)
        return cls._instance

    def __init__(self, number_of_players=None, game_mode=None, map_size=None, civilization=None, ai_mode=None):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.room_id = "1"
            self.number_of_players = number_of_players
            self.player_count = 0
            self.game_mode = game_mode
            self.map_size = map_size
            self.civilization = civilization
            self.ai_mode = ai_mode

# Create a global instance of GameRoom
