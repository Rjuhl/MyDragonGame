from typing import List
from pathlib import Path

from decorators import singleton

@singleton
class IdGenerator:
    """
        Centralized incremental ID generator for game entities.

        This class provides monotonically increasing integer IDs that are:
        - unique within a single game/save
        - persistent across game loads (via disk storage)

        IDs are stored per game in:
            data/games/<game_name>/idstart

        Design notes
        - Implemented as a singleton so all systems share one ID source.
        - IDs are simple integers; no reuse or compaction is attempted.
        - `load_game()` must be called when switching or loading a save.
    """

    PATH = Path(__file__).parent.parent.parent / 'data' / 'games'

    def __init__(self):
        self.current_id = 0
        self.current_game = None

    def load_game(self, game_name):
        self.current_id = 0
        self.current_game = game_name
        path = self.PATH / self.current_game / 'idstart'
        if path.exists(): self.current_id = int(path.read_text(encoding='utf-8'))
    
    def get_id(self) -> int:
        id = self.current_id
        self.current_id += 1
        return id
    
    def get_ids(self, num_ids: int) -> List[int]:
        if num_ids <= 0: return []
        self.current_id += num_ids
        return [self.current_id - i for i in range(1, num_ids + 1)]
    
    def save(self) -> None:
        if self.current_game and (self.PATH / self.current_game).is_dir():
            path = self.PATH / self.current_game / 'idstart'
            path.write_text(str(self.current_id), encoding='utf-8')

id_generator = IdGenerator()