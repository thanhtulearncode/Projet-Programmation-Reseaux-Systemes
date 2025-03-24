from time import sleep

class GameRoomManager:
    _instance = None
    _room_password = None  
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GameRoomManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, data_processor):
        if not hasattr(self, 'initialized'):
            self.data_processor = data_processor
            self.player_id = None
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
            number_of_players, game_mode, map_size_x, map_size_y, player_count, civilization, ai_mode, password = respond
            GameRoomManager._room_password = password
            map_size = (int(map_size_x), (int(map_size_y)))
            return GameRoom(
                number_of_players=int(number_of_players), 
                game_mode=game_mode, 
                map_size=map_size, 
                civilization=civilization, 
                ai_mode=ai_mode,
                password=password
            )
    
class GameRoom:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GameRoom, cls).__new__(cls)
        return cls._instance

    def __init__(self, number_of_players=None, game_mode=None, map_size=None, civilization=None, ai_mode=None, password=None):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.room_id = "1"
            self.number_of_players = number_of_players
            self.player_count = 0
            self.game_mode = game_mode
            self.map_size = map_size
            self.civilization = civilization
            self.ai_mode = ai_mode
            self.password = password
            self.players = []

    def verify_password(self, password):
        return password == GameRoomManager._room_password and self.player_count < self.number_of_players


