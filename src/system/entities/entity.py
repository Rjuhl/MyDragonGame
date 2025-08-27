from system.id_generator import id_generator

class Entity:
    def __init__(self, location, size, imd_id, render_size): # Use pygame rects
        self.id = id_generator.get_id()
        self.location = location
        self.size = size # Determines hitbox
        self.prev_location = size
        self.img_id = imd_id
        self.render_size = render_size # Determines where to render
        self.lifespan = 0

        self.movement_subscribers = []
    
    def move(self, movement_vec, with_listeners=True):
        # Need to update prev location to use for collisions in the future
        self.prev_location = self.location.copy()
        self.location += movement_vec

        if with_listeners:
            for movement_subscriber in self.movement_subscribers:
                movement_subscriber.receive_movement_event(self)

        return self
    
    def add_movement_subscriber(self, subscriber):
        self.movement_subscribers.append(subscriber)
        return self
    
    def remove_movement_subscriber(self, subscriber):
        self.movement_subscribers.remove(subscriber)
        return self
    
    def update(self):
        self.lifespan += 1
        return self

