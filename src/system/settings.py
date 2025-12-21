import json
from pathlib import Path
from typing import Any, Dict, Optional
from decorators import singleton

class GameSettings:
    PATH = Path(__file__).parent.parent.parent / 'data' / 'games'
    def __init__(self, name: str, game_settings: Dict[str, Any]):
        self.name = name
        self.game_settings = game_settings
    
    @classmethod
    def load(cls, game_name: str):
        game_settings = {}
        path = cls.PATH / game_name / 'game_settings'
        if path.exists(): 
            game_settings = json.loads(path.read_text(encoding="utf-8"))
        return GameSettings(game_name, game_settings)

    def save(self):
        if self.name:
            path = self.PATH / self.name / 'game_settings'
            path.write_text(json.dumps(self.game_settings, ensure_ascii=False, indent=2), encoding='utf-8')

    def get(self, key: str, default: Any = None) -> Any:
        return self.game_settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.game_settings[key] = value


@singleton
class GlobalSettings:
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


global_settings = GlobalSettings(
    defaults={
        "volume": 80
    }
)
        