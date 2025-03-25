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
            self.number_received_packages = 0
            self.packet_manager = PacketManager()
    
    def processing(self):
        from network.Game_Room import GameRoom, GameRoomManager
        received_packets = []
        ## Case: a player in the game room process the packages after recording all of its packets and about to capture all other players' packets
        if self.game_engine and self.game_engine.generated_map:
            packet= self.packet_manager.process_packet(self.packet_manager.package)
            received_packets.extend(packet)
            self.packet_manager.send_packet()
            self.number_received_packages = 0
        else:
            ## Case: Not in the game room need to filter out the right packets
            import time
            time.sleep(3) ## ADJUST

        timeout_counter = 0
        while timeout_counter < 50: ## ADJUST

            received = self.packet_manager.receive_packet()
            if received:
                packet = self.packet_manager.process_packet(received)
                match packet[0][1]:
                    ## Case: the admin player in the game room treat the scan_rooms request
                    case "scan_rooms" if GameRoomManager().player_id == 0:
                        gr = GameRoom()
                        PacketManager().package = f"{gr.number_of_players};{gr.game_mode};{gr.map_size[0]};{gr.map_size[1]};{gr.player_count};{gr.civilization};{gr.ai_mode}"
                        PacketManager().send_packet()
                    ## Case: the new player treat the scan_rooms response from the admin player
                    case "Utopia" | "Gold Rush" if not self.game_engine:
                        return packet[0] ## Escape the function since the new don't treat other packets
                    ## Case: the admin player in the game room treat the map,unit and building requests
                    case "map_request" if GameRoomManager().player_id == 0:
                        PacketManager().package = PacketManager().create_map_packet(self.game_engine.map)
                        ## somehow send the units and buildings ##DONE
                        PacketManager().pakage += PacketManager().create_current_state_packet(self.game_engine.players, self.game_engine.map)
                        PacketManager().send_packet() 
                    ## Case: the new player treat the map,unit and building responses from the admin player
                    case "map" if self.game_engine and not self.game_engine.generated_map:
                        self.game_engine.load_map(packet[0][2])
                        ## somehow treat all the units and buildings ##DONE
                        for i in range(1, len(packet)):
                            self.game_engine.load_current_state(packet[i])
                        return None ## Escape the function to join the game
                    case _ :
                        if self.number_received_packages < GameRoom().number_of_players:
                            received_packets.extend(packet)
                            self.number_received_packages += 1
                            if self.number_received_packages >= GameRoom().number_of_players:
                                break
                timeout_counter += 1
            else:
                time.sleep(1)   

                
        sorted_packets = sorted(received_packets, key=lambda x: x[0])
        done = []
        new_packets = []
        for packet in sorted_packets:
            """unit_packet = f"{current_time_call};{unit.player.id};{type};{target.position[0]};{target.position[1]};"
        unit_packet += f"{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.task};{unit.direction};"   
        self.package += f"{unit_packet}*"""""
            ## TODO: treat the packets and conflict resolution
            ## Here sort_packets is a list of packets sorted by the current_time_call: 
            ## [[time_call, arg1, arg2,...], [time_call, arg1, arg2,...], [time_call, arg1, arg2,...], ...]
            ## Previously: timecall;arg1;arg2,...*timecall;arg1;arg2,...*timecall;arg1;arg2,...*...
            player_id, type_update, x, y = packet[1], packet[2], packet[3], packet[4]
            found = next((d for d in done if (d[1], d[2], d[3]) == (type_update, x, y)), None)
            if not found:
                new_packets.append(packet)
                done.append((player_id, type_update, x, y))
            elif found[0] == player_id:  
                new_packets.append(packet)
        
        for packet in new_packets:
            self.game_engine.update_game(packet)

    """
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

    """