from network.Data import PacketManager

class DataProcessor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.game_engine = None
            self.packet_manager = PacketManager()
    
    def update_data(self, wait=False):
        packet = self.packet_manager.receive_packet(3 if wait else 0)
        if not packet:
            return None
        
        print("Received:", packet)
        packet = self.packet_manager.process_packet(packet)
        print("Processed:", packet)
        
        for row in filter(lambda r: len(r) > 1, packet):
            print(row)
            if row[1] in {"place_unit", "remove_unit", "spawn_unit", "kill_unit", "spawn_building", "kill_building", "current_unit", "current_building"}:
                self.game_engine.update_game(row)
            elif row[1] == "map" and not self.game_engine.generated_map:
                self.game_engine.load_map(row[2])
                self.game_engine.generated_map = True
            elif not self.packet_manager.player or self.packet_manager.player.id == 0:
                return row
        return None

    def setup_engine(self):
        pass