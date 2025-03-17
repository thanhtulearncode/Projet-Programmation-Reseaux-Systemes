def compare_files(file1_path, file2_path):
    try:
        with open(file1_path, 'rb') as file1, open(file2_path, 'rb') as file2:
            file1_data = file1.read()
            file2_data = file2.read()
            if file1_data == file2_data:
                return True  
            else:
                return False  
    except FileNotFoundError:
        print("not exist")
        return False

file1 = 'game_save6.dat'
file2 = 'output.dat'

if compare_files(file1, file2):
    print("same")
else:
    print("diff")
