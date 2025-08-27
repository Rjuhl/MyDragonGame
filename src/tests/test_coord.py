import pytest
from utils.coords import Coord
from conftest import base_coord

@pytest.mark.parametrize(
    'init_coord, world_coord, view_coord, chunk_coord, screen_coord',
    [
        pytest.param((0, 0), (0, 0), (0, 0), (0, 0), Coord.world(0, 0), id="sanity_check"),

    ]
)
def test_world_coord_init(init_coord, world_coord, view_coord, chunk_coord, screen_coord):
    coord = Coord.world(*init_coord)
    assert coord.as_world_coord() == world_coord
    assert coord.as_view_coord(screen_coord) == view_coord
    assert coord.as_chunk_coord() == chunk_coord 


def test_screen_coord_init():
    pass


def test_chunk_coord_init():
    pass

# @pytest.mark.parametrize(
#     'base_coord, movement, screen offset, expected_world, expected_screen',
#     [
#         pytest.param(base_coord(), (0, -1),  base_coord(), (0, -1), ()id="sanity_check"),
#     ]
# )
# def test_world_coord_movement():
#     pass


def test_screen_coord_movement():
    pass


def test_chunk_coord_movement():
    pass
