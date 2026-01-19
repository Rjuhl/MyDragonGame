from typing import List, Optional, Callable, Dict

from world.chunk import Chunk
from utils.coords import Coord
from system.screen import Screen
from system.render_obj import RenderObj
from system.entities.entity import Entity
from system.entities.sprites.player import Player
from system.entities.physics.shadows import Shadows
from system.entities.physics.spatial_hash_grid import SpatialHashGrid

from system.game_clock import game_clock
from system.entities.physics.collisions import check_collision, resolve_collisions

from metrics.simple_metrics import timeit

class EntityManager:
    """
        Owns and updates all entities in the world.

        Responsibilities
        - Stores entities by id
        - Updates entities and collects "on-screen" entities for rendering
        - Runs broad-phase + narrow-phase collision resolution via SpatialHashGrid + resolve_collisions
        - Manages receiver surfaces and builds shadow RenderObjs
        - Supports safe add/remove during update via queueing
        - Notifies subscribers when an entity is killed/removed
    """

    def __init__(self, screen: Screen):
        self.screen = screen
        self.shadows = Shadows()
        self.spatial_hash_grid = SpatialHashGrid()
        self.entities: Dict[int, Entity] = {}
        self.player = None

        self.kill_listener_subscribers = []
        self.entities_on_screen = []
        self.queued_additions = set()
        self.queued_removals = set()

    # -------------------------------------------------------------------------
    # Basic configuration
    # -------------------------------------------------------------------------
    
    def set_player(self, player: Optional[Player]) -> None:
        """ Bind the player entity (may be None during loading/screens) """
        self.player = player

    # -------------------------------------------------------------------------
    # Safe add/remove API (queueing)
    # -------------------------------------------------------------------------

    def queue_entity_addition(self, entity: Entity) -> None:
        """ Request that an entity be added at the end of the current update tick """
        self.queued_additions.add(entity)

    def queue_entity_removal(self, entity: Entity) -> None:
        """ Request that an entity be removed at the end of the current update tick """
        self.queued_removals.add(entity)

    # -------------------------------------------------------------------------
    # Immediate add/remove (called by the queue flush)
    # -------------------------------------------------------------------------

    def add_entity(self, entity: Entity) -> None:
        """
        Add an entity immediately.
        NOTE: Prefer queue_entity_addition() during update loops.
        """
        entity.bind_to_manager(self)
        self.entities[entity.id] = entity
        if entity.solid: self.spatial_hash_grid.add_entity(entity)

    def remove_entity(self, entity: Entity) -> None:
        """
        Remove an entity immediately and notify subscribers.
        NOTE: Prefer queue_entity_removal() during update loops.
        """
        # kill entity
        del self.entities[entity.id]
        if entity.solid: self.spatial_hash_grid.remove_entity(entity)

        if not entity.send_death_event: return

        # Notify subscribers
        for subscriber in self.kill_listener_subscribers:
            subscriber.recieve_death_event(entity)

    def add_kill_listener_subscriber(self, subscriber):
        self.kill_listener_subscribers.append(subscriber)

    # -------------------------------------------------------------------------
    # Main update loop
    # -------------------------------------------------------------------------
    @timeit()
    def update_entities(self) -> None:
        """
        Update all entities for this tick.

        Steps
        - Compute what is on-screen (for entity update optimizations and render list)
        - Rebuild shadow receivers (screen + any entity-provided receivers)
        - Resolve collisions among on-screen candidates (broad-phase from grid)
        - Apply any queued add/remove operations
        """
        print(f"There are {len(self.entities)} entities")
        dt = game_clock.dt
        screen_location, screen_size = self.screen.get_hitbox()

        self.entities_on_screen = []
        self.shadows.reset_receivers()

        # Always include a ground plane to recieve shadows
        self.shadows.add_receiver(self.screen.get_screen_reciever())

        # Update entities and collect render/collision/shadow metadata.
        for entity in self.entities.values():
            # The +z padding of 1 prevents “flat” entities from missing collision
            onscreen = check_collision(entity.location, entity.size + Coord.math(0, 0, 1), screen_location, screen_size)
            entity.update(dt, onscreen)
            if onscreen: 
                self.entities_on_screen.append(entity)
                if (reciever := entity.serve_reciever()): 
                    self.shadows.add_receiver(reciever)
                
        
        resolve_collisions(self.spatial_hash_grid.get_possible_onscreen_collisions(*self.screen.get_bounding_box()))
        
        # Handle entity adds/removes that initaited in the update loop
        for entity in self.queued_removals: self.remove_entity(entity)
        for entity in self.queued_additions: self.add_entity(entity)
        
        self.queued_removals.clear()
        self.queued_additions.clear()

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def get_entity_render_objs(self, player: Player) -> List[RenderObj]:
        """
            Collect RenderObjs for everything currently on-screen:
            - entity render objs
            - entity-provided shadow sprites (if any)
            - computed projected shadows from the Shadows system (ellipse caster)
        """
        render_objs = []
        for entity in self.entities_on_screen:
            render_objs.extend(entity.get_render_objs())
            if (shadow:= entity.serve_shadow()): render_objs.append(shadow)
        
        render_objs.extend(self.shadows.get_shadow_objs(player.get_shadow()))
        render_objs.sort(key= lambda r_obj: r_obj.render_order)

        return render_objs
    
    def get_and_removed_chunk_entities(self, chunk: Chunk) -> set[Entity]:
        """ Return entities in a chunk region AND remove them from both """
        x, y, _ = chunk.location.location
        removed_entities = self.spatial_hash_grid.get_entities_in_range(x, y, chunk.SIZE, chunk.SIZE, remove_entities=True)
        try:
            for entity in removed_entities: del self.entities[entity.id]
        except Exception as e:
            print(f"Entity of type: {entity.__class__} caused exception")
            raise e
        return removed_entities

    def get_chunk_entities(self, chunk: Chunk) -> set[Entity]:
        """ Return entities in a chunk region (does not remove them) """
        x, y, _ = chunk.location.location
        return self.spatial_hash_grid.get_entities_in_range(x, y, chunk.SIZE, chunk.SIZE)
    
    def get_entities_in_range(
        self, 
        base_location: Coord, 
        radius: int, 
        filter: Callable[[Entity], bool] = lambda _: True
        ) -> set[Entity]:
        """ Return entities within a radius of a world location """

        x, y, _ = base_location.copy().update_as_world_coord(-radius, radius).location
        entities = self.spatial_hash_grid.get_entities_in_range(x, y, radius * 2, radius * 2, strict=False)
        return {
            entity for entity in entities if filter(entity) and base_location.euclidean_2D(entity.location) <= radius
        }


class EntityManagerSubscriber:
    """
        Interface/protocol for objects that want to be notified when entities are removed.
    """

    def recieve_death_event(entity: Entity):
        pass

