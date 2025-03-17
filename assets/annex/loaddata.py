def convert_to_hex(file_path):
    with open(file_path, 'rb') as file:
        hex_data = file.read().hex()
    return hex_data

# Path to the .dat file
file_path = 'game_save6.dat'

# Convert the .dat file data to hex
hex_representation = convert_to_hex(file_path)

# Print the hex data
print(hex_representation)

# Use the hex data directly without saving to a file
hex_data = hex_representation.strip()

# Convert the remaining hex data back to binary (bytes)
binary_data = bytes.fromhex(hex_data)

# Save the binary data to a new .dat file
with open("output.dat", "wb") as f:
    f.write(binary_data)

print("Data has been processed and saved to 'output.dat'.")
