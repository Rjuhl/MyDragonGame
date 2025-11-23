from decorators import singleton
from pathlib import Path
from typing import List

@singleton
class IdGenerator:
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
        if self.current_game:
            path = self.PATH / self.current_game / 'idstart'
            path.write_text(str(self.current_id), encoding='utf-8')

id_generator = IdGenerator()