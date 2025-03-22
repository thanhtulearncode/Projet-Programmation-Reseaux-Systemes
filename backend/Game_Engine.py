import curses
import time
import pickle
import os
import tkinter as tk

from queue import Queue
from frontend.gui import GUI

from logger import debug_print
from Units import *
from Building import *
from Actions import *
from frontend.Terrain import Map
from network.Data import *
from network.DataProcessor import DataProcessor
try:
    from frontend import gui
    USE_PYGAME = True
except ImportError:
    USE_PYGAME = False
    debug_print("Pygame not installed; running without Pygame features such as 2.5D map view.")

from html_report import generate_html_report

from IA import IA

# GameEngine Class
class GameEngine:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GameEngine, cls).__new__(cls)
        return cls._instance

    def __init__(self, game_mode, map_size, players, sauvegarde=False):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True

        self.game_mode = game_mode
        self.map_size = map_size
        self.players = players
        self.map = Map(*map_size)  # Create a map object
        self.turn = 0
        self.is_paused = False  # Flag to track if the game is paused
        self.changed_tiles = set()  # Set to track changed tiles
        
        # IA related attributes
        self.ias = [IA(player, player.ai_profile, self.map, time.time()) for player in self.players]  # Instantiate IA for each player
        for i in range(len(self.players)):
            self.players[i].ai = self.ias[i]
        self.IA_used = False
        self.send_data = True

        # Sauvegarde related attributes
        if not sauvegarde:
            pass
            #Building.place_starting_buildings(self.map)   # Place starting town centers on the map
            #Unit.place_starting_units(self.players, self.map)  # Place starting units on the map
        
        self.debug_print = debug_print
        self.current_time = time.time()

        self.terminalon = True

        # GUI thread related attributes
        self.gui_running = False
        self.data_queue = Queue()
        self.gui_thread = None

    def start_gui_thread(self):
        """Initialize and start the GUI thread"""
        if not self.gui_thread:
            self.data_queue = Queue()
            self.gui_thread = GUI(self.data_queue)
            self.gui_thread.start()
            self.gui_running = True

    def stop_gui_thread(self):
        """Stop the GUI thread safely"""
        if self.gui_thread:
            #self.gui_thread.stop()
            self.gui_thread = None
            self.gui_running = False

    def update_gui(self):
        """Send current game state to GUI thread"""
        if self.gui_running and not self.data_queue.full():
            self.data_queue.put(self)

    def get_current_time(self):
        """Retourne le temps actuel si le jeu n'est pas en pause"""
        if not self.is_paused:
            return time.time()
        return self.current_time
    
    def get_ai_by_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player.ai
        return None
    
    def get_player_by_id(self, player_id):
        for player in self.players:
            if player.id == player_id:
                return player
        return None
    def update_units(self, unit_packet):
        #unit_packet = f"{type}{unit.name};{unit.position[0]};{unit.position[1]};{unit.health};{unit.player.id}"
        unit_info = unit_packet.strip().split(';')
        print(unit_info)
        type = unit_info[0]
        unit_name = unit_info[1]
        unit_position = int(float(unit_info[2])), int(float(unit_info[3]))
        unit_health = int(unit_info[4])
        player_id = int(unit_info[5])
        player = self.get_player_by_id(player_id)
        if type == "spawn_unit":
            unit_position = int(unit_position[0]), int(unit_position[1])
            if unit_name == "Swordsman":
                Unit.spawn_unit(Swordsman, unit_position[0], unit_position[1], player, self.map)
            elif unit_name == "Archer":
                Unit.spawn_unit(Archer, unit_position[0], unit_position[1], player, self.map)
            elif unit_name == "Horseman":
                Unit.spawn_unit(Horseman, unit_position[0], unit_position[1], player, self.map)
            else:
                Unit.spawn_unit(Villager, unit_position[0], unit_position[1], player, self.map)
                if player.units and player.units[-1]:
                    player.units[-1].name = unit_name
        elif type == "place_unit":
            for unit in player.units:
                if unit.name == unit_name:
                    unit.position = unit_position
                    unit.hp = unit_health  
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
            
    def update_buildings(self, building_packet):
        #building_packet = f"{type};{building.name};{building.position[0]};{building.position[1]};{building.hp};{building.player.id}"
        building_info = building_packet.strip().split(';')
        type = building_info[0]
        building_name = building_info[1]
        building_position = int(float(building_info[2])), int(float(building_info[3]))
        building_hp = int(building_info[4])
        player_id = int(building_info[5])
        player = self.get_player_by_id(player_id)
        if type == "spawn_building":
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
            else: 
                return
        elif type == "kill_building":
            for building in player.buildings:
                if building.position == building_position:
                    break
                Building.kill_building(player, player.building, self.map)
            
    def update_map(self, packets):
        packets = packets.split("\n")
        for packet in packets:
            if "building" in packet:
                self.update_buildings(packet)
            elif "unit" in packet:
                self.update_units(packet)
            elif "resource" in packet:
                self.update_resources_map(packet)
            else:
                continue
    
    def run(self, stdscr):
        # Initialize the starting view position
        top_left_x, top_left_y = 0, 0
        viewport_width, viewport_height = 30, 30
        # Display the initial viewport
        stdscr.clear()  # Clear the screen
        
        if self.terminalon :
            self.map.display_viewport(stdscr, top_left_x, top_left_y, viewport_width, viewport_height, Map_is_paused=self.is_paused)  # Display the initial viewport

        try:
            while not self.check_victory():
                # Mettre à jour current_time au début de chaque itération si le jeu n'est pas en pause
                if not self.is_paused:
                    self.current_time = time.time()

                # Handle input
                curses.curs_set(0)  # Hide cursor
                stdscr.nodelay(True)  # Make getch() non-blocking
                key = stdscr.getch()  # Get the key pressed by the user
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
                    self.debug_print(self.players[0].buildings[0].position)
                    self.debug_print(action.get_adjacent_positions(self.players[0].buildings[0].position[0], self.players[0].buildings[0].position[1], self.players[0].buildings[0].size))
                elif key == ord('o'):
                    self.terminalon = not self.terminalon   
                elif key == ord('i'):
                    action.construct_building(self.players[2].units[1], Keep, 10, 10, self.players[2], self.get_current_time())
                    action.move_unit(self.players[1].units[1],15,15,self.get_current_time())
                elif key == ord('u'):
                    Building.kill_building(self.players[0], self.players[0].buildings[0], self.map)
                elif key == ord('y'):
                    Building.kill_building(self.players[0], self.players[0].buildings[-1], self.map)
                elif key == ord('t'):
                    self.players[0].owned_resources["Wood"] = 100


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

                #call the IA
                if not self.is_paused and self.turn % 200 == 0 and self.IA_used == True: # Call the IA every 5 turns: change 0, 5, 10, 15, ... depending on lag
                    for ia in self.ias:
                        ia.current_time_called = self.get_current_time()  # Update the current time for each IA
                        ia.run()  # Run the AI logic for each player
                    
                if not self.is_paused and self.turn % 10 == 0:
                    # Move units toward their target position
                    for player in self.players:
                        for unit in player.units:
                            if unit.task == "going_to_battle":
                                action.go_battle(unit, unit.target_attack, self.get_current_time())
                            elif unit.task == "attacking":
                                action._attack(unit, unit.target_attack, self.get_current_time())
                            elif unit.target_position:
                                target_x, target_y = unit.target_position
                                action.move_unit(unit, target_x, target_y, self.get_current_time())
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
                        for building in player.buildings:
                            if hasattr(building, 'training_queue') and building.training_queue != []:
                                unit = building.training_queue[0]
                                Unit.train_unit(unit, unit.spawn_position[0], unit.spawn_position[1], player, unit.spawn_building, self.map, self.get_current_time())
                            elif type(building).__name__ == "Keep":
                                nearby_enemies = IA.find_nearby_enemies(building.player.ai, max_distance=building.range, unit_position=building.position)  # 5 tile radius
                                if nearby_enemies:
                                    closest_enemy = min(nearby_enemies, 
                                        key=lambda e: IA.calculate_distance(building.player.ai, pos1=unit.position, pos2=e.position))
                                    action.attack_target(building, target=closest_enemy, current_time_called=self.current_time, game_map=self.map)
                                else: 
                                    building.target = None

                # Clear the screen and display the new part of the map after moving
                stdscr.clear()
                if self.terminalon :
                    self.map.display_viewport(stdscr, top_left_x, top_left_y, viewport_width, viewport_height, Map_is_paused=self.is_paused)
                stdscr.refresh()

                if self.gui_running:
                    self.update_gui()

                self.turn += 1

            active_players = [p for p in self.players if p.units or p.buildings]
            self.debug_print(f"Player {active_players[0].name} wins the game!", 'Magenta')
            input("Press Enter to exit...")

        except KeyboardInterrupt:
            self.debug_print("Game interrupted. Exiting...", 'Yellow')
        finally:
            if self.gui_running:
                self.stop_gui_thread()
    
    def check_victory(self):
        if self.turn % 500 == 0: # Check if the game is over
            active_players = [p for p in self.players if p.units or p.buildings] # Check if the player has units and buildings
            return len(active_players) == 1 # Check if there is only one player left
        else:
            return False

    #condition de victoire: être le dernier joueur avec des bâtiments
    def victory():
    
        def big_text(text):
            root = tk.Tk()
            root.title("Texte en gros")
            label = tk.Label(root, text=text, font=("Arial", 48), padx=20, pady=20)
            label.pack(expand=True)
            root.mainloop()

        if GameEngine.check_victory(GameEngine.self) ==True:
            time.stop()
            GUI.load_image(GUI.IMG_PATH / "victory.png")
            big_text(f"Player {GameEngine.active_players[0].name} wins the game!")

    def pause_game(self):
        self.is_paused = not self.is_paused

    def save_game(self, filename=None):
        if not self.is_paused:
            self.is_paused = True
            self.debug_print("Game paused.")
        
        # Generate a filename if none is provided
        if filename is None:
            for i in range(10):  # Limit to 10 auto-saves
                filename = f"../assets/annex/game_save{i}.dat"
                filename1 = f"../assets/annex/game_save{i}.txt"
                if not os.path.exists(filename):  # Check if the file exists
                    break
            else:
                self.debug_print("No available slots to save the game.")
                return
        else:
            # If a filename is provided, add a unique suffix if necessary
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(filename):
                filename = f"{base}_{counter}{ext}"
                counter += 1

        # Save the game state
        try:
            with open(filename, 'wb') as f:
                game_state = {
                    'players': self.players,
                    'map': self.map,
                    'turn': self.turn,
                    'is_paused': self.is_paused,
                    'changed_tiles': self.changed_tiles,
                    'ias': self.ias  # Add self.ias to the saved state
                }
                pickle.dump(game_state, f)
            self.debug_print(f"Game saved to {filename}.")
            # Save the game state to a text file
            with open(filename, "rb") as dat_file:
                data = pickle.load(dat_file)
            with open(filename1, "w", encoding="utf-8") as txt_file:
                txt_file.write(str(data))  
        except Exception as e:
            self.debug_print(f"Error saving game: {e}")


    def load_game(self, filename):
        if not self.is_paused:
            self.is_paused = True
            self.debug_print("Game paused.")
        try:
            with open(filename, 'rb') as f:
                game_state = pickle.load(f)
                self.players = game_state['players']
                self.map = game_state['map']
                self.turn = game_state['turn']
                self.is_paused = game_state['is_paused']
                self.changed_tiles = game_state['changed_tiles']
                self.ias = game_state.get('ias', None)  # Load self.ias or set it to None if missing
                self.current_time = time.time()
            self.debug_print(f"Game loaded from {filename}.")
        except Exception as e:
            self.debug_print(f"Error loading game: {e}")

    def run_multi_player(self, stdscr, this_player_id):
        # Initialize the starting view position
        top_left_x, top_left_y = 0, 0
        viewport_width, viewport_height = 30, 30
        # Display the initial viewport
        stdscr.clear()  # Clear the screen
        processor = DataProcessor(self)
        if self.terminalon :
            self.map.display_viewport(stdscr, top_left_x, top_left_y, viewport_width, viewport_height, Map_is_paused=self.is_paused)  # Display the initial viewport

        try:
            while not self.check_victory():
                # Mettre à jour current_time au début de chaque itération si le jeu n'est pas en pause
                if not self.is_paused:
                    self.current_time = time.time()

                # Handle input
                curses.curs_set(0)  # Hide cursor
                stdscr.nodelay(True)  # Make getch() non-blocking
                key = stdscr.getch()  # Get the key pressed by the user
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
                    for player in self.players:
                        print(player.package.map)
                        print(player.package.package)
                        player.package.map=""
                        player.package.package=""
                    Building.place_starting_buildings(self.map)   # Place starting town centers on the map
                    Unit.place_starting_units(self.players, self.map)  # Place starting units on the map
                elif key == ord('t'):
                    self.update_units("kill_unit;Igor;35;103;25;2")
                elif key == ord('y'):
                    self.update_units("remove_unit;Thibaud;41;107;25;2")
                    self.update_units("place_unit;Thibaud;41;108;25;2")
                    print("yes")
                elif key == ord('u'):
                    packets = "spawn_building;Town Center;114;60;1000;1\nspawn_building;Town Center;36;107;1000;2\nspawn_building;Town Center;34;15;1000;3\nspawn_unit;Leopold;116;58;25;1\nspawn_unit;Adriana;113;61;25;1\nspawn_unit;Mohammed;111;63;25;1\nspawn_unit;Fran?ois/François;33;107;25;2\nspawn_unit;Igor;35;103;25;2\nspawn_unit;Thibaud;41;107;25;2\nspawn_unit;Johnny;38;18;25;3\nspawn_unit;Clement;29;15;25;3\nspawn_unit;Rosy;30;18;25;3"
                    packets += "\nplace_unit;Fran?ois/François;38;99;25;2\nremove_unit;Fran?ois/François;37.55806095915671;99.44193904084328;25;2\nplace_unit;Fran?ois/François;37.55806095915671;99.44193904084328;25;2\nremove_unit;Fran?ois/François;37;100;25;2\nplace_unit;Fran?ois/François;37;100;25;2\nremove_unit;Fran?ois/François;36.396691802976505;100.6033081970235;25;2\nplace_unit;Fran?ois/François;36.396691802976505;100.6033081970235;25;2\nspawn_building;House;43;107;200;2\nremove_unit;Fran?ois/François;36;101;25;2\nplace_unit;Fran?ois/François;36;101;25;2\nremove_unit;Fran?ois/François;35.46968474980076;101.53031525019924;25;2\nplace_unit;Fran?ois/François;35.46968474980076;101.53031525019924;25;2\nremove_unit;Fran?ois/François;35.02551900665695;101.97448099334305;25;2\nplace_unit;Fran?ois/François;35.02551900665695;101.97448099334305;25;2\nremove_unit;Fran?ois/François;35;102;25;2\nplace_unit;Fran?ois/François;35;102;25;2\nremove_unit;Fran?ois/François;35.0;102.75311470031738;25;2\nplace_unit;Fran?ois/François;35.0;102.75311470031738;25;2\nremove_unit;Fran?ois/François;35;103;25;2\nplace_unit;Fran?ois/François;35;103;25;2\nremove_unit;Fran?ois/François;35.0;103.75312232971191;25;2\nplace_unit;Fran?ois/François;35.0;103.75312232971191;25;2\nremove_unit;Fran?ois/François;35;104;25;2\nplace_unit;Fran?ois/François;35;104;25;2\nremove_unit;Fran?ois/François;35.0;104.6281566619873;25;2\nplace_unit;Fran?ois/François;35.0;104.6281566619873;25;2\nremove_unit;Fran?ois/François;35;105;25;2\nplace_unit;Fran?ois/François;35;105;25;2\nremove_unit;Fran?ois/François;35.0;105.62820434570312;25;2\nplace_unit;Fran?ois/François;35.0;105.62820434570312;25;2\nremove_unit;Fran?ois/François;35;106;25;2\nplace_unit;Fran?ois/François;35;106;25;2"
                    self.update_map(packets)

                    for player in self.players:
                        for unit in player.units:
                            print(unit.name)
                            print(unit.position)

                elif key == ord('i'):
                    self.map.update_initial_map(self.players[0].package.map)
                elif key == ord('o'):
                    self.send_data = not self.send_data

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

                #call the IA
                if not self.is_paused and self.turn % 200 == 0 and self.IA_used == True: # Call the IA every 5 turns: change 0, 5, 10, 15, ... depending on lag
                    ia = self.get_ai_by_id(this_player_id)
                    ia.current_time_called = self.get_current_time()  # Update the current time for each IA
                    ia.run()  # Run the AI logic for each player
                    
                if not self.is_paused and self.turn % 10 == 0:
                    # Move units toward their target position
                    for player in self.players:
                        if player.id == this_player_id:
                            for unit in player.units:
                                if unit.task == "going_to_battle":
                                    action.go_battle(unit, unit.target_attack, self.get_current_time())
                                elif unit.task == "attacking":
                                    action._attack(unit, unit.target_attack, self.get_current_time())
                                elif unit.target_position:
                                    target_x, target_y = unit.target_position
                                    action.move_unit(unit, target_x, target_y, self.get_current_time())
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
                            for building in player.buildings:
                                if hasattr(building, 'training_queue') and building.training_queue != []:
                                    unit = building.training_queue[0]
                                    Unit.train_unit(unit, unit.spawn_position[0], unit.spawn_position[1], player, unit.spawn_building, self.map, self.get_current_time())
                                elif type(building).__name__ == "Keep":
                                    nearby_enemies = IA.find_nearby_enemies(building.player.ai, max_distance=building.range, unit_position=building.position)  # 5 tile radius
                                    if nearby_enemies:
                                        closest_enemy = min(nearby_enemies, 
                                            key=lambda e: IA.calculate_distance(building.player.ai, pos1=unit.position, pos2=e.position))
                                        action.attack_target(building, target=closest_enemy, current_time_called=self.current_time, game_map=self.map)
                                    else: 
                                        building.target = None
                        else:
                            pass
                            #processor.update_data(player)
                # Clear the screen and display the new part of the map after moving
                stdscr.clear()
                if self.terminalon :
                    self.map.display_viewport(stdscr, top_left_x, top_left_y, viewport_width, viewport_height, Map_is_paused=self.is_paused)
                stdscr.refresh()

                if self.gui_running:
                    self.update_gui()

                self.turn += 1
                if self.send_data:
                    print(self.players[1].package.package)
                    self.players[1].package.pakage = ""
                    print("===========================")

            active_players = [p for p in self.players if p.units or p.buildings]
            self.debug_print(f"Player {active_players[0].name} wins the game!", 'Magenta')
            input("Press Enter to exit...")

        except KeyboardInterrupt:
            self.debug_print("Game interrupted. Exiting...", 'Yellow')
        finally:
            if self.gui_running:
                self.stop_gui_thread()
