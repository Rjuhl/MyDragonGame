import json
from pathlib import Path
from typing import Any, Dict

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
        self.game_settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self.game_settings[key] = value

        