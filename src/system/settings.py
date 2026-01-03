import json
from typing import Any, Dict, Optional, Self

from pathlib import Path

from decorators import singleton
from constants import DEFAULT_SOUND_VOLUME

class GameSettings:
    """
        Per-save-game settings stored on disk.

        Each game/save has its own directory under:
            data/games/<game_name>/

        This class loads/saves a JSON file at:
            data/games/<game_name>/game_settings

        Notes
        - The JSON structure is a plain dict[str, Any].
        - Call save() after making changes if you want them persisted.
    """
     
    PATH = Path(__file__).parent.parent.parent / 'data' / 'games'

    def __init__(self, name: str, game_settings: Dict[str, Any]):
        self.name = name
        self.game_settings = game_settings
    
    @classmethod
    def load(cls, game_name: str) -> Self:
        game_settings = {}
        path = cls.PATH / game_name / 'game_settings'
        if path.is_file(): 
            game_settings = json.loads(path.read_text(encoding="utf-8"))
        return GameSettings(game_name, game_settings)

    def save(self) -> None:
        if self.name:
            path = self.PATH / self.name / 'game_settings'
            path.write_text(json.dumps(self.game_settings, ensure_ascii=False, indent=2), encoding='utf-8')

    def get(self, key: str, default: Any = None) -> Any:
        return self.game_settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.game_settings[key] = value


@singleton
class GlobalSettings:
    """
        Global settings shared across all saves (stored once on disk).
        
        Stored at:
            data/global_settings
    """

    PATH = Path(__file__).parent.parent.parent / 'data' / 'global_settings'

    def __init__(self, defaults: Optional[Dict[str, Any]] = None):
        self.global_settings = {} if defaults is None else defaults
        self._load_settings()

    def _load_settings(self):
        if self.PATH.is_file():
            self.global_settings = json.loads(self.PATH.read_text(encoding="utf-8"))

    def get(self, key: str, default: Any = None) -> Any:
        return self.global_settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.global_settings[key] = value

    def save(self):
        self.PATH.write_text(json.dumps(self.global_settings, ensure_ascii=False, indent=2), encoding='utf-8')


# Singleton instance with presets if neccarry
global_settings = GlobalSettings(
    defaults={
        "volume": DEFAULT_SOUND_VOLUME
    }
)
        