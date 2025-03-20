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
    
    def initiate_sync(self):
        
        ## Send a request to the server to initialize the engine
        self.packet_manager.send_packet("initialize_engine_request")
        ## Wait for the server to respond with the corresonding civilisation, number of players and mode
        self.packet_manager.receive()
        self.setup_engine()
        ## Send a request to the server to initialize the map, to r correct the current resources and units
        PacketManager().send_packet("initialize_map_request")
        ## Wait for the server to respond with the resources
        self.packet_manager.receive()
        self.update_data()
        ## Send a request to the server to initialize the units and buildings
        self.packet_manager.send_packet("initialize_units_request")
        ## Wait for the server to respond with the units and buildings
        self.packet_manager.receive()
        self.update_data()
        
        pass

    def update_data(self, init=False):
        packet =self.packet_manager.receive_packet()
        self.packet_manager.process_packet(packet)
        if not init:
            for row in packet:
                match row[1]:
                    case "place_unit"| "remove_unit" | "place_building" | "remove_building":
                        self.game_engine.update_map(row)


    def setup_engine(self):
        pass
        ### GameEngine()