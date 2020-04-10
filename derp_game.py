import asyncio
import logging
import sys
import derplib.game as libgame
from derplib.errors import CharacterInUse, InvalidCharacter
from derplib.character import Character, Character_Flags
import derplib.net as dnet
from derplib.room import Room
from derplib.lurktype import LurkType
import json

log = logging.getLogger('game')

class derp_game():

    game = libgame.Game()
    game.initial_points = 100
    game.description = 'Welcome to DerpLurk, feel free to derp around.'
    # key: Character name
    # value: character
    characters = {}
    # list of rooms in the game
    rooms = {}

    def __init__(self):
        self.__load_data("data.json")
        # self.rooms[0] = Room(self, 'main room', 0, 'game lobby', [1], [])
        # self.rooms[1] = Room(self, 'second room', 1, 'another room', [0], [])

        # monster1 = Character()
        # monster1.name = "Bad guy"
        # monster1.description = "a really bad guy"
        # monster1.current_room = 1
        # monster1.flags = Character_Flags.ALIVE | Character_Flags.READY | Character_Flags.STARTED | Character_Flags.MONSTER
        # monster1.stats.attack = 20
        # monster1.stats.defense = 20
        # monster1.stats.regen = 20
        # monster1.stats.health = 20
        # monster1.stats.gold = 100
        # self.characters[monster1.name] = monster1
        # self.rooms[1].characters.append(monster1.name)

    def __load_data(self, file):
        with open(file) as f:
            data = json.load(f)

        for room in data["Rooms"]:
            number = room["number"]
            name = room["name"]
            description = room["description"]
            connections = room["connections"]
            self.rooms[number] = Room(self, name, number, description, connections, [])
        
        for monster in data["Monsters"]:
            name = monster["name"]
            description = monster["description"]
            room = monster["room"]
            attack = monster["attack"]
            defense = monster["defense"]
            regen = monster["regen"]
            health = monster["health"]
            gold = monster["gold"]

            c = Character()
            c.name = name
            c.description = description
            c.current_room = room
            c.stats.attack = attack
            c.stats.defense = defense
            c.stats.regen = regen
            c.stats.health = health
            c.stats.gold = gold
            c.flags = Character_Flags.ALIVE | Character_Flags.READY | Character_Flags.STARTED | Character_Flags.MONSTER
            self.characters[name] = c
            self.rooms[room].characters.append(name)

    async def initialize_character(self, character, writer):
        name = character.name
        if name in self.characters:
            char = self.characters[name]
            if char.writer == None:
                char.writer = writer
                log.debug(f'found character: {name}')
                await dnet.send_ACCEPT(writer, LurkType.CHARACTER)
                update = self.rooms[char.current_room].full_update_for_player_pack()
                char.writer.write(update)
                asyncio.create_task(char.writer.drain())
                return char
            else:
                raise CharacterInUse(name)
        else:
            valid_character = self.__validate_new_character(character)
            valid_character.writer = writer
            self.characters[name] = valid_character
            await dnet.send_ACCEPT(writer, LurkType.CHARACTER)
            await self.rooms[valid_character.current_room].enter_room(valid_character.name)
            log.debug(f'created character: {name}: {valid_character}')
            return valid_character

    def __validate_new_character(self, c):
        s = c.stats
        if s.attack < 0 or s.defense < 0 or s.regen < 0:
            raise InvalidCharacter(c.name, 'Negative stats are not allowed')
        if s.attack + s.defense + s.regen <= self.game.initial_points:
            c.stats.health = 100
            c.stats.gold = 0
            c.stats.current_room = 0
            #new character should be alive and optionally join battle
            newflags = Character_Flags.ALIVE
            newflags |= c.flags & Character_Flags.JOIN_BATTLE
            newflags |= Character_Flags.READY
            c.flags = newflags
            return c
        else:
            raise InvalidCharacter(c.name, 'Stats are over initial point limit')

    def disconnect_character(self, name):
        c = self.characters[name]
        c.writer = None # remove writer connection
        # c.flags &= ~Character_Flags.ALIVE # Character does not die when leaving

    def get_character_writer(self, name):
        if name in self.characters:
            return self.characters[name].writer
        else:
            return None

    #TODO Verify or should this go into room
    async def send_message(self, recipient, sender, message):
        room = self.rooms[self.characters[sender].current_room]
        result = await room.send_message(recipient, sender, message)
        return result
        # data = dnet.pack_MESSAGE(recipient, sender, message)
        # if recipient in self.characters and self.characters[recipient].writer != None:
        #     asyncio.create_task(self.update_character(recipient, data))
        # else:
        #     return "Not connected"


    async def update_client_room(self, name):
        clients_char, writer = self.characters[name]
        curr_room = clients_char.current_room
        # await clients_char.send(writer)
        # Batch send full room update
        # main room
        writer.write(self.rooms[curr_room].pack())
        # connections
        for rnum in self.rooms[curr_room].connections:
            writer.write(self.rooms[rnum].pack_as_connection())
        # all characters including main character (possibly out of order)
        for cname in self.rooms[curr_room].characters:
            writer.write(self.characters[cname][0].pack())

        # flush it all out
        await writer.drain()

    async def start_character(self, name):
        c = self.characters[name]
        c.flags |= Character_Flags.STARTED
        asyncio.create_task(self.rooms[c.current_room].update_all_characters())

    async def change_room(self, name, number):
        room = self.rooms[self.characters[name].current_room]
        result = await room.leave_room(name, number)
        return result

    async def fight(self, name):
        c = self.characters[name]
        if c.flags & Character_Flags.ALIVE == 0:
            return "DEAD"
        room = self.rooms[c.current_room]
        result = await room.fight(name)
        return result

    async def loot(self, name, target):
        code = await self.rooms[self.characters[name].current_room].loot(name, target)
        return code

    # async def broadcast_character_update(self, name):
    #     """update everyone in the same room as name"""
    #     c,w = self.characters[name]
    #     data = c.pack()
    #     character_list = self.rooms[c.current_room].characters
    #     for char in character_list:
    #         asyncio.create_task(self.update_character(char, data))

