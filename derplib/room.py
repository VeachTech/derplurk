import socket
import asyncio
import logging
import struct
from .lurktype import LurkType
import derp_game
import derplib.net as dnet
from derplib.character import Character_Flags

log = logging.getLogger('Room')

class Room():
    
    # game = None
    # name = ''
    # number = 0
    # description = ''
    # connections = [] # list of rooms this one is connected to
    # characters = []

    def __init__(self, game, name, number, description, connections, characters):
        self.game = game
        self.name = name
        self.number = number
        self.description = description
        self.connections = connections
        self.characters = characters

    async def enter_room(self, name):
        #DONE get data of all current characters (before adding new one)
        existing_character_data = self.get_all_characters_info()
        #DONE send character room info + characters info
        room_data = self.get_rooms_info()
        char = self.game.characters[name]
        # apply regen health
        char.stats.health += char.stats.regen
        # log.debug(f'{char.name} entered room #{self.number}')

        if char.stats.health > 100:
            char.stats.health = 100
        char.writer.write(room_data + existing_character_data)
        #DONE update whole room of new character
        asyncio.create_task(char.writer.drain())
        # asyncio.create_task(self.update_one_character(name))
        #DONE add character name to list
        self.characters.append(name)
        await self.update_one_character(name)
        

    #TODO not informing others of left player, Uh, might be my client
    async def leave_room(self, name, number):
        char = self.game.characters[name]
        if char.flags & Character_Flags.ALIVE == 0:
            # log.debug(f'{char.name} is dead...')
            return "DEAD"

        if number in self.connections:
            #DONE change room number of character
            char.current_room = number
            #DONE remove character from list
            self.characters.remove(name)
            #DONE call enter room of appropiate room
            #asyncio.create_task(self.game.rooms[number].enter_room(name))
            await self.game.rooms[number].enter_room(name)
            #DONE update other characters of character leaving
            await self.update_one_character(name)
            return "Success"
        else:
            return "Invalid Room"

    async def fight(self, name):
        #DONE get players with join battle + named character
        players = [self.game.characters[name],]
        monsters = []
        for char in self.characters:
            if char != name:
                c = self.game.characters[char]
                if c.flags & Character_Flags.ALIVE:
                    if c.flags & Character_Flags.MONSTER:
                        monsters.append(c)
                    elif c.flags & Character_Flags.JOIN_BATTLE:
                        players.append(c)
        if not monsters:
            return "nofight"

        # log.debug('Players in battle:')
        # for player in players:
        #     log.debug(f'{player.name}, Health: {player.stats.health}')
        
        #TODO fight clalculations
        players_attack = 0
        monsters_attack = 0
        awarded_gold = 0
        for player in players:
            players_attack += player.stats.attack
        
        # log.debug(f'Players total attack: {players_attack}')
        
        #attack monsters
        log.debug('Monsters in battle')
        for monster in monsters:
            # log.debug(f'{monster.name}, Health {monster.stats.health}')
            damage = players_attack - monster.stats.defense
            if damage > 0:
                monster.stats.health -= damage
                if monster.stats.health <= 0:
                    monster.flags &= ~Character_Flags.ALIVE # Set to DEAD
                    # log.debug(f'{monster.name} died')
                    awarded_gold += 50
        
        # for monster in monsters:
        #     log.debug(f'Monster: {monster.name} now has health {monster.stats.health}')
        
        # get remaining monster damage
        for monster in monsters:
            if monster.flags & Character_Flags.ALIVE:
                monsters_attack += monster.stats.attack
        # log.debug(f'Monsters total attack: {monsters_attack}')
        
        # deal damage to players and give gold regardless of death
        for player in players:
            player.stats.gold += awarded_gold
            damage = monsters_attack - player.stats.defense
            if damage > 0:
                player.stats.health -= damage
                if player.stats.health <= 0:
                    player.flags &= ~Character_Flags.ALIVE
                    # log.debug(f'{player.name} died')

        # for player in players:
        #     log.debug(f'{player.name}, Health {player.stats.health}, Gold {player.stats.gold}')
        
        #TODO update all characters of new stats
        await self.update_all_characters()
        return "Success"

    async def loot(self, recipient, target):
        if target in self.characters:
            target_char = self.game.characters[target]
            recipient_char = self.game.characters[recipient]

            if target_char.flags & Character_Flags.ALIVE:
                return "Target Alive"
            else:
                recipient_char.stats.gold += target_char.stats.gold
                target_char.stats.gold = 0
                self.update_one_character(recipient)
                self.update_one_character(target)
                return "Looted"
        else:
            return "No Target"

    async def send_message(self, recipient, sender, message):
        char = self.game.characters[sender]
        if char.flags & Character_Flags.ALIVE == 0:
            return "DEAD"
        
        if recipient in self.characters:
            r = self.game.characters[recipient]
            data = dnet.pack_MESSAGE(recipient, sender, message)
            r.writer.write(data)
            asyncio.create_task(r.writer.drain())
            return "Success"
        else:
            return "Unable to send"

    def get_all_characters_info(self):
        data = b''
        for char in self.characters:
            data += self.game.characters[char].pack()
        return data

    async def update_one_character(self, name):
        data = self.game.characters[name].pack()

        writers = []
        for char in self.characters:
            writers.append(self.game.characters[char].writer)

        for w in writers:
            if w != None:
                w.write(data)
                asyncio.create_task(w.drain())

    def full_update_for_player_pack(self):
        data = self.get_rooms_info()
        data += self.get_all_characters_info()
        return data
    
    async def update_all_characters(self):
        data = b''
        
        for char in self.characters:
            data += self.game.characters[char].pack()

        writers = []
        for char in self.characters:
            writers.append(self.game.characters[char].writer)

        for w in writers:
            if w != None:
                w.write(data)
                asyncio.create_task(w.drain())

    def get_rooms_info(self):
        data = self.pack()

        for con in self.connections:
            data += self.game.rooms[con].pack_as_connection()
        
        return data
        # writers = []
        # for char in self.characters:
        #     writers.append(self.game.characters[char].writer)

        # for w in writers:
        #     if w != None:
        #         w.write(data)
        #         asyncio.create_task(w.drain())

    def pack(self):
        #TODO send name, number, and description
        number_bytes = struct.pack('<H', self.number)
        name_bytes = bytes(self.name, 'ascii')[:31].ljust(32, bytes(1))
        description_len_bytes = struct.pack('<H', len(self.description))
        description_bytes = bytes(self.description, 'ascii')
        return LurkType.ROOM + number_bytes + name_bytes + description_len_bytes + description_bytes

    def pack_as_connection(self):
        #TODO send name, number, and description
        number_bytes = struct.pack('<H', self.number)
        name_bytes = bytes(self.name, 'ascii')[:31].ljust(32, bytes(1))
        description_len_bytes = struct.pack('<H', len(self.description))
        description_bytes = bytes(self.description, 'ascii')
        return LurkType.CONNECTION + number_bytes + name_bytes + description_len_bytes + description_bytes
