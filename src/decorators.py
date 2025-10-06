import numpy as np
from functools import wraps
from regestries import ENTITY_REGISTRY, SHADOW_ENTITY_REGISTRY
from system.entities.base_entity import BaseEntity
from utils.coords import Coord
from utils.types.shade_levels import ShadeLevel

def singleton(cls):
    """Make a class a singleton."""
    instances = {}
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


def register_entity(cls):
    """ Adds different entity types to a regestry so that the can be saved and loaded together"""
    if not issubclass(cls, BaseEntity):
        raise TypeError("Only classes that inherit from BaseEntity can be added to registry")
    
    if not hasattr(cls, "jsonify"):
            raise AttributeError(f"{cls.__name__} has no jsonify method")

    ENTITY_REGISTRY[cls.__name__] = cls
    orig = cls.jsonify
    @wraps(orig)
    def new_jsonify(self, *args, **kwargs):
        json = orig(self, *args, **kwargs)
        json["classname"] = self.__class__.__name__
        return json

    cls.jsonify = new_jsonify
    return cls


def generate_shadow(
        length: float, width: float, fade: float = 0, 
        override_serve_shadow_entity: bool = True, shade_level: ShadeLevel = ShadeLevel.GROUND
    ):
    """ Generates an elliptical shadow for the entity """
    from system.entities.entity import Entity
    from system.render_obj import RenderObj
    def decorator(cls: Entity):
        if not issubclass(cls, Entity):
            raise TypeError("Only classes that inherit from BaseEntity can be added to registry")
        
        cls.SHADOW_ID = -1
        SHADOW_ENTITY_REGISTRY[cls] = (length, width, fade)

        if override_serve_shadow_entity:
           
            def serve_shadow(self):
                draw_location = self.draw_location() - self.render_offset.location[:-1] + np.array([-length * Coord.BASIS[0, 0], -width * Coord.BASIS[1, 0]])
                draw_location[1] -= np.floor(self.location.z * Coord.BASIS[1, 2])
                return RenderObj(
                    self.SHADOW_ID,
                    draw_location,
                    (shade_level, self.location.x, self.location.y, self.location.z),
                    isShadow=True
                )

            cls.serve_shadow = serve_shadow

        return cls
    return decorator
