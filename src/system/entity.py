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

    def check_collision(self, other):
        """AABB overlap test in 3D.
        inclusive=True means touching faces/edges count as a collision.
        """
        if not isinstance(other, Entity):
            raise NotImplementedError("Collision is only defined between Entity instances.")

        # Self box min/max on each axis
        ax1, ay1, az1 = self.location.x, self.location.y, self.location.z
        ax2, ay2, az2 = ax1 + self.size.x, ay1 + self.size.y, az1 + self.size.z

        # Other box min/max
        bx1, by1, bz1 = other.location.x, other.location.y, other.location.z
        bx2, by2, bz2 = bx1 + other.size.x, by1 + other.size.y, bz1 + other.size.z

        # Ensure correct ordering in case size components are negative
        ax1, ax2 = (ax1, ax2) if ax1 <= ax2 else (ax2, ax1)
        ay1, ay2 = (ay1, ay2) if ay1 <= ay2 else (ay2, ay1)
        az1, az2 = (az1, az2) if az1 <= az2 else (az2, az1)
        bx1, bx2 = (bx1, bx2) if bx1 <= bx2 else (bx2, bx1)
        by1, by2 = (by1, by2) if by1 <= by2 else (by2, by1)
        bz1, bz2 = (bz1, bz2) if bz1 <= bz2 else (bz2, bz1)

    
        overlap_x = (ax1 <= bx2) and (bx1 <= ax2)
        overlap_y = (ay1 <= by2) and (by1 <= ay2)
        overlap_z = (az1 <= bz2) and (bz1 <= az2)

        return overlap_x and overlap_y and overlap_z

    def update(self):
        self.lifespan += 1
        return self