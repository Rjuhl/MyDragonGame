from system.id_generator import id_generator

class Entity:
    def __init__(self, location, size, img_id, render_offset): # Use pygame rects
        self.id = id_generator.get_id()
        self.location = location
        self.size = size # Determines hitbox
        self.prev_location = size
        self.img_id = img_id
        self.render_offset = render_offset # Determines where to render
        self.lifespan = 0

        self.movement_subscribers = []
        self.mananger = None
    
    def move(self, movement_vec, with_listeners=True):
        # Need to update prev location to use for collisions in the future
        self.prev_location = self.location.copy()
        self.location += movement_vec

        if with_listeners:
            for movement_subscriber in self.movement_subscribers:
                movement_subscriber.receive_movement_event(self)

        return self
    
    def bind_to_manager(self, manager):
        self.mananger = manager

    def kill(self):
        if self.mananger:
            self.mananger.remove_entity(self)
    
    def add_movement_subscriber(self, subscriber):
        self.movement_subscribers.append(subscriber)
        return self
    
    def remove_movement_subscriber(self, subscriber):
        self.movement_subscribers.remove(subscriber)
        return self
    
    def update(self, dt, onscreen=True):
        self.lifespan += dt
        return self

    def save(self):
        pass

    def load(self, data):
        pass

    def handle_collision(self, self_velocity, other_entity, other_velocity, timestep):
        pass
