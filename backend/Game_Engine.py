import curses
import time
import pickle
import os
import threading
import zlib
from queue import Queue

from frontend.gui import GUI
from logger import debug_print
from Units import *
from Building import *
from Actions import *
from frontend.Terrain import Map
from network.Data import PacketManager
from network.DataProcessor import DataProcessor
from network.Game_Room import *
from html_report import generate_html_report
from IA import IA

try:
    from frontend import gui
    USE_PYGAME = True
except ImportError:
    USE_PYGAME = False
    debug_print("Pygame not installed; running without 2.5D features.")

class GameEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GameEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self, game_mode, map_size, players, sauvegarde=False):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        self.game_mode = game_mode
        self.map_size = map_size
        self.players = players
        self.map = Map(*map_size)
        self.generated_map = False
        self.turn = 0
        self.is_paused = False
        self.changed_tiles = set()
        self.ias = [IA(p, p.ai_profile, self.map, time.time()) for p in players]
        for p, ia in zip(players, self.ias):
            p.ai = ia
        self.IA_used = False
        self.send_data = False
        self.packet_manager = PacketManager()
        self.data_processor = DataProcessor()
        self.data_processor.game_engine = self
        self.last_sent_state = None  # Store last sent state to reduce redundant updates
        
        if not sauvegarde:
            Building.place_starting_buildings(self.map)
            Unit.place_starting_units(self.players, self.map)
        
        self.debug_print = debug_print
        self.current_time = time.time()
        self.gui_running = False
        self.data_queue = Queue()
        self.gui_thread = None

    def get_current_time(self):
        """Retourne le temps actuel si le jeu n'est pas en pause"""
        if not self.is_paused:
            return time.time()
        return self.current_time
    
    def start_gui_thread(self):
        if not self.gui_thread:
            self.gui_thread = GUI(self.data_queue)
            self.gui_thread.start()
            self.gui_running = True

    def stop_gui_thread(self):
        if self.gui_thread:
            self.gui_thread = None
            self.gui_running = False

    def update_gui(self):
        if self.gui_running and not self.data_queue.full():
            self.data_queue.put(self)

    def load_map(self, map_packet):
        self.map.map_decoding(map_packet)

    def update_units(self, unit_info):
        #unit_packet = f"{type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.player.id};{unit.task};{unit.direction}"   
        type = unit_info[1]
        unit_name = unit_info[2]
        unit_position = int(float(unit_info[3])), int(float(unit_info[4]))
        unit_health = int(unit_info[5])
        player_id = int(unit_info[0])
        player = self.get_player_by_id(player_id)
        unit_task = unit_info[6]
        unit_direction = unit_info[7]
        if type == "spawn_unit" or type == "current_unit":
            unit_position = int(unit_position[0]), int(unit_position[1])
            if "Swordsman" in unit_name:
                unit = Swordsman(player)
                for u in player.units:
                    if u.name == unit_name:
                        player.units.remove(u)
                        u.player = None
                        self.map.remove_unit(int(u.position[0]), int(u.position[1]), u)
                player.units.append(unit)
                x, y = unit_position
                player.population = len(player.units)
                unit.hp = unit_health  
                unit.task = unit_task
                unit.direction = unit_direction
                self.map.place_unit(x, y, unit)
            elif "Archer" in unit_name:
                unit = Archer(player)
                for u in player.units:
                    if u.name == unit_name:
                        player.units.remove(u)
                        u.player = None
                        self.map.remove_unit(int(u.position[0]), int(u.position[1]), u)
                player.units.append(unit)
                x, y = unit_position
                player.population = len(player.units)
                unit.hp = unit_health  
                unit.task = unit_task
                unit.direction = unit_direction
                self.map.place_unit(x, y, unit)
            elif "Horseman" in unit_name:
                unit = Horseman(player, position = unit_position, name = unit_name)
                for u in player.units:
                    if u.name == unit_name:
                        player.units.remove(u)
                        u.player = None
                        self.map.remove_unit(int(u.position[0]), int(u.position[1]), u)
                player.units.append(unit)
                x, y = unit_position
                player.population = len(player.units)
                unit.hp = unit_health  
                unit.task = unit_task
                unit.direction = unit_direction
                self.map.place_unit(x, y, unit)
            else:
                #Unit.spawn_unit(Villager, unit_position[0], unit_position[1], player, self.map)
                unit = Villager(player, position = unit_position, name = unit_name)
                for u in player.units:
                    if u.name == unit_name:
                        player.units.remove(u)
                        u.player = None
                        self.map.remove_unit(int(u.position[0]), int(u.position[1]), u)
                player.units.append(unit)
                x, y = unit_position
                player.population = len(player.units)
                unit.hp = unit_health  
                unit.task = unit_task
                unit.direction = unit_direction
                self.map.place_unit(x, y, unit)

        elif type == "place_unit":
            for unit in player.units:
                if unit.name == unit_name:
                    unit.position = unit_position
                    unit.hp = unit_health  
                    unit.task = unit_task
                    unit.direction = unit_direction
                    self.map.place_unit(int(unit_position[0]), int(unit_position[1]), unit)
                    break

        elif type == "remove_unit":
            print("Huy dep trai1")
            for unit in player.units:
                print(unit.name)
                print(unit_name)
                if unit.name == unit_name:
                    print("Huy dep trai2")
                    self.map.remove_unit(int(unit_position[0]), int(unit_position[1]), unit)
                    print("Huy dep trai3")
                    break
        elif type == "kill_unit":
            for unit in player.units:
                if unit.name == unit_name:
                    Unit.kill_unit(player, unit, self.map)
            
    def update_buildings(self, building_info):
        #building_packet = f"{type};{building.name};{building.position[0]};{building.position[1]};{building.hp};{building.player.id}"
        type = building_info[1]
        building_name = building_info[2]
        building_position = int(float(building_info[3])), int(float(building_info[4]))
        building_hp = int(building_info[5])
        player_id = int(building_info[0])
        player = self.get_player_by_id(player_id)
        if type == "spawn_building" or type == "current_building":
            building_position = int(building_position[0]), int(building_position[1])
            if building_name == "Town Center":
                Building.spawn_building(player, building_position[0], building_position[1], TownCenter, self.map)
            elif building_name == "Barracks":
                Building.spawn_building(player, building_position[0], building_position[1], Barracks, self.map)
            elif building_name == "Stable":
                Building.spawn_building(player, building_position[0], building_position[1], Stable, self.map)
            elif building_name == "ArcheryRange":
                Building.spawn_building(player, building_position[0], building_position[1], ArcheryRange, self.map)
            elif building_name == "Keep":
                Building.spawn_building(player, building_position[0], building_position[1], Keep, self.map)
            elif building_name == "Farm":
                Building.spawn_building(player, building_position[0], building_position[1], Farm, self.map)
            elif building_name == "House":
                Building.spawn_building(player, building_position[0], building_position[1], House, self.map)
            elif building_name == "Camp":
                Building.spawn_building(player, building_position[0], building_position[1], Camp, self.map)
            else: 
                return
        elif type == "kill_building":
            for building in player.buildings:
                if building.position == building_position:
                    break
                Building.kill_building(player, building, self.map)
    
    def update_game(self, packet):
        if packet[1] and "unit" in packet[1]:
            self.update_units(packet)
        elif packet[1] and "building" in packet[1]:
            self.update_buildings(packet)

    def run_multi_player(self, stdscr, this_player_id):
        terminal_height, terminal_width = stdscr.getmaxyx()
        viewport_width, viewport_height = min(30, terminal_width // 2), min(30, terminal_height - 1)
        top_left_x, top_left_y = 0, 0
        stdscr.clear()

        try:
            while not self.check_victory():
                start_time = time.time()
                if not self.is_paused:
                    self.current_time = time.time()
                
                request = self.data_processor.update_data()
                if request and request[1] == "scan_rooms":
                    gr= GameRoom()
                    self.packet_manager.package =  f"{gr.number_of_players};{gr.game_mode};{gr.map_size[0]};{gr.map_size[1]};{gr.player_count};{gr.civilization};{gr.ai_mode}"
                    self.packet_manager.send_packet()
                elif request:
                    self.packet_manager.package = PacketManager().create_map_packet(self.map)
                    self.packet_manager.map = PacketManager().package
                    self.packet_manager.send_packet()
                self.sync_game_state()
                
                curses.curs_set(0)
                stdscr.nodelay(True)
                key = stdscr.getch()
                action = Action(self.map)

                if key == curses.KEY_UP or key == ord('z'):
                    top_left_y = max(0, top_left_y - 1)
                elif key == curses.KEY_DOWN or key == ord('s'):
                    top_left_y = min(self.map.height - viewport_height, top_left_y + 1)
                elif key == curses.KEY_LEFT or key == ord('q'):
                    top_left_x = max(0, top_left_x - 1)
                elif key == curses.KEY_RIGHT or key == ord('d'):
                    top_left_x = min(self.map.width - viewport_width, top_left_x + 1)
                elif key == ord('Z'):
                    top_left_y = max(0, top_left_y - 5)
                elif key == ord('S'):
                    top_left_y = min(self.map.height - viewport_height, top_left_y + 5)
                elif key == ord('Q'):
                    top_left_x = max(0, top_left_x - 5)
                elif key == ord('D'):   
                    top_left_x = min(self.map.width - viewport_width, top_left_x + 5)

                ###### TEST KEYS #######
                elif key == ord('r'):
                    """
                    for player in self.players:
                        print(player.package.map)
                        print(player.package.package)
                        player.package.map=""
                        player.package.package=""
                    """
                    Building.place_starting_buildings(self.map)   # Place starting town centers on the map
                    Unit.place_starting_units(self.players, self.map)  # Place starting units on the map
                elif key == ord('t'):
                    self.update_units("spawn_unit;Villager;25;105;25;1;None;south")
                elif key == ord('y'):
                    self.update_units("remove_unit;Villager;25;105;25;1;going_to_construction_site;southwest")
                    self.update_units("place_unit;Villager;24;106;25;1;going_to_construction_site;southwest")
                    self.update_units("remove_unit;Villager;24;106;25;1;going_to_construction_site;southwest")
                    self.update_units("place_unit;Villager;23;107;25;1;going_to_construction_site;southwest")
                    print("yes")
                elif key == ord('u'):
                    packets = "0;current_unit;Pauline;114;59;25;None;south*0;current_unit;Valentine;110;63;25;None;south*0;current_unit;Theophile;108;60;25;None;south*0;current_building;Town Center;114;60;1000*1;current_unit;Cecile;34;101;25;None;south*1;current_unit;Bill;34;101;25;None;south*1;current_unit;Lise;36;100;25;None;south*1;current_building;Town Center;34;106;1000*2;current_unit;Arielle;32;6;25;None;south*2;current_unit;Reinhard;31;13;25;None;south*2;current_unit;Lina;30;12;25;None;south*2;current_building;Town Center;34;12;1000*"
                    #packets += "\nplace_unit;Fran?ois/François;38;99;25;2\nremove_unit;Fran?ois/François;37.55806095915671;99.44193904084328;25;2\nplace_unit;Fran?ois/François;37.55806095915671;99.44193904084328;25;2\nremove_unit;Fran?ois/François;37;100;25;2\nplace_unit;Fran?ois/François;37;100;25;2\nremove_unit;Fran?ois/François;36.396691802976505;100.6033081970235;25;2\nplace_unit;Fran?ois/François;36.396691802976505;100.6033081970235;25;2\nspawn_building;House;43;107;200;2\nremove_unit;Fran?ois/François;36;101;25;2\nplace_unit;Fran?ois/François;36;101;25;2\nremove_unit;Fran?ois/François;35.46968474980076;101.53031525019924;25;2\nplace_unit;Fran?ois/François;35.46968474980076;101.53031525019924;25;2\nremove_unit;Fran?ois/François;35.02551900665695;101.97448099334305;25;2\nplace_unit;Fran?ois/François;35.02551900665695;101.97448099334305;25;2\nremove_unit;Fran?ois/François;35;102;25;2\nplace_unit;Fran?ois/François;35;102;25;2\nremove_unit;Fran?ois/François;35.0;102.75311470031738;25;2\nplace_unit;Fran?ois/François;35.0;102.75311470031738;25;2\nremove_unit;Fran?ois/François;35;103;25;2\nplace_unit;Fran?ois/François;35;103;25;2\nremove_unit;Fran?ois/François;35.0;103.75312232971191;25;2\nplace_unit;Fran?ois/François;35.0;103.75312232971191;25;2\nremove_unit;Fran?ois/François;35;104;25;2\nplace_unit;Fran?ois/François;35;104;25;2\nremove_unit;Fran?ois/François;35.0;104.6281566619873;25;2\nplace_unit;Fran?ois/François;35.0;104.6281566619873;25;2\nremove_unit;Fran?ois/François;35;105;25;2\nplace_unit;Fran?ois/François;35;105;25;2\nremove_unit;Fran?ois/François;35.0;105.62820434570312;25;2\nplace_unit;Fran?ois/François;35.0;105.62820434570312;25;2\nremove_unit;Fran?ois/François;35;106;25;2\nplace_unit;Fran?ois/François;35;106;25;2"
                    packets = packets.split("*")
                    for packet in packets:
                        packet = packet.split(";")
                        self.update_game(packet)

                    for player in self.players:
                        for unit in player.units:
                            print(unit.name)
                            print(unit.position)

                elif key == ord('i'):
                    for player in self.players:
                        print(player.id)
                        for unit in player.units:
                            print(unit.name)
                            print(unit.position)
                    
                elif key == ord('o'):
                    self.send_data = not self.send_data
                elif key == ord('i'):  # Add AI mode switching
                    # Get current player's AI
                    current_player = self.get_player_by_id(this_player_id)
                    if current_player and current_player.ai:
                        # Toggle between aggressive and defensive
                        if current_player.ai_profile == "aggressive":
                            current_player.ai_profile = "defensive"
                        else:
                            current_player.ai_profile = "aggressive"
                        # Update the AI instance
                        current_player.ai = IA(current_player, current_player.ai_profile, self.map, time.time())
                        self.debug_print(f"AI mode changed to: {current_player.ai_profile}")
                        print(f"AI mode changed to: {current_player.ai_profile}")

                #########################

                ###### CHEAT KEYS #######
                elif key == ord('g'):
                    self.players[0].owned_resources["Gold"] += 5000
                elif key == ord('w'):
                    self.players[0].owned_resources["Wood"] += 5000
                elif key == ord('f'):
                    self.players[0].owned_resources["Food"] += 5000
                elif key == ord('h'):
                    for player in self.players:
                        player.owned_resources["Gold"] = 0
                        player.owned_resources["Wood"] = 0
                        player.owned_resources["Food"] = 0

                #########################


                elif key == curses.KEY_F9:
                    if not self.gui_running:
                        self.start_gui_thread()
                    else:
                        self.stop_gui_thread()
                        stdscr.clear()
                        stdscr.refresh()
                        continue
                elif key == ord('\t'):  # TAB key
                    generate_html_report(self.players)
                    self.debug_print(f"HTML report generated at turn {self.turn}")
                    if self.is_paused == False:
                        self.is_paused = True
                        self.debug_print("Game paused.")
                elif key == ord('p'):
                    self.is_paused = not self.is_paused
                    if self.is_paused:
                        self.debug_print("Game paused.")
                    else:
                        self.debug_print("Game resumed.")

                elif key == ord('n'):
                    self.IA_used = not self.IA_used
                    self.debug_print(f"IA used: {self.IA_used}")

                elif key == curses.KEY_F10: 
                    self.save_game()
                elif key == curses.KEY_F12:
                    # Find the latest save file in the directory
                    save_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'annex')
                    save_files = [f for f in os.listdir(save_dir) if f.endswith('.dat')]
                    if save_files:
                        latest_save_file = max(save_files, key=lambda f: os.path.getctime(os.path.join(save_dir, f)))
                        latest_save_path = os.path.join(save_dir, latest_save_file)
                        self.load_game(latest_save_path)
                    else:
                        self.debug_print("No save files found.") 
                
                if not self.is_paused and self.turn % 200 == 0 and self.IA_used:
                    ia = self.get_ai_by_id(this_player_id)
                    if ia:
                        ia.run()

                if not self.is_paused and self.turn % 10 == 0:
                    self.process_unit_actions(this_player_id, action)
                
                stdscr.clear()
                self.map.display_viewport(stdscr, top_left_x, top_left_y, viewport_width, viewport_height, self.is_paused)
                stdscr.refresh()
                if self.gui_running:
                    self.update_gui()
                self.turn += 1
                
                # Ensure stable loop time
                elapsed_time = time.time() - start_time
                time.sleep(max(0.05 - elapsed_time, 0))
        except KeyboardInterrupt:
            self.debug_print("Game interrupted. Exiting...", 'Yellow')
        finally:
            if self.gui_running:
                self.stop_gui_thread()

    def sync_game_state(self):
        current_state = self.packet_manager.create_current_state_packet(self.players)
        if current_state != self.last_sent_state:
            self.packet_manager.package = current_state
            self.packet_manager.send_packet()
            self.last_sent_state = current_state

    def process_unit_actions(self, player_id, action):
        player = self.get_player_by_id(player_id)
        if player:
            for unit in player.units:
                if unit.task == "going_to_battle":
                    action.go_battle(unit, unit.target_attack, self.current_time)
                elif unit.task == "attacking":
                    action._attack(unit, unit.target_attack, self.current_time)
                elif unit.target_position:
                    action.move_unit(unit, *unit.target_position, self.current_time)
                elif unit.task == "gathering" or unit.task == "returning":
                    action._gather(unit, unit.last_gathered, self.get_current_time())
                elif unit.task == "marching":
                    action.gather_resources(unit, unit.last_gathered, self.get_current_time())
                elif unit.task == "is_attacked":
                    action._attack(unit, unit.is_attacked_by, self.get_current_time())
                elif unit.task == "going_to_construction_site":
                    action.construct_building(unit, unit.construction_type, unit.target_building[0], unit.target_building[1], player, self.get_current_time())
                elif unit.task == "constructing":
                    action._construct(unit, unit.construction_type, unit.target_building[0], unit.target_building[1], player, self.get_current_time())

    def check_victory(self):
        active_players = [p for p in self.players if p.units or p.buildings]
        return len(active_players) == 1

    def get_ai_by_id(self, player_id):
        return next((p.ai for p in self.players if p.id == player_id), None)

    def get_player_by_id(self, player_id):
        return next((p for p in self.players if p.id == player_id), None)

    def save_game(self, filename=None):
        filename = filename or f"../assets/annex/game_save{self.turn % 10}.dat"
        try:
            with open(filename, 'wb') as f:
                pickle.dump({'players': self.players, 'map': self.map, 'turn': self.turn}, f)
            self.debug_print(f"Game saved to {filename}.")
        except Exception as e:
            self.debug_print(f"Error saving game: {e}")

    def load_latest_save(self):
        save_dir = os.path.join(os.path.dirname(__file__), '..', 'assets', 'annex')
        save_files = [f for f in os.listdir(save_dir) if f.endswith('.dat')]
        if save_files:
            latest_save = max(save_files, key=lambda f: os.path.getctime(os.path.join(save_dir, f)))
            self.load_game(os.path.join(save_dir, latest_save))
        else:
            self.debug_print("No save files found.")

    def load_game(self, filename):
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                self.players, self.map, self.turn = data['players'], data['map'], data['turn']
            self.debug_print(f"Game loaded from {filename}.")
        except Exception as e:
            self.debug_print(f"Error loading game: {e}")
