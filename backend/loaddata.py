import pickle
import json
import Players
from pathlib import Path
path = Path(__file__).resolve().parent.parent / "assets" / "annex" / "game_save0.dat"
with open(path, "rb") as file:
    data = pickle.load(file)

data_str = json.dumps(data, ensure_ascii=False, indent=4)

with open("data_as_string.txt", "w", encoding="utf-8") as output_file:
    output_file.write(data_str)

