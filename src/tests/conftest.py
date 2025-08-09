import pytest
from world.utils.coords import Coord

@pytest.fixture
def base_coord():
    return Coord.world(0, 0)