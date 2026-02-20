import time
from functools import wraps
from decorators import singleton
from typing import Dict, Tuple
from collections import defaultdict
from constants import DEGUB_ON

class LightMetric:
    def __init__(self):
        self.times: Dict[str, Tuple[int, float]] = defaultdict(lambda: [0, 0])

    def add_time(self, name: str, time: float, base=False):
        self.times[name] = (self.times[name][0] + 1, self.times[name][1] + time)
        if base: 
            self._print_times()
            self.times.clear()
    
    def _print_times(self):
        for f, (times, time) in self.times.items():
            print(f"{f} called {times} times for a total of {time:.6f} seconds")
        print("\n")

light_metric = LightMetric()


def timeit(*, base=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not DEGUB_ON: return func(*args, **kwargs)
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            light_metric.add_time(func.__name__, elapsed, base=base)
            return result
        return wrapper
    return decorator

