import pytest
from utils.coords import Coord

@pytest.fixture
def base_coord():
    return Coord.world(0, 0)