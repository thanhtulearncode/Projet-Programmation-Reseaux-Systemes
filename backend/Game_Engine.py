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
    
    """
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
    """
    def check_victory(self):
        if self.turn % 500 == 0: # Check if the game is over
            active_players = [p for p in self.players if p.units or p.buildings] # Check if the player has units and buildings
            return len(active_players) == 1 # Check if there is only one player left
        else:
            return False
    def update_map(self, packet):
        elements = packet.split(";")
        player_id, update_type, object_id, start_x, start_y = elements
        start_x, start_y = int(start_x), int(start_y)
        player_id = int(player_id)
        t = object_id.split(".")
        symbol = t[1]
        player = self.get_player_by_id(player_id)
        if update_type == "place_unit":
            #unit_class = Unit.get_unit_by_symbol(symbol)
            #Unit.spawn_unit(unit_class, start_x, start_y, player, self.map)
            #unit = player.units[-1]
            for unit in player.units:
                if unit.id == object_id:
                    break
            self.map.place_unit(start_x, start_y, unit)
        elif update_type == "remove_unit":
            for unit in player.units:
                if unit.id == object_id:
                    break
            self.map.remove_unit(start_x,start_y, unit)
        elif update_type == "move_unit":
            for unit in player.units:
                if unit.id == object_id:
                    break
            self.map.move_unit(unit, start_x, start_y, unit.position[0], unit.position[1])
        elif update_type == "place_building":
            building_class = Building.get_building_by_symbol(symbol)
            building = Building.spawn_building(building_class, start_x, start_y, player, self.map)
            self.map.place_building(start_x, start_y, building)
        elif update_type == "remove_building":
            for building in player.buildings:
                if building.id == object_id:
                    break
            Building.kill_building(player, building, self.map)
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
                    self.update_map("1;place_unit;1.v.6;1;1")
                elif key == ord('t'):
                    self.update_map("1;remove_unit;1.v.6;1;1")
                elif key == ord('y'):
                    self.update_map("1;place_unit;1.v.6;1;2")
                elif key == ord('u'):
                    self.update_map("1;remove_unit;1.v.6;1;2")
                elif key == ord('i'):
                    self.update_map("1;place_unit;1.v.6;1;3")
                    map_packet = "..............................................................................G....................G....................\n.......................................................................................G................................\n........................................................................................................G...............\n.......................................................G......G.........................................................\n........................................................................................................................\n...............................................G........................................................................\n........................................................................................................................\n......G.................................................................................................................\n.G........................................................G.............................................................\n.............................................................G..........................................................\n.............................................................................................G..........................\n..........................................................................................G..................G..........\n...........................................................................................................W............\n...................................................G................................................G...W.WWWW........G.\n..................W.....................................................................................WWWWWW.W...W....\n..G...............WW......................G.............................................................WWWWWW.WWWWW....\n..................WWW................................................................G..................W...WGWWWW......\n..................WWW.................G......................................................................WWWWWW..G..\n..............G..WWWWW...........G................................................................G.....................\n...........G......WW...........................G.........G..............................................................\n........................................................................................................................\n........................................................................................................................\n.................................................................W...........................................G..........\n......W............................................G............WWWWWW..................................................\n......WWW........................................................WWWWWWW...............................................G\n...WWWWW.............G...........................................WW.W..WW...............................................\n..WWWWW..........................................................W.WW.......................G..............G............\n...GWWW..........................................................WWWW...................................................\n...WW.WW..........G....G..................WW.....................WWW....G...............................................\n...WWWWWW.................................WWWWW.................W..W....................................................\n.......................................G..W...GW................WWWW...................G................................\n...........................................G..W.................WWW.....................................W.G.............\n...........................................WWWW...................W.....................................W...............\n............................................WW..........................................................W...............\n.......................................................................................G................W...............\nG.G................................................................G...........................G....WWWWW...............\n............................................................G.G.....................................WWWW................\n.........................................................WW.................G....................WWWWW..................\n.........................................................WW.........G...........................WWWWW...................\n......................................................WW.W....................................WWWWWWW...................\n.....................G.................G...G........WWW.WW....................................WWWW.WW...................\n....................WW.WWWWW.............G..........WWWWW..W.......................................WW...................\n....................WWWWWWWW..........................G....W.......................................WWW..................\n.....................WW.WW.W...............................W.............................W..............................\n................G.......................................WW.W............................WWW.............................\n.......................................................WWWWW.............................WWWWWW.........................\n........................................................WWW......................GWW.W.WWWWWG.W.........................\n.....................................................G..WWW.......................WWWWWWWWW.............................\n...................WWW............................................................WWW...G...............................\n...................WWW.............................................................WW...................................\n...................WWW......................................................W.W............................WWW..........\n...................WWW....................G...............................WWWWWW.........................WWWWG..........\n.....................W....................................................WWWWWWW........................WWWWWW.........\n.....................W..........................................................W..........................WWWW.........\n.....................WW......................................................WW.W................WW.........W...........\n.......G..........................G...........................................WWW...............WWWW........W...........\n..............................................................................................WWW..W....................\n...............................................................................................W...WW...................\n.................W.WW..........................................................................W....W...................\n................WWWWWW..............................WW..........................G.............WW........................\n..................WWWWW..............G...............W..........................G............WW.........................\n....................WWWW.............................WW....................................WWW..........................\n.....................W.W...........................WWWWW........................W..........WW...........................\n....................................................WWWW......................WWW...........WW..........................\n................G......................................WW.....................WW............WWW.........................\n.......................................................W.......................W........................................\n.G.....................G..............WW...............W......................WW........................................\n..............G.......................WWWW...................................WWW........................................\n...................................G...W.W...................................WW........................................G\n.......................................WWWWW.................................WW.........................................\n......................................WWWWWWW..............................................G............................\n.....................G.................W..WW...................W........................................................\n........................................WWWW...................WW.WWW...................................................\n........................................WW..........G...........WWWWW...................................................\n.......................G........................................WWWWW..................................G................\n.............................G.................................WWWWWWW..................................................\n................................................................W...........G...............................G...........\n..........................................................G.......................G.....................................\n....G.WWW...............................................................................................................\nG.WWWWWWW...............................................................................................................\n..WW..WW................................................................................................................\n..W...WW.................................................................................G..............................\n.......WW.............G.............................................G...................................................\n........W.........................................................................................................G.....\n........W....................................G..........................................................................\n........W................................................................G..G...............................G...........\n......WWW.........................................................................................................G.....\n........W.............................................G.................................................................\n........W...........W..............................................................................W....................\n........W.W.........W................G.....................G...................................WWWWW..G..........G......\n.....G..W.W...WWWWWWW..........G..................................................G..............WWW....................\n........WWW.WWWWWWWWWWWWW...........................G..................................G........GWW.....................\n..........WWWW....WWWW.WW........................................................................WW.....................\n...........WWW....WWW..WW.......................................................................WWW.....................\n....G.......W.......WWGW...........................................................G...........WWWW.....................\n.....................G..................................................................................................\n................................................................................................G.......................\n........................................................................................................................\n........................................................................................................................\n........................................................................................................................\n..........................WW...................................................................WWWW.....................\n............G.............WW.................................................................WWW.WW.........G...........\n.........................WW....................G.............................................WWWWW......................\n.........................WWW.................................................................WWW........................\n.....G...................WWWWWW.....................................................WW.........WWW......................\n.......................G....WWW......W.W............................................WWW.........WW......................\n............................WWW.....WWWW.................G..........................WWWWW........WWW....................\n............................WW.......WWW............................................WWWWW...............................\n......................................WW...............G................................WWWW..............G.............\n........................................................................................G.WW............................\n...........................................................................................W..............G.............\n........................................................................................................................\n........................................................................................................................\n..................................................................G.....................................................\n...........................................................................................G............................\n................G.......................................................................................................\n........................................................................................................................\n........................................................................................................................\n........................................................................G...............................................\n................................................G.......................................................................\n"
                    self.map.update_initial_map(map_packet)
                    
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