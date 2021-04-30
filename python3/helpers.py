import os


MIN_DISTANCE = 10
SAFETY_MARGIN = 2
BOMB_LIST = {}
BLAST_LIST = {}

BLAST_DURATION_TICKS = os.environ.get('BLAST_DURATION_TICKS') or 10
AMMO_DURATION_TICKS = os.environ.get('AMMO_DURATION_TICKS') or 40
BOMB_DURATION_TICKS = os.environ.get('BOMB_DURATION_TICKS') or 40


# given a tile location as an (x,y) tuple
# return the surrounding tiles as a list
def get_surrounding_tiles(location):

    # find all the surrounding tiles relative to us
    # location[0] = x-index; location[1] = y-index
    tile_up = (location[0], location[1]+1)  
    tile_down = (location[0], location[1]-1)    
    tile_left = (location[0]-1, location[1])
    tile_right = (location[0]+1, location[1])        
    
    # combine these into a list
    all_surrounding_tiles = [tile_up, tile_down, tile_left, tile_right]
    
    # include only the tiles that are within the game boundary
    # empty list to store our valid surrounding tiles
    valid_surrounding_tiles = []
    
    # loop through tiles
    for tile in all_surrounding_tiles:
        # check if the tile is within the boundaries of the game
        # note: the map is size 9x9
        if tile[0] >= 0 and tile[0] < 9 and \
            tile[1] >= 0 and tile[1] < 9: 
            # add valid tiles to our list
            valid_surrounding_tiles.append(tile)
    
    return valid_surrounding_tiles


def get_extended_surrounding_tiles(location):
    # tile pattern (c= closest, t = tick + 1 potential location)
    #       t
    #     t c t
    #   t c P c t
    #     t c t
    #       t
    
    extended_surrounding_tiles = [
        (location[0], location[1]+2),      # t
        (location[0]-1, location[1]+1),    # t
        (location[0], location[1]+1),      # c
        (location[0]+1, location[1]+1),    # t
        (location[0]-2, location[1]),      # t
        (location[0]-1, location[1]),      # c
        (location[0]+1, location[1]),      # c
        (location[0]+2, location[1]),      # t
        (location[0]-1, location[1]-1),    # t
        (location[0], location[1]-1),      # c
        (location[0]+1, location[1]-1),    # t
        (location[0], location[1]-2),      # t
    ]

    valid_tiles = []
    for tile in extended_surrounding_tiles:
        if tile[0] >=0 and tile[0] < 9 and tile[1] >=0 and tile[1]:
            valid_tiles.append(tile)

    return valid_tiles





# this function returns the object tag at a location
def entity_at(x,y,game_state):
    for entity in game_state["entities"]:
        if entity["x"] == x and entity["y"] == y:
            return entity["type"]

# given a list of tiles
# return the ones which are actually empty
def get_empty_tiles(tiles,game_state):

	# empty list to store our empty tiles
	empty_tiles = []

	for tile in tiles:
		if entity_at(tile[0],tile[1],game_state) is None:
			# the tile isn't occupied, so we'll add it to the list
			empty_tiles.append(tile)

	return empty_tiles


# implement safe tiles, any tile that is empty, or has ammo/powerup in it.
def get_safe_tiles(tiles, game_state):
    safe_tiles = []

    for tile in tiles:
        tile_entity = entity_at(tile[0], tile[1], game_state)
        if tile_entity is None:
            safe_tiles.append(tile)
        else:
            if tile not in BLAST_LIST:
                if tile_entity == "a" or tile_entity == "bp":
                    safe_tiles.append(tile)
    return safe_tiles

# implement questionable tiles, any tile that is empty, or has no blast in it.
def get_questionable_tiles(tiles, game_state):
    questionable_tiles = []

    for tile in tiles:
        tile_entity = entity_at(tile[0], tile[1], game_state)
        if tile_entity is None:
            questionable_tiles.append(tile)
        else:
            if tile not in BLAST_LIST and tile_entity not in ['x', 'm', 'o', 'w']:
                questionable_tiles.append(tile)
    return questionable_tiles


# given an adjacent tile location, move us there
def move_to_tile(location, tile):

    # see where the tile is relative to our current location
    diff = tuple(x-y for x, y in zip(location, tile))
    
    # return the action that moves in the direction of the tile
    if diff == (0,1):
        action = 'down'
    elif diff == (0,-1):
        action = 'up'
    elif diff == (1,0):
        action = 'left'
    elif diff == (-1,0):
        action = 'right'
    else:
        action = ''
    
    return action

# returns the manhattan distance between two tiles, calculated as:
# 	|x1 - x2| + |y1 - y2|
def manhattan_distance(start, end):

	distance = abs(start[0] - end[0]) + abs(start[1] - end[1])
	
	return distance

# return a list of bombs on the map
def get_bombs(game_state):
    list_of_bombs = []
    for i in game_state["entities"]:
        if i["type"] == "b":
            x = i["x"]
            y = i["y"]
            list_of_bombs.append((x,y))

    return list_of_bombs


def get_ammo(game_state):
    list_of_ammo = []
    for i in game_state["entities"]:
        if i["type"] == "a":
            x = i["x"]
            y = i["y"]
            list_of_ammo.append((x,y))

    return list_of_ammo


def get_blasts(game_state):
    list_of_blasts = []
    for i in game_state["entities"]:
        if i["type"] == "x":
            x = i["x"]
            y = i["y"]
            list_of_blasts.append((x,y))

    return list_of_blasts


def get_powerups(game_state):
    list_of_powerups = []
    for i in game_state["entities"]:
        if i["type"] == "bp":
            x = i["x"]
            y = i["y"]
            list_of_powerups.append((x,y))

    return list_of_powerups

# return a list of the item positions that are nearby
def get_items_in_range(location: tuple, items: list) -> list:
    """Get the items in range of the player """
    items_in_range = []
    for item in items:
        distance = manhattan_distance(location, item)
        if distance <= MIN_DISTANCE:
            items_in_range.append(item)
    return items_in_range



def get_bombs_in_range(location: tuple, bombs: list) -> list:
    """Get the bombs in range of the player """
    return get_items_in_range(location, bombs)

def get_ammo_in_range(location: tuple, ammo: list) -> list:
    """Get the ammo in range of the player """
    return get_items_in_range(location, ammo)

def get_powerups_in_range(location: tuple, powerups: list) -> list:
    """Get the ammo in range of the player """
    return get_items_in_range(location, powerups)

# given a list of tiles and bombs
# find the tile that's safest to move to
def get_safest_tile(tiles, bombs, location):
    return get_furthest_tile_from_closest_item(tiles, bombs, location)

def get_closest_tile_to_nearest_ammo(tiles, ammo, player_location) -> tuple: 
    return get_nearest_tile_to_closest_item(tiles, ammo, player_location)

def get_closest_tile_to_nearest_powerup(tiles, powerups, player_location) -> tuple: 
    return get_nearest_tile_to_closest_item(tiles, powerups, player_location)



# =========================================
# helper functions 
# =========================================

# furthest tile from nearest item
def get_furthest_tile_from_closest_item(tiles_list, items_list, player_location) -> tuple:
    distances = get_distances_to_item(tiles_list, items_list, player_location)
    return max(distances, key=distances.get)

# closest tile to nearest item
def get_nearest_tile_to_closest_item(tiles_list, items_list, player_location) -> tuple:
    distances = get_distances_to_item(tiles_list, items_list, player_location)
    return min(distances, key=distances.get)

# distance calc for surrounding tiles and nearest item, distance method can be overloaded
def get_distances_to_item(tiles_list, items_list, player_location, distance_func=manhattan_distance) -> dict:
    closest_item = get_nearest_item(items_list, player_location, distance_func)

    manhattan_distances = {}
    for tile in tiles_list:
        distance = distance_func(tile, closest_item)
        manhattan_distances[tile] = distance
    return manhattan_distances



# func get bomb ticks
def update_bomb_list(game_state):
    bombs = get_bombs(game_state)
    for bomb in bombs:
        if bomb in BOMB_LIST:
            if BOMB_LIST[bomb]["ticks"] > 1:
                BOMB_LIST[bomb]["ticks"] -= 1
            else:
                try:
                    BOMB_LIST.pop(bomb)
                except: 
                    print("Couldn't remove bomb from list", bomb)
        else:
            BOMB_LIST[bomb]  = {
                "ticks": BOMB_DURATION_TICKS - SAFETY_MARGIN
            }

    print("Bombs", BOMB_LIST)

def update_explosion_list(game_state):
    blasts = get_blasts(game_state)
    for blast in blasts:
        if blast in BLAST_LIST:
            if BLAST_LIST[blast]["ticks"] > 1:
                BLAST_LIST[blast]["ticks"] -= 1
            else:
                try:
                    BLAST_LIST.pop(blast)
                except: 
                    print("Couldn't remove blast from list", blast)
        else:
            BLAST_LIST[blast]  = {
                "ticks": BLAST_DURATION_TICKS - SAFETY_MARGIN
            }
    print("Blasts", BLAST_LIST)

def get_ticks_for_bomb(bomb):
    try:
        return BOMB_LIST[bomb]["ticks"]
    except:
        return 0

def get_nearest_bomb(bombs, player_location):
    return get_nearest_item(bombs, player_location)

def get_nearest_item(items_list, player_location, distance_func=manhattan_distance):
    if len(items_list) == 0: 
        return None
    min_distance = MIN_DISTANCE
    closest_item = items_list[0]

    for item in items_list: 
        new_item_distance = distance_func(item, player_location)
        if new_item_distance < min_distance:
            min_distance = new_item_distance
            closest_item = item
    return closest_item



# func for potential bomb radius

# implement bomb tracking list with ticks

# check for potential bomb blast