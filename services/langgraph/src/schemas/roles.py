from enum import Enum
from pathlib import Path

from src.config.settings import Config


class Role(Enum):
    """Champion and system roles for the story generation."""
    
    def __new__(cls, display_name: str, temperature: float = 0.7):
        obj = object.__new__(cls)
        obj._value_ = display_name
        obj.temperature = temperature
        return obj


def _load_roles() -> dict:
    """Load champion roles from the champions.txt file."""
    roles = {}
    
    # Add system roles
    roles["Summarizer"] = "Summarizer"
    roles["Event"] = "Event"
    roles["Novel"] = "Novel"
    roles["RoleAssigner"] = "RoleAssigner"
    
    # Load champion roles from file
    champions_file = Config.CHAMPIONS_FILE
    if champions_file.exists():
        with open(champions_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Handle format: "Champion Name 0.7" or just "Champion Name"
                parts = line.rsplit(" ", 1)
                if len(parts) == 2 and parts[1].replace(".", "").isdigit():
                    name = parts[0]
                else:
                    name = line
                
                # Create identifier (remove spaces, apostrophes, etc.)
                identifier = (
                    name.replace(" ", "")
                    .replace("'", "")
                    .replace(".", "")
                    .replace("&", "And")
                )
                roles[identifier] = name
    
    return roles


# Dynamically create Role enum with loaded roles
_roles_dict = _load_roles()
Role = Enum("Role", _roles_dict, type=Role)

