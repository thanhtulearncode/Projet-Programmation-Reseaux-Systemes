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
        self.map = Map(*map_size)  # Create a map object
        self.generated_map = False
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
            Building.place_starting_buildings(self.map)   # Place starting town centers on the map
            Unit.place_starting_units(self.players, self.map)  # Place starting units on the map
        
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
    
    def load_map(self, map_packet):
        self.map.map_decoding(map_packet)

    def update_resources_map(self, resource_info):
        #f"{0};{type};{resource.type};{x};{y};{resource.amount}"
        type = resource_info[1]
        resource_type = resource_info[2]
        x = int(float(resource_info[3]))
        y = int(float(resource_info[4]))
        self.map.grid[y][x].resource.amount = int(resource_info[5])
        if self.map.grid[y][x].resource.amount <= 0:
            self.map.grid[y][x].resource = None

    def load_current_state(self, packet):
        if packet[1] and "unit" in packet[2]:
            player_id = int(packet[1])
            action_type = packet[2]
            target_name = packet[3]
            target_x = int(float(packet[4])) if packet[4] != "None" else None
            target_y = int(float(packet[5])) if packet[5] != "None" else None
            target_hp = int(packet[6]) if packet[6] != "None" else None
            unit_name = packet[7]
            unit_x = int(float(packet[8]))
            unit_y = int(float(packet[9]))
            unit_hp = int(packet[10])
            unit_task = packet[11]
            unit_direction = packet[12]
            
            player = self.get_player_by_id(player_id)

            if action_type in ("spawn_unit", "current_unit"):
                unit_classes = {"Swordsman": Swordsman, "Archer": Archer, "Horseman": Horseman, "Villager": Villager}
                unit_class = next((cls for name, cls in unit_classes.items() if name in unit_name), Villager)
                unit = unit_class(player, position=(unit_x, unit_y), name=unit_name)
                unit.hp = unit_hp
                unit.task = unit_task
                unit.direction = unit_direction
                
                for u in player.units:
                    if u.name == unit_name:
                        player.units.remove(u)
                        u.player = None
                        self.map.remove_unit(int(u.position[0]), int(u.position[1]), u)
                        break
                
                player.units.append(unit)
                player.population = len(player.units)
                self.map.place_unit(unit_x, unit_y, unit)
        elif packet[1] and "building" in packet[2]:
            player_id = int(packet[1])
            action_type = packet[2]
            target_name = packet[3]
            target_x = int(float(packet[4])) if packet[4] != "None" else None
            target_y = int(float(packet[5])) if packet[5] != "None" else None
            target_hp = int(packet[6]) if packet[6] != "None" else None
            building_name = packet[7]
            building_x = int(float(packet[8]))
            building_y = int(float(packet[9]))
            building_hp = int(packet[10])
            
            player = self.get_player_by_id(player_id)
            
            if action_type in ["spawn_building", "current_building"]:
                building_position = (building_x, building_y)
                building_classes = {
                    "Town Center": TownCenter, "Barracks": Barracks, "Stable": Stable, 
                    "ArcheryRange": ArcheryRange, "Keep": Keep, "Farm": Farm, 
                    "House": House, "Camp": Camp
                }
                building_class = building_classes.get(building_name, None)
                if building_class:
                    building = building_class(player)
                    building.position = building_x, building_y
                    for b in player.buildings:
                        if b.position == building.position:
                            player.building.remove(b)
                            b.player = None
                            self.map.remove_building(int(u.position[0]), int(u.position[1]), b)
                    self.map.place_building(building_x, building_y, building)
                    player.buildings.append(building)
        else:
            return


    def update_units(self, unit_info):
        current_time_called = float(unit_info[0])
        player_id = int(unit_info[1])
        action_type = unit_info[2]
        target_name = unit_info[3]
        target_x = int(float(unit_info[4])) if unit_info[4] != "None" else None
        target_y = int(float(unit_info[5])) if unit_info[5] != "None" else None
        target_hp = int(unit_info[6]) if unit_info[6] != "None" else None
        unit_name = unit_info[7]
        unit_x = int(float(unit_info[8]))
        unit_y = int(float(unit_info[9]))
        unit_hp = int(unit_info[10])
        unit_task = unit_info[11]
        unit_direction = unit_info[12]
        
        player = self.get_player_by_id(player_id)

        if action_type in ("spawn_unit", "current_unit"):
            unit_classes = {"Swordsman": Swordsman, "Archer": Archer, "Horseman": Horseman, "Villager": Villager}
            unit_class = next((cls for name, cls in unit_classes.items() if name in unit_name), Villager)
            unit = unit_class(player, position=(unit_x, unit_y), name=unit_name)
            unit.hp = unit_hp
            unit.task = unit_task
            unit.direction = unit_direction
            
            for u in player.units:
                if u.name == unit_name:
                    player.units.remove(u)
                    u.player = None
                    self.map.remove_unit(int(u.position[0]), int(u.position[1]), u)
                    break
            
            player.units.append(unit)
            player.population = len(player.units)
            self.map.place_unit(unit_x, unit_y, unit)
        elif action_type == "kill_unit":
            for unit in player.units:
                if unit.name == unit_name:
                    Unit.kill_unit(player, unit, self.map)
        elif action_type == "going_to_battle":
            unit = None
            for u in player.units:
                if u.name == unit_name:
                    unit = u
            Action(self.map).go_battle(unit, unit.target_attack, self.get_current_time())
        elif action_type == "_attack":
            unit = None
            for u in player.units:
                if u.name == unit_name:
                    unit = u
            enemy = None
            if unit.target_attack and unit.target_attack.name == target_name:
                enemy = unit.target_attack
            elif unit.is_attacked_by and unit.is_attacked_by.name == target_name:
                enemy = unit.is_attacked_by
            Action(self.map)._attack(unit, enemy, self.get_current_time())
        elif action_type == "move_unit":
            unit = None
            for u in player.units:
                if u.name == unit_name:
                    unit = u
            Action(self.map).move_unit(unit, target_x, target_y, self.get_current_time())
        elif action_type == "_gather":
            unit = None
            for u in player.units:
                if u.name == unit_name:
                    unit = u
            Action(self.map)._gather(unit, target_name, self.get_current_time())
        elif action_type == "gather_resources":
            unit = None
            for u in player.units:
                if u.name == unit_name:
                    unit = u
            Action(self.map).gather_resources(unit, unit.last_gathered, self.get_current_time())
        elif action_type == "construct_building":
            unit = None
            for u in player.units:
                if u.name == unit_name:
                    unit = u
            Action(self.map).construct_building(unit, unit.construction_type, unit.target_building[0], unit.target_building[1], player, self.get_current_time())
        elif action_type == "_construct":
            unit = None
            for u in player.units:
                if u.name == unit_name:
                    unit = u
            Action(self.map)._construct(unit, unit.construction_type, unit.target_building[0], unit.target_building[1], player, self.get_current_time())

    def update_buildings(self, building_info):
        player_id = int(building_info[1])
        action_type = building_info[2]
        target_name = building_info[3]
        target_x = int(float(building_info[4])) if building_info[4] != "None" else None
        target_y = int(float(building_info[5])) if building_info[5] != "None" else None
        target_hp = int(building_info[6]) if building_info[6] != "None" else None
        building_name = building_info[7]
        building_x = int(float(building_info[8]))
        building_y = int(float(building_info[9]))
        building_hp = int(building_info[10])
        
        player = self.get_player_by_id(player_id)
        
        if action_type in ["spawn_building", "current_building"]:
            building_position = (building_x, building_y)
            building_classes = {
                "Town Center": TownCenter, "Barracks": Barracks, "Stable": Stable, 
                "ArcheryRange": ArcheryRange, "Keep": Keep, "Farm": Farm, 
                "House": House, "Camp": Camp
            }
            building_class = building_classes.get(building_name, None)
            if building_class:
                building = building_class(player)
                building.position = building_x, building_y
                for b in player.buildings:
                    if b.position == building.position:
                        player.building.remove(b)
                        b.player = None
                        self.map.remove_building(int(b.position[0]), int(b.position[1]), b)
                self.map.place_building(building_x, building_y, building)
                player.buildings.append(building)
        
        elif action_type == "kill_building":
            for building in player.buildings:
                if building.position == (building_x, building_y):
                    Building.kill_building(player, building, self.map)
                    break
            
    def update_game(self, packet):
        if packet[1] and "building" in packet[2]:
            print("Huy dep trai 456")
            self.update_buildings(packet)
        elif packet[1] and "unit" in packet[2]:
            print("Huy dep trai 123")
            self.update_units(packet)
        else:
            return
    
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
                                enemy = unit.target_attack
                                PacketManager.create_unit_packet(unit, "go_battle", self.get_current_time, enemy.name, enemy.position[0], enemy.position[1], enemy.hp)
                                #action.go_battle(unit, unit.target_attack, self.get_current_time())
                            elif unit.task == "attacking":
                                enemy = unit.target_attack
                                PacketManager.create_unit_packet(unit, "_attack", self.get_current_time, enemy.name, enemy.position[0], enemy.position[1], enemy.hp)
                                #action._attack(unit, unit.target_attack, self.get_current_time())
                            elif unit.target_position:
                                target_x, target_y = unit.target_position
                                PacketManager.create_unit_packet(unit, "move_unit", self.get_current_time(), None, target_x, target_y)
                                #action.move_unit(unit, target_x, target_y, self.get_current_time())
                            elif unit.task == "gathering" or unit.task == "returning":
                                resource_type = unit.last_gathered
                                x, y = unit.target_resource
                                PacketManager.create_unit_packet(unit, "_gather", self.get_current_time(), resource_type, x, y)
                                #action._gather(unit, unit.last_gathered, self.get_current_time())
                            elif unit.task == "marching":
                                resource_type = unit.last_gathered
                                PacketManager.create_unit_packet(unit, "gather_resources", self.get_current_time(), resource_type)
                                #action.gather_resources(unit, unit.last_gathered, self.get_current_time())
                            elif unit.task == "is_attacked":
                                enemy = unit.is_attacked_by
                                PacketManager.create_unit_packet(unit, "_attack", self.get_current_time, enemy.name, enemy.position[0], enemy.position[1], enemy.hp)
                                #action._attack(unit, unit.is_attacked_by, self.get_current_time())
                            elif unit.task == "going_to_construction_site":
                                building_type = unit.construction_type.name
                                x, y = unit.target_buiilding
                                PacketManager.create_unit_packet(unit, "construct_building", self.get_current_time(), building_type, x, y)
                                #action.construct_building(unit, unit.construction_type, unit.target_building[0], unit.target_building[1], player, self.get_current_time())
                            elif unit.task == "constructing":
                                building_type = unit.construction_type.name
                                x, y = unit.target_buiilding
                                PacketManager.create_unit_packet(unit, "_construct", self.get_current_time(), building_type, x, y)
                                #action._construct(unit, unit.construction_type, unit.target_building[0], unit.target_building[1], player, self.get_current_time())
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

                #call the IA
                if not self.is_paused and self.turn % 200 == 0 and self.IA_used == True: # Call the IA every 5 turns: change 0, 5, 10, 15, ... depending on lag
                    ia = self.get_ai_by_id(this_player_id)
                    ia.current_time_called = self.get_current_time()  # Update the current time for each IA
                    ia.run()  # Run the AI logic for each player
                    
                if not self.is_paused and self.turn % 10 == 0:
                    # Move units toward their target position
                        player = self.get_player_by_id(this_player_id)
                        for unit in player.units:
                            if unit.task == "going_to_battle":
                                enemy = unit.target_attack
                                PacketManager.create_unit_packet(unit, "go_battle", self.get_current_time, enemy.name, enemy.position[0], enemy.position[1], enemy.hp)
                                #action.go_battle(unit, unit.target_attack, self.get_current_time())
                            elif unit.task == "attacking":
                                enemy = unit.target_attack
                                PacketManager.create_unit_packet(unit, "_attack", self.get_current_time, enemy.name, enemy.position[0], enemy.position[1], enemy.hp)
                                #action._attack(unit, unit.target_attack, self.get_current_time())
                            elif unit.target_position:
                                target_x, target_y = unit.target_position
                                PacketManager.create_unit_packet(unit, "move_unit", self.get_current_time(), None, target_x, target_y)
                                #action.move_unit(unit, target_x, target_y, self.get_current_time())
                            elif unit.task == "gathering" or unit.task == "returning":
                                resource_type = unit.last_gathered
                                x, y = unit.target_resource
                                PacketManager.create_unit_packet(unit, "_gather", self.get_current_time(), resource_type, x, y)
                                #action._gather(unit, unit.last_gathered, self.get_current_time())
                            elif unit.task == "marching":
                                resource_type = unit.last_gathered
                                PacketManager.create_unit_packet(unit, "gather_resources", self.get_current_time(), resource_type)
                                #action.gather_resources(unit, unit.last_gathered, self.get_current_time())
                            elif unit.task == "is_attacked":
                                enemy = unit.is_attacked_by
                                PacketManager.create_unit_packet(unit, "_attack", self.get_current_time, enemy.name, enemy.position[0], enemy.position[1], enemy.hp)
                                #action._attack(unit, unit.is_attacked_by, self.get_current_time())
                            elif unit.task == "going_to_construction_site":
                                building_type = unit.construction_type.name
                                x, y = unit.target_buiilding
                                PacketManager.create_unit_packet(unit, "construct_building", self.get_current_time(), building_type, x, y)
                                #action.construct_building(unit, unit.construction_type, unit.target_building[0], unit.target_building[1], player, self.get_current_time())
                            elif unit.task == "constructing":
                                building_type = unit.construction_type.name
                                x, y = unit.target_buiilding
                                PacketManager.create_unit_packet(unit, "_construct", self.get_current_time(), building_type, x, y)
                                #action._construct(unit, unit.construction_type, unit.target_building[0], unit.target_building[1], player, self.get_current_time())
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
                        DataProcessor().processing()


                                
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