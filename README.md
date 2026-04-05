
# MyDragonGame
MyDragonGame is an open-world isometric game built with Pygame. Play as a dragon that explores the world and the creatures that inhabit it. Beware of wizards that will attack you on sight and collect the power-up that they drop.  
<p align="center">
  <img src="https://github.com/user-attachments/assets/69df8427-1626-4cd9-b4e1-72c087753148" width="600" alt="gameplay demo">
</p>

# Install
To download a dmg or exe, you can go [here](https://rjuhl.github.io/my-dragon-game-download-website/index.html)
## Mac (Need Python 3.X downloaded)
```
git clone https://github.com/Rjuhl/MyDragonGame.git
cd MyDragonGame
python -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 src/game_name.py
```
## Windows (Need Python 3.X downloaded and Visual Studio Build Tools [C++])
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
git clone https://github.com/Rjuhl/MyDragonGame.git
cd MyDragonGame
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/game_name.py
```

> If crashing when entering the game on Windows, try switching all instances of pnoise to snoise in terrain_generator.py (will be fixed in biome update)

## Default Controls (can change in settings)
| Action | Key |
|--------|-----|
| Move | WASD or Arrow Keys |
| Fly Up | Space |
| Fly Down | Shift |
| Fire | Hold Left Click |
| Pause | Esc |

> **Tip:** While breathing fire, moving your mouse above the dragon arcs the flame upward, and moving it below the dragon arcs the mouse downward.

## Biomes
1. Grassland
2. Forest
3. Artic
4. Desert
