import argparse
import subprocess

APP_NAME = "MyDragonGame"
ENTRY_POINT = "src/game_name.py"
ASSETS_DIR = "assets"

def build_mac():
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--icon", "assets/my_dragon_game_app_icon.icns",
        "--add-data", f"{ASSETS_DIR}:assets",
        ENTRY_POINT,
    ]
    print(f"Building for macOS: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def build_windows():
    cmd = [
        "pyinstaller",
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--noconsole",
        "--icon", "assets/my_dragon_game_app_icon.ico",
        "--add-data", f"{ASSETS_DIR};assets",
        ENTRY_POINT,
    ]
    print(f"Building for Windows: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description="Build dist for MyDragonGame")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-m", "--mac", action="store_true", help="Build for macOS")
    group.add_argument("-w", "--windows", action="store_true", help="Build for Windows")
    args = parser.parse_args()

    if args.mac:
        build_mac()
    elif args.windows:
        build_windows()

if __name__ == "__main__":
    main()
