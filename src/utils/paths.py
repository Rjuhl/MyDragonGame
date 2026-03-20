import sys
from pathlib import Path


def assets_root() -> Path:
    """Path to the bundled assets directory. Works both in dev and PyInstaller dist."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS) / 'assets'
    return Path(__file__).parent.parent.parent / 'assets'


def data_root() -> Path:
    """Path to the user-writable data directory. Works both in dev and PyInstaller dist."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'data'
    return Path(__file__).parent.parent.parent / 'data'
