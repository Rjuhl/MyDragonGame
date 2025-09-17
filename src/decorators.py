from functools import wraps
from regestries import ENTITY_REGISTRY
from system.entities.base_entity import BaseEntity

def singleton(cls):
    """Make a class a singleton."""
    instances = {}
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

# TODO: [BUG] Since thus applied to Entitiy and children its nesting the json with the change
def register_entity(cls):
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