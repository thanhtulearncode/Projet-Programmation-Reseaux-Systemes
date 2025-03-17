import pickle
def convert_to_hex(file_path):
    with open(file_path, 'rb') as file:
        hex_data = file.read().hex()
    return hex_data

def save_hex_to_file(hex_data, output_file):
    with open(output_file, 'w') as hex_file:
        hex_file.write(hex_data)

for i in range(8):
    file_path = f"game_save{i}.dat"

    hex_representation = convert_to_hex(file_path)

    output_file = file_path.replace('.dat', '.hex')

    save_hex_to_file(hex_representation, output_file)

    with open(f"game_save{i}.hex", "r") as f:
        hex_data = f.read().strip()  

    binary_data = bytes.fromhex(hex_data)

    with open(f"output{i}.dat", "wb") as f:
        pickle.dump(binary_data, f)


