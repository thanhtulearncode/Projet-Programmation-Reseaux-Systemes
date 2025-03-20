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
        packet_manager.pakage = f"1;scan_rooms"
        packet_manager.send_packet()
        respond= packet_manager.update_data()
        if not respond:
            return None
        else:
            number_of_players, game_mode, map_size_x, map_size_y, player_count, civilisation, ai_mode = respond
            map_size = (map_size_x, map_size_y)
            gameroom = GameRoom(int(number_of_players), game_mode, map_size, civilisation, ai_mode)
            gameroom.player_count = player_count
            return gameroom
        
class GameRoom:
    def __init__(self, number_of_players, game_mode, map_size, civilisation, ai_mode):
        self.room_id = "1"
        self.number_of_players = number_of_players
        self.player_count = 0
        self.game_mode = game_mode
        self.map_size = map_size
        self.civilisation = civilisation
        self.ai_mode = ai_mode
        