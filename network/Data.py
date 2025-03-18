class PacketManager:
    """
    A singleton class to handle the creation, sending, and receiving of packets
    for network communication in the game.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PacketManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, this_player=None):
        if not hasattr(self, "initialized"):
            self.this_player = this_player
            self.initialized = True

    def create_packet(self, player_id, update_type, object_id, position=None, additional_data=None):
        """
        Creates a packet with the given information.

        Args:
            player_id (int): The ID of the player.
            update_type (str): The type of update (e.g., "move_unit", "attack_unit").
            object_id (int): The ID of the object (unit or building).
            position (tuple, optional): The position of the object (x, y).
            additional_data (dict, optional): Any additional data to include in the packet.

        Returns:
            dict: A dictionary representing the packet.
        """
        packet = {
            "player_id": player_id,
            "update_type": update_type,
            "object_id": object_id,
            "position": position,
            "additional_data": additional_data,
        }
        return packet

    def send_packet(self, packet, server_address):
        """
        Sends a packet to the specified server address.

        Args:
            packet (dict): The packet to send.
            server_address (tuple): The server address as (host, port).
        """
        import socket
        import pickle

        try:
            serialized_packet = pickle.dumps(packet)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(server_address)
                s.sendall(serialized_packet)
            print(f"Packet sent to {server_address}: {packet}")
        except Exception as e:
            print(f"Error sending packet: {e}")

    def receive_packet(self, server_socket):
        """
        Receives a packet from the server socket.

        Args:
            server_socket (socket.socket): The server socket.

        Returns:
            dict: The received packet as a dictionary.
        """
        import pickle

        try:
            connection, _ = server_socket.accept()
            with connection:
                data = connection.recv(1024)
                packet = pickle.loads(data)
                print(f"Packet received: {packet}")
                return packet
        except Exception as e:
            print(f"Error receiving packet: {e}")
            return None