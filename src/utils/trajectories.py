from utils.coords import Coord

def base_trajectory(age: float) -> Coord:
        return 24 * (-(((age - 600) / 600) ** 2) + 1)