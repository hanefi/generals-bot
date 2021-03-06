"""
    @ Harris Christiansen (code@HarrisChristiansen.com)
    Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
    Path Collect Both: Collects troops along a path, and attacks outward using path.
"""

import logging

import startup
from base import bot_moves

# Show all logging
logging.basicConfig(level=logging.INFO)

######################### Move Making #########################

_bot = None
_map = None


def make_move(current_bot, current_map):
    global _bot, _map
    _bot = current_bot
    _map = current_map

    # Make Move
    if _map.turn % 8 == 0:
        if move_collect_to_path():
            return
    if _map.turn % 2 == 0:
        if make_primary_move():
            return
    if not move_outward():
        if not move_collect_to_path():
            make_primary_move()
    return


def place_move(source, dest):
    _bot.place_move(source, dest, move_half=bot_moves.should_move_half(_map, source, dest))


######################### Primary Move Making #########################

def make_primary_move():
    update_primary_target()
    if len(_map.path) > 1:
        return move_primary_path_forward()
    elif _target is not None:
        new_primary_path()
    return False


######################### Primary Targeting #########################

_target = None
_path_position = 0


def update_primary_target():
    global _target
    moves_left = 100
    path_length = len(_map.path)
    if path_length > 2:
        moves_left = path_length - _path_position - 1

    if _target is not None:  # Refresh Target Tile State
        _target = _map.grid[_target.y][_target.x]
        if moves_left <= 2:  # Make target appear smaller to avoid un-targeting # TEMP-FIX
            _target.army /= 5
    new_target = _map.find_primary_target(_target)

    if _target != new_target:
        _target = new_target
        new_primary_path(restore_old_position=True)


######################### Primary Path #########################

def move_primary_path_forward():
    global _path_position
    try:
        source = _map.path[_path_position]
    except IndexError:
        # logging.debug("Invalid Current Path Position")
        return new_primary_path()

    if source.tile != _map.player_index or source.army < 2:  # Out of Army, Restart Path
        # logging.debug("Path Error: Out of Army (%d,%d)" % (source.tile, source.army))
        return new_primary_path()

    try:
        dest = _map.path[_path_position + 1]  # Determine Destination
        if dest.tile == _map.player_index or source.army > (dest.army + 1):
            place_move(source, dest)
        else:
            # logging.debug("Path Error: Out of Army To Attack (%d,%d,%d,%d)" % (dest.x,dest.y,source.army,dest.army))
            return new_primary_path()
    except IndexError:
        # logging.debug("Path Error: Target Destination Out Of List Bounds")
        return new_primary_path(restore_old_position=True)

    _path_position += 1
    return True


def new_primary_path(restore_old_position=False):
    global _bot, _path_position, _target

    # Store Old Tile
    old_tile = None
    if _path_position > 0 and len(_map.path) > 0:  # Store old path position
        old_tile = _map.path[_path_position]
    _path_position = 0

    # Determine Source and Path
    source = _map.find_city()
    if source is None:
        source = _map.find_largest_tile(includeGeneral=True)
    _map.path = source.path_to(_target)  # Find new path to target

    # Restore Old Tile
    if restore_old_position and old_tile is not None:
        for i, tile in enumerate(_map.path):
            if (tile.x, tile.y) == (old_tile.x, old_tile.y):
                _path_position = i
                return True

    return False


######################### Move Outward #########################

def move_outward():
    (source, dest) = bot_moves.move_outward(_map, _map.path)
    if source:
        place_move(source, dest)
        return True
    return False


######################### Collect To Path #########################

def find_collect_path():
    # Find Largest Tile
    source = _map.find_largest_tile(notInPath=_map.path, includeGeneral=0.33)
    if source is None or source.army < 4:
        _map.collect_path = []
        return _map.collect_path

    # Determine Target Tile
    dest = None
    if source.army > 40:
        dest = source.nearest_target_tile()
    if dest is None:
        dest = source.nearest_tile_in_path(_map.path)

    # Return Path
    return source.path_to(dest)


def move_collect_to_path():
    # Update Path
    _map.collect_path = find_collect_path()

    # Perform Move
    (move_from, move_to) = bot_moves.move_path(_map.collect_path)
    if move_from is not None:
        place_move(move_from, move_to)
        return True

    return False


######################### Main #########################

# Start Game
if __name__ == '__main__':
    startup.startup(make_move, "PurdueBot-P2")
