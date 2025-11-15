from decorators import singleton
from pathlib import Path
from typing import List

@singleton
class IdGenerator:
    PATH = Path(__file__).parent.parent.parent / 'data' / 'idstart'
    def __init__(self):
        self.current_id = 0
        if self.PATH.exists():
            self.current_id = int(self.PATH.read_text(encoding='utf-8'))
    
    def get_id(self) -> int:
        id = self.current_id
        self.current_id += 1
        return id
    
    def get_ids(self, num_ids: int) -> List[int]:
        if num_ids <= 0: return []
        self.current_id += num_ids
        return [self.current_id - i for i in range(1, num_ids + 1)]
    
    def save(self) -> None:
        self.PATH.write_text(str(self.current_id), encoding='utf-8')

id_generator = IdGenerator()