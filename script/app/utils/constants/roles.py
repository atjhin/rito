import os
from enum import Enum
from pathlib import Path

class Role(Enum):
    def __new__(cls, display_name: str, temperature: float):
        obj = object.__new__(cls)
        obj._value_ = display_name  
        obj.temperature = temperature
        return obj

current_dir = Path(__file__).parent
file_path = current_dir / "champions.txt"
roles = {}

with open(file_path) as f:
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
        roles[identifier] = name

Role = Enum("Role", roles, type=Role)

if __name__ == "__main__":
    print(Role.Summarizer.value)