class DataProcessor:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, game_engine):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.game_engine = game_engine
    
    def initiate_sync(self):
        """
        ## Send a request to the server to initialize the engine
        PacketMamager().send_packet("initialize_engine_request")
        ## Wait for the server to respond with the corresonding civilisation, number of players and mode
        PacketMamager().receive()
        self.setup_engine()
        ## Send a request to the server to initialize the map, to r correct the current resources and units
        PacketMamager().send_packet("initialize_map_request")
        ## Wait for the server to respond with the resources
        PacketMamager().receive()
        self.update_data()
        ## Send a request to the server to initialize the units and buildings
        PacketMamager().send_packet("initialize_units_request")
        ## Wait for the server to respond with the units and buildings
        PacketMamager().receive()
        self.update_data()
        """
        pass

    def update_data(self):
        pass

    def setup_engine(self):
        pass
        ### GameEngine()

    