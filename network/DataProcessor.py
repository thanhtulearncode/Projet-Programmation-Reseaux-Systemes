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
    
    def processing(self):
        from network.Game_Room import Game_Room
        received_packets = []
        if self.game_engine and self.game_engine.generated_map:
            packet= self.packet_manager.process_packet(self.packet_manager.package)
            received_packets.extend(packet)
            self.packet_manager.send_packet()
        number_received_packages = 1
        timeout_counter = 0
        while number_received_packages <= Game_Room.number_players and timeout_counter < 100:

            received = self.packet_manager.receive_packet()
            if received:
                packet= self.packet_manager.process_packet(packet)
                if (packet[0][1] == "scan_rooms"):
                    gr = Game_Room()
                    PacketManager().package =  f"{gr.number_of_players};{gr.game_mode};{gr.map_size[0]};{gr.map_size[1]};{gr.player_count};{gr.civilization};{gr.ai_mode}"
                    PacketManager().send_packet()
                if not self.game_engine and (packet[0][1] == "Utopia" or packet[0][1] == "Gold Rush"):
                    return packet[0]
                    
                if self.game_engine and not self.game_engine.generated_map:

                number_received_packages += 1
                
                received_packets.extend(packet)
            timeout_counter += 1
        sorted_packets = sorted(received_packets, key=lambda x: x[0])
        done = []
        for packet in sorted_packets:
            """unit_packet = f"{current_time_call};{unit.player.id};{type};{target.position[0]};{target.position[1]};"
        unit_packet += f"{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.task};{unit.direction};"   
        self.package += f"{unit_packet}*"""""
            packet1 = packet.strip().split(';')
            type_update, x, y = packet1[2], packet[3], packet[4]
            if type_update not in done:
                self.game_engine.package += f"{packet}*"
                done.append((type_update, x, y))


    def update_data(self, wait = False):
        if not wait:
            packet =self.packet_manager.receive_packet()
        else:
            packet = self.packet_manager.receive_packet(3)
        print("Received: ",packet)

        if packet:
            packet= self.packet_manager.process_packet(packet)
            print ("Processed: ",packet)
            for row in [row for row in packet if len(row) > 1]:
                print(row)
                match row[1]:
                    case "place_unit"| "remove_unit" | "spawn_unit" | "kill_unit" | "spawn_building" | "kill_building" | "current_unit" | "current_building":
                        self.game_engine.update_game(row)
                    case "map":
                        if not self.game_engine.generated_map:
                            self.game_engine.load_map(row[2])
                            self.game_engine.generated_map = True
                    case default:
                        if not self.packet_manager.player or self.packet_manager.player.id == 0:
                            return row
            return None

    def setup_engine(self):
        pass
        ### GameEngine()