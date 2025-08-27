def generate_unique_entity_pair_string(entity1, entity2):
    return str(entity1.id) + str(entity2.id) if entity1.id < entity2.id else str(entity2.id) + str(entity1.id)