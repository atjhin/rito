import os
from enum import Enum

base_dir = os.path.dirname(__file__)
champions_path = os.path.join(base_dir, "champions.txt")

class Role(Enum):
    def __new__(cls, display_name: str, temperature: float):
        obj = object.__new__(cls)
        obj._value_ = display_name  
        obj.temperature = temperature
        return obj

roles = {}
with open("champion_temperatures.txt") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        name, temp = line.rsplit(" ", 1)
        identifier = (
            name.replace(" ", "")
                .replace("'", "")
                .replace(".", "")
                .replace("&", "And")
        )
        roles[identifier] = (name, float(temp))

Role = Enum("Role", roles, type=Role)

Role = Enum("Role", {**Role.__members__,
                     "Narrator": ("Narrator", 0.2),
                     "StoryTeller": ("StoryTeller", 0.5)}, type=Role)


class ModelChoices(Enum):
    gemini_2_flash_lite = "gemini-2.0-flash-lite"
    gemini_2_5_flash_lite = "gemini-2.5-flash-lite"
    gemini_2_5_flash = "gemini-2.5-flash"

