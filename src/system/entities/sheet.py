import json
import pygame
from pathlib import Path
from typing import Optional, List

from regestries import SHADOW_ENTITY_REGISTRY
from utils.generate_shadow_ellipse import generate_shadow_ellipse


class SheetManager:
    """
        Loads all sprite sheets from an asset directory and provides access to sprites by id.

        Directory convention (preserved from your code):
        <id>_<name>.<ext>

        Example:
        0_player.png
        1_tree.png

        For each file:
        - The numeric prefix determines the sprite ID order (after sorting).
        - The <name> portion is used to load metadata from:
            assets/sprites/meta_data/<name>.json

        Also appends procedurally-generated "shadow ellipse" sheets for entity classes
        registered in SHADOW_ENTITY_REGISTRY, and writes `entity_cls.SHADOW_ID` so
        entities can reference their shadow sprite id at runtime.
    """

    def __init__(self, asset_dir: Path):

        self.sprites: List[SpriteSheet] = []
        
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
        """
        Return either:
        - the full sheet image if frame is None
        - a single frame cropped from the sheet metadata otherwise
        """
        return self.sprites[id].get_sprite(frame=frame)

        

class SpriteSheet:
    """
        Represents a sprite sheet image and optional frame metadata.

        If metadata exists at:
            assets/sprites/meta_data/<sheet_name>.json

        then `get_sprite(frame=n)` will crop and return the n-th frame.
        Otherwise, `get_sprite(frame=...)` will raise IndexError.
    """

    def __init__(self, img: pygame.Surface, name: str):
        self.img = img
        self.data = []

        current_dir = Path(__file__).parent
        data_path = current_dir.parent.parent.parent / 'assets' / 'sprites' / 'meta_data' / f'{name}.json'
        self._load_data(data_path)
    
    def _get_frame(self, frame: int) -> pygame.Surface:
        """ Crop the requested frame (x, y, w, h) from the sheet image into a new surface """
        x, y, w, h = self.data[frame]
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        sprite.blit(self.img, (0, 0), (x, y, w, h))
        return sprite
    
    def _load_data(self, data_path: Path):
        """ Load frame rectangles from a TexturePacker-style JSON file """
        if data_path.is_file():
            json_data = json.loads(data_path.read_text(encoding="utf-8"))
            for _, data in enumerate(json_data["frames"].items()):
                self.data.append([*data[-1]["frame"].values()])

    def get_sprite(self, frame: Optional[int] = None):
        """
        If no frame is specified, return the full sheet image.
        If a frame is specified, return that cropped frame.
        """
        return self.img if frame is None else self._get_frame(frame)