import pickle

def convert_to_hex(file_path):
    with open(file_path, 'rb') as file:
        hex_data = file.read().hex()
    return hex_data

def save_hex_to_file(hex_data, output_file):
    with open(output_file, 'w') as hex_file:
        hex_file.write(hex_data)

# Path to the .dat file
file_path = 'game_save6.dat'

# Convert the .dat file data to hex
hex_representation = convert_to_hex(file_path)

# Create the hex file in the same directory
output_file = file_path.replace('.dat', '.hex')
save_hex_to_file(hex_representation, output_file)

# Read the hex data from the .hex file
with open("game_save6.hex", "r") as f:
    hex_data = f.read().strip()


hex_data = hex_data[14:-2]

# Convert the remaining hex data back to binary (bytes)
binary_data = bytes.fromhex(hex_data)

# Save the binary data to a new .dat file
with open("output.dat", "wb") as f:
    pickle.dump(binary_data, f)

print("Data has been processed and saved to 'output.dat'.")
