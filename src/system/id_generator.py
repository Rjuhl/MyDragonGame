from decorators import singleton
from pathlib import Path

@singleton
class IdGenerator:
    PATH = Path(__file__).parent.parent.parent / 'data' / 'idstart'
    def __init__(self):
        self.current_id = 0
        if self.PATH.exists():
            self.current_id = int(self.PATH.read_text(encoding='utf-8'))
    
    def get_id(self):
        id = self.current_id
        self.current_id += 1
        return id
    
    def save(self):
        self.PATH.write_text(str(self.current_id), encoding='utf-8')

id_generator = IdGenerator()