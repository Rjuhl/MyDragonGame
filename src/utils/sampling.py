import random
from bisect import bisect_left
from typing import Tuple, List, Any

def sample_from_weighted_list(weights: List[Tuple[Any, int]]) -> int:
    """ 
    Given (ITEM, weights) returns random id influenced by the weights
    Implementation: build cumulative sums and binary search.
    """
    csum, sums, ids = 0, [], []
    for id, weight in weights:
        csum += weight
        sums.append(csum)
        ids.append(id)
    return ids[bisect_left(sums, random.randint(0, csum))]