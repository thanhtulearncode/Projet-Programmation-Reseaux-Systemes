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
from network.Game_Room import *
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
    def __init__(self, game_mode, map_size, players, sauvegarde=False):
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
            print(f"Player {i+1} AI profile: {self.players[i].ai}")
            print(f"Player {i+1} AI: {self.ias[i]}")
        self.IA_used = False
        self.send_data = False

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
    
    def load_initial_map(self, map_packet):
        self.map.map_decoding(map_packet)

    def update_units(self, unit_packet):
        #unit_packet = f"{type};{unit.name};{unit.position[0]};{unit.position[1]};{unit.hp};{unit.player.id};{unit.task};{unit.direction}"   
        unit_info = unit_packet.strip().split(';')
        print(unit_info)
        type = unit_info[0]
        unit_name = unit_info[1]
        unit_position = int(float(unit_info[2])), int(float(unit_info[3]))
        unit_health = int(unit_info[4])
        player_id = int(unit_info[5])
        player = self.get_player_by_id(player_id)
        unit_task = unit_info[6]
        unit_direction = unit_info[7]
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
            
    def update_game(self, packets):
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
        # Get terminal size
        terminal_height, terminal_width = stdscr.getmaxyx()
        
        # Adjust viewport size to fit terminal
        viewport_width = min(30, terminal_width // 2)  # Divide by 2 because each tile takes 2 chars
        viewport_height = min(30, terminal_height - 1)  # Leave 1 line for status
        
        # Initialize the starting view position
        top_left_x, top_left_y = 0, 0
        
        # Display the initial viewport
        stdscr.clear()
        
        # Rest of the code remains the same
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
                    packets = "spawn_building;Town Center;114;60;1000;1\nspawn_building;Town Center;36;107;1000;2\nspawn_building;Town Center;34;15;1000;3\nspawn_unit;Leopold;116;58;25;1\nspawn_unit;Adriana;113;61;25;1\nspawn_unit;Mohammed;111;63;25;1\nspawn_unit;Fran?ois/François;33;107;25;2\nspawn_unit;Igor;35;103;25;2\nspawn_unit;Thibaud;41;107;25;2\nspawn_unit;Johnny;38;18;25;3\nspawn_unit;Clement;29;15;25;3\nspawn_unit;Rosy;30;18;25;3"
                    packets += "\nplace_unit;Fran?ois/François;38;99;25;2\nremove_unit;Fran?ois/François;37.55806095915671;99.44193904084328;25;2\nplace_unit;Fran?ois/François;37.55806095915671;99.44193904084328;25;2\nremove_unit;Fran?ois/François;37;100;25;2\nplace_unit;Fran?ois/François;37;100;25;2\nremove_unit;Fran?ois/François;36.396691802976505;100.6033081970235;25;2\nplace_unit;Fran?ois/François;36.396691802976505;100.6033081970235;25;2\nspawn_building;House;43;107;200;2\nremove_unit;Fran?ois/François;36;101;25;2\nplace_unit;Fran?ois/François;36;101;25;2\nremove_unit;Fran?ois/François;35.46968474980076;101.53031525019924;25;2\nplace_unit;Fran?ois/François;35.46968474980076;101.53031525019924;25;2\nremove_unit;Fran?ois/François;35.02551900665695;101.97448099334305;25;2\nplace_unit;Fran?ois/François;35.02551900665695;101.97448099334305;25;2\nremove_unit;Fran?ois/François;35;102;25;2\nplace_unit;Fran?ois/François;35;102;25;2\nremove_unit;Fran?ois/François;35.0;102.75311470031738;25;2\nplace_unit;Fran?ois/François;35.0;102.75311470031738;25;2\nremove_unit;Fran?ois/François;35;103;25;2\nplace_unit;Fran?ois/François;35;103;25;2\nremove_unit;Fran?ois/François;35.0;103.75312232971191;25;2\nplace_unit;Fran?ois/François;35.0;103.75312232971191;25;2\nremove_unit;Fran?ois/François;35;104;25;2\nplace_unit;Fran?ois/François;35;104;25;2\nremove_unit;Fran?ois/François;35.0;104.6281566619873;25;2\nplace_unit;Fran?ois/François;35.0;104.6281566619873;25;2\nremove_unit;Fran?ois/François;35;105;25;2\nplace_unit;Fran?ois/François;35;105;25;2\nremove_unit;Fran?ois/François;35.0;105.62820434570312;25;2\nplace_unit;Fran?ois/François;35.0;105.62820434570312;25;2\nremove_unit;Fran?ois/François;35;106;25;2\nplace_unit;Fran?ois/François;35;106;25;2"
                    self.update_map(packets)

                    for player in self.players:
                        for unit in player.units:
                            print(unit.name)
                            print(unit.position)

                elif key == ord('i'):
                    self.load_initial_map(".29G1.51G1.38/.105G1.14/.66G1.53/.19W1.36G1.63/.17W6.52W4.1W1.39/.2G1.14W6.52W6.21G1.17/.19W5.56W1.19G1.19/.22W2.78G1.17/.22W2.30G1.65/.21W4.35G1.59/.17W7.81G1.14/.17W1.2W4.23G1.72/.22W1.35G1.61/.120/.31G1.41G1.43G1.2/.120/.18G1.101/.120/.97G1.22/.40G1.79/.120/.40G1.79/.42G1.4G1.72/.120/.72W2.46/.72W3.31G1.13/.16G1.14W3.32G1.5W2.46/.1G1.27W3.1W1.39W1.46/.29W3.1W1.38W2.46/.28G1W5.38W1.26G1.20/.30W4.44G1.41/.31W1.72G1.15/.31W1.88/.11G1.6G1.8W2.2W1.88/.28W4.79G1.8/.16G1.11W2.35G1.54/.29W1.79G1.10/.29W3.34G1.16G1.34G1.1/.29W3.37W2.26G1.22/.6G1.3G1.17W2.38W4.48/.29W2.36W5.36W2.10/.14G1.14W2.36W5.35W3.10/.29W1.39W3.34W3.11/.29W3.38W1.35W2.12/.19G1.11W2.70G1.2W2.6G1.5/.19G1.100/.120/.103G1.7G1.8/.19G1.35G1.64/.78G1.41/G1.24G1.60W3.31/.43G1.43W3.30/.1G1.11G1.4G1.66W4.1G1.29/.53G1.24W1.6W4.13W1.17/.56G1.21W1.7W2.14W4.14/.19G1.56W5.21W4.14/.5G2.23W2.45W2.1W4.16G1.1W3.4G1.10/.28W6.39W1.1G1W3.1W2G1.19W1.1W1.15/.27W4.2W1.37W3.2W2.42/.24W4.5W3.16G1.16W5.46/G1.19W8.5W3.27G1.6W4.46/.7W1.15W2.1W2.5W3.35W5.2G1.41/.6W2.3W2.11W1.1W2.44W5.2G1.38G1.1/.6W2.4W2.9W4.45W2.19G1.26/.5W3.3W3.10W3.1W1.8G1.82/.5W3.2W3.11W5.91/.6W2.3W1.108/.4W4.112/.4W5.35G1.7W1.21G1.45/.4W2.44W3.21G1.8G1.36/W2.2W2.44W2.68/W3.48W1.68/W3.48W2.33G1.33/.2W3.28G1.15W4.4W1.62/.2G1.1W1.43W2.3W5.31G1.30/.2W3.19G1.22W2.4W5.62/.48W2.3W1.2W2.19W2.41/.31G1.7G1.5G1.7W1.1W3.18W6.22W1.15/.76W3G1W3.19W4.14/.18G1.13W1.43W1.5W1.19W4.14/.32W1.48W2.20W3.14/.16G1.12W5.67W5.14/.28W1G1W3.37G1.9G1.23W1.15/.29W2.6G1.82/.29W2.26G1.18G1.43/.30W1.89/.55W2.63/.54W3.56W3.4/.23G1W1.29W1.3W1.53W4.4/.23W3.3G1.24W1.3W1.3G1.49W2.6/.23W1.1W1.15G1.12W5.13G1.39W2.6/.23W7.25W4.16W1.44/.23W2.1W2.27W1.1W1.15W4.27W2.14/.55W3.15W3.28W3.13/.41G1.13W3.15W3.28W3.13/.54W2.17W2.29W1.15/.71W3.4G1.25W1.15/.23W4.44W2.31W1.15/.8W1.15W3.1G1W4.38W2.31W1.15/.7W2.16W4.1W4.70W1.15/G1.5W3.1W1.9G1.10W1.71W2.15/.5W6.20W3.61G1.24/.5W5.73G1.36/.7W3.19G1.17G1.2G1.4W3.62/.9W1.9G1.35W3.17G1.44/.9W4.40W5.29G1.32/.12W1.40W3.20G1.43/.5G1.6W6.36W2.64/.55W2.1W2.14G1.27G1.17/.56W3.61/.2G1.117/.10G1.53G1.55/.9G1.110/.120/.120/.120/.20G1.20G1.21G1.56/.120/.58G1.61/.5G1.114")

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
                            #processor.update_data()
                        request = DataProcessor().update_data() 
                        if request:
                            if request[1] == "scan_rooms":
                                gr= GameRoom()
                                PacketManager().package =  f"{gr.number_of_players};{gr.game_mode};{gr.map_size[0]};{gr.map_size[1]};{gr.player_count};{gr.civilization};{gr.ai_mode}"
                                PacketManager().send_packet()
                            else:
                                requesting_played_id = request[0]
                                resources = None ##TODO
                                PacketManager().package = (Resource_manager.create_init_resource_response(requesting_played_id,resources))
                                PacketManager().send_packet()
                                
                # Clear the screen and display the new part of the map after moving
                stdscr.clear()
                if self.terminalon :
                    try:
                        self.map.display_viewport(stdscr, top_left_x, top_left_y, 
                                                viewport_width, viewport_height, 
                                                Map_is_paused=self.is_paused)
                    except curses.error:
                        # Handle viewport drawing error gracefully
                        pass
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