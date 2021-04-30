from game_state import GameState
import asyncio
import random
import os
import datetime
import helpers   # import our helper functions
# from . import helpers


MIN_DISTANCE_TO_ADVERSARY = 3

uri = os.environ.get(
    'GAME_CONNECTION_STRING') or "ws://127.0.0.1:3000/?role=agent&agentId=agentId&name=myAgent"


actions = ["up", "down", "left", "right"]

AgentID = "0"

class Agent():
    def __init__(self):
        self._client = GameState(uri)

        self._client.set_game_tick_callback(self._on_game_tick)
        loop = asyncio.get_event_loop()
        connection = loop.run_until_complete(self._client.connect())
        tasks = [
            asyncio.ensure_future(self._client._handle_messages(connection)),
        ]

        loop.run_until_complete(asyncio.wait(tasks))

    def _get_bomb_to_detonate(self, game_state) -> [int, int] or None:
        agent_number = game_state.get("connection").get("agent_number")
        AgentID = agent_number
        entities = self._client._state.get("entities")
        bombs = list(filter(lambda entity: entity.get(
            "owner") == agent_number and entity.get("type") == "b", entities))
        bomb = next(iter(bombs or []), None)
        if bomb != None:
            return [bomb.get("x"), bomb.get("y")]
        else:
            return None

    async def _on_game_tick(self, tick_number, game_state):

        # Base variables
        
        my_id = str(game_state["connection"]["agent_number"]) 
        if my_id == "1": 
            adversary_id = "0" 
        else: 
            adversary_id = "1"
        my_location = game_state["agent_state"][my_id]["coordinates"] 
        adversary_location = game_state["agent_state"][adversary_id]["coordinates"] 
        ammo = game_state["agent_state"][my_id]["inventory"]["bombs"]  
        adversary_ammo = game_state["agent_state"][adversary_id]["inventory"]["bombs"]  
        hp = game_state["agent_state"][my_id]["hp"]
        adversary_hp = game_state["agent_state"][adversary_id]["hp"]

        log(f"me: {my_id} HP: {hp} ammo: {ammo} | adv: {adversary_id} HP: {adversary_hp} ammo: {adversary_ammo}")


        # get key items
        bombs = helpers.get_bombs(game_state) 
        ammo_cache = helpers.get_ammo(game_state) 
        powerups = helpers.get_powerups(game_state) 

        min_distance = helpers.MIN_DISTANCE

        # get location state
        surrounding_tiles = helpers.get_surrounding_tiles(my_location)
        extended_surrounding_tiles = helpers.get_extended_surrounding_tiles(my_location)
        non_wall_tiles = helpers.get_questionable_tiles(surrounding_tiles, game_state)
        safe_tiles = helpers.get_safe_tiles(surrounding_tiles, game_state)
        empty_tiles = helpers.get_empty_tiles(surrounding_tiles, game_state)

        print("My location", game_state["agent_state"][my_id]["coordinates"], "non-wall tiles", non_wall_tiles)


        bombs_in_range = helpers.get_bombs_in_range(my_location, bombs)
        ammo_in_range = helpers.get_ammo_in_range(my_location, ammo_cache)
        powerups_in_range = helpers.get_powerups_in_range(my_location, powerups)


        # update danger cache
        helpers.update_bomb_list(game_state)
        helpers.update_explosion_list(game_state)
        
        # order of tasks:
            # 1 escape a bomb at my feet - go anywhere
            # 2 get safe tiles
        nearest_bomb = helpers.get_nearest_bomb(bombs, my_location)
        bomb_ticks = helpers.get_ticks_for_bomb(nearest_bomb)

        action = random.choice(actions)

        # if I'm on a bomb, I should probably move
        if helpers.entity_at(my_location[0],my_location[1],game_state) == 'b':
            log(f"I'm on a bomb!")
            if non_wall_tiles:
                if powerups_in_range:
                    action = move_towards_powerup(surrounding_tiles, powerups, my_location)
                elif ammo_in_range:
                    action = move_towards_ammo(surrounding_tiles, ammo_cache, my_location)
                else:
                    action = run_from_bomb(surrounding_tiles, bombs, my_location)
            else:
                action = no_move()

        # if we're near a bomb, we should also probably move
        # update: only run from the bomb if there are not many ticks left
        elif bombs_in_range and bomb_ticks < 4:
            log("There's a bomb nearby!")
            if non_wall_tiles:
                run_from_bomb(surrounding_tiles, bombs, my_location)
            else:
                action = no_move()

        elif powerups_in_range:
            if non_wall_tiles:
                action = move_towards_powerup(surrounding_tiles, powerups, my_location)
            else:
                action = no_move()

        # if there's some ammo in range - try to pickup
        elif ammo_in_range:
            if non_wall_tiles:
                action = move_towards_ammo(surrounding_tiles, ammo_cache, my_location)
            else:
                action = no_move()

        # if there are no bombs in range
        else:

            # but first, let's check if we have any ammo
            distance_to_other_player = helpers.manhattan_distance(my_location, adversary_location)
            log (f"Distance to player: {distance_to_other_player} | me: {my_location}, adv: {adversary_location}")

            if distance_to_other_player < MIN_DISTANCE_TO_ADVERSARY: 
                if ammo > 0:
                    # we've got ammo + we're near the adversary, let's place a bomb
                    log("Drop a bomb! 💣")
                    action = "bomb"
                else:
                    # run away!
                    log("RUN AWAY!!!! 🏃‍♂️")
                    adversary_move = helpers.get_furthest_tile_from_closest_item(surrounding_tiles, [adversary_location], my_location)
                    action = helpers.move_to_tile(my_location, adversary_move) 

            else:
                # no ammo or not close to adversary, chase adversary
                log("chase adversary 🦸‍♂️")
                adversary_move = helpers.get_nearest_tile_to_closest_item(surrounding_tiles, [adversary_location], my_location)
                action = helpers.move_to_tile(my_location, adversary_move) 

        log (f"Moving '{action}'")
        # logic to send valid action packet to game server
        if action in ["up", "left", "right", "down"]:
            await self._client.send_move(action)
        elif action == "bomb":
            await self._client.send_bomb()
        elif action == "detonate":
            bomb_coordinates = self._get_bomb_to_detonate(game_state)
            if bomb_coordinates != None:
                x, y = bomb_coordinates
                await self._client.send_detonate(x, y)
        else:
            print(f"Unhandled action: {action}")


def move_towards_powerup(surrounding_tiles, powerups, my_location):
    log("moving towards a powerup 🧨")
    powerup_tile = helpers.get_closest_tile_to_nearest_powerup(surrounding_tiles, powerups, my_location)
    return helpers.move_to_tile(my_location, powerup_tile)

def move_towards_ammo(surrounding_tiles, ammo_cache, my_location):
    log("moving towards some ammo 💸")
    ammo_tile = helpers.get_closest_tile_to_nearest_ammo(surrounding_tiles, ammo_cache, my_location)
    return helpers.move_to_tile(my_location, ammo_tile)

def run_from_bomb(surrounding_tiles, bombs, my_location):
    log("escaping a bomb! 💥")
    safest_tile = helpers.get_safest_tile(surrounding_tiles, bombs, my_location)
    return helpers.move_to_tile(my_location, safest_tile)

def no_move():
    log(f"no free spot - do nothing :(")
    return ''

def log(message: str):
    if AgentID == "0":
        print(f"{datetime.datetime.now()} - {message}")


def main():
    Agent()


if __name__ == "__main__":
    main()
