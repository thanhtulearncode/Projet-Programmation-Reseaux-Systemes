def convert_to_hex(file_path):
    with open(file_path, 'rb') as file:
        hex_data = file.read().hex()
    return hex_data

def save_hex_to_file(hex_data, output_file):
    with open(output_file, 'w') as hex_file:
        hex_file.write(hex_data)

file_path = 'game_save0.dat'

hex_representation = convert_to_hex(file_path)

output_file = file_path.replace('.dat', '.hex')

save_hex_to_file(hex_representation, output_file)

