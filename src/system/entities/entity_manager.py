import numpy as np
from typing import List, Dict
from system.game_clock import game_clock
from system.entities.physics.collisions import check_collision, resolve_collisions
from system.entities.physics.spatial_hash_grid import SpatialHashGrid
from system.screen import Screen
from system.entities.entity import Entity
from system.render_obj import RenderObj
from world.chunk import Chunk
from utils.types.shade_levels import ShadeLevel
from system.entities.sprites.player import Player
from system.entities.physics.shadows import EllipseData, Receiver, Shadows
from constants import TILE_SIZE, DISPLAY_SIZE, WORLD_HEIGHT


class EntityManager:
    def __init__(self, screen: Screen):
        self.screen = screen
        self.shadows = Shadows()
        self.spatial_hash_grid = SpatialHashGrid()
        self.entities = set()
        self.player = None

        self.kill_listener_subscribers = []
        self.entities_on_screen = []
        self.queued_additions = set()
        self.queued_removals = set()
    
    def queue_entity_addition(self, entity: Entity) -> None:
        self.queued_additions.add(entity)

    def queue_entity_removal(self, entity: Entity) -> None:
        self.queued_removals.add(entity)

    def add_entity(self, entity: Entity) -> None:
        entity.bind_to_manager(self)
        self.entities.add(entity)
        if entity.solid: self.spatial_hash_grid.add_entity(entity)

    def remove_entity(self, entity: Entity) -> None:
        # kill entity
        self.entities.remove(entity)
        if entity.solid: self.spatial_hash_grid.remove_entity(entity)

        # Notify subscribers
        for subscriber in self.kill_listener_subscribers:
            subscriber.recieve_death_event(entity)


    def add_kill_listener_subscriber(self, subscriber):
        self.kill_listener_subscribers.append(subscriber)

    # Updates all entities and returns a list of them to render
    def update_entities(self) -> None :
        dt = game_clock.dt
        screen_location, screen_size = self.screen.get_hitbox()

        self.entities_on_screen = []
        self.shadows.reset_receivers()

        self.shadows.add_receiver(self.screen.get_screen_reciever())
        for entity in self.entities:
            onscreen = check_collision(entity.location, entity.size, screen_location, screen_size)
            entity.update(dt, onscreen)
            if onscreen: 
                self.entities_on_screen.append(entity)
                if (reciever := entity.serve_reciever()): 
                    self.shadows.add_receiver(reciever)
                
        
        resolve_collisions(self.spatial_hash_grid.get_possible_onscreen_collisions(*self.screen.get_bounding_box()))
        
        # Handle entity adds/removes that initaited in the update loop

        for entity in self.queued_removals: self.remove_entity(entity)
        for entity in self.queued_additions: self.add_entity(entity)
        
        self.queued_removals = set()
        self.queued_additions = set()

    def get_entity_render_objs(self, player: Player) -> List[RenderObj]:
        render_objs = []
        for entity in self.entities_on_screen:
            render_objs.extend(entity.get_render_objs())
            if (shadow:= entity.serve_shadow()): render_objs.append(shadow)
        
        render_objs.extend(self.shadows.get_shadow_objs(player.get_shadow()))
        render_objs.sort(key= lambda r_obj: r_obj.render_order)

        return render_objs
    
    def get_and_removed_chunk_entities(self, chunk: Chunk) -> set[Entity]:
        x, y, _ = chunk.location.location
        removed_entities = self.spatial_hash_grid.get_entities_in_range(x, y, chunk.SIZE, chunk.SIZE, remove_entities=True)
        self.entities.difference_update(removed_entities)
        return removed_entities

    def get_chunk_entities(self, chunk: Chunk) -> set[Entity]:
        x, y, _ = chunk.location.location
        return self.spatial_hash_grid.get_entities_in_range(x, y, chunk.SIZE, chunk.SIZE)

class EntityManagerSubscriber:
    def recieve_death_event(entity: Entity):
        pass

