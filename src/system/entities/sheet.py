import json
import pygame
from pathlib import Path
from typing import Optional
from regestries import SHADOW_ENTITY_REGISTRY
from utils.generate_shadow_ellipse import generate_shadow_ellipse


class SheetManager:
    def __init__(self, asset_dir: Path):

        self.sprites = []
        
        paths = []
        for asset in asset_dir.iterdir():
            if asset.is_file(): paths.append(asset.resolve())
        paths.sort(key=lambda path: int(path.name[:path.name.find('_')]))
        
        for file in paths:
            name = file.name[file.name.find('_')+1:file.name.find('.')]
            img = pygame.image.load(file).convert_alpha()
            self.sprites.append(SpriteSheet(img, name))

        next_id = len(self.sprites)
        for entity_cls in SHADOW_ENTITY_REGISTRY:
            self.sprites.append(SpriteSheet(
                generate_shadow_ellipse(*SHADOW_ENTITY_REGISTRY[entity_cls]), 
                f"{next_id}_shadow"
            ))
            self.sprites.append(SpriteSheet(
                generate_shadow_ellipse(*SHADOW_ENTITY_REGISTRY[entity_cls], rotation=90),
                f"{next_id + 1}_shadow"
            ))
            entity_cls.SHADOW_ID = next_id
            next_id += 2


    def get_sprite(self, id: int, frame: Optional[int] = None) -> pygame.Surface:
        return self.sprites[id].get_sprite(frame=frame)

        

class SpriteSheet:
    def __init__(self, img: pygame.Surface, name: str):
        self.img = img
        self.data = []

        current_dir = Path(__file__).parent
        data_path = current_dir.parent.parent.parent / 'assets' / 'sprites' / 'meta_data' / f'{name}.json'

        if data_path.is_file():
            json_data = json.loads(data_path.read_text(encoding="utf-8"))
            for _, data in enumerate(json_data["frames"].items()):
                self.data.append([*data[-1]["frame"].values()])
    
    def _get_frame(self, frame: int) -> pygame.Surface:
        x, y, w, h = self.data[frame]
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        sprite.blit(self.img, (0, 0), (x, y, w, h))
        return sprite

    def get_sprite(self, frame: Optional[int] = None):
        return self.img if frame is None else self._get_frame(frame)
    