import socket
import asyncio
import logging
import struct
from .lurktype import LurkType
import derp_game
import derplib.net as dnet

class Room():
    
    game = None
    name = ''
    number = 0
    description = ''
    connections = [] # list of rooms this one is connected to
    characters = []

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
        char.writer.write(room_data + existing_character_data)
        #DONE update whole room of new character
        asyncio.create_task(char.writer.drain())
        asyncio.create_task(self.update_one_character(name))
        #DONE add character name to list
        self.characters.append(name)

    #TODO not informing others of left player, Uh, might be my client
    async def leave_room(self, name, number):
        if number in self.connections:
            #TODO: Apply characters regen
            #DONE change room number of character
            char = self.game.characters[name]
            char.current_room = number
            #DONE remove character from list
            self.characters.remove(name)
            #DONE call enter room of appropiate room
            asyncio.create_task(self.game.rooms[number].enter_room(name))
            #DONE update other characters of character leaving
            asyncio.create_task(self.update_one_character(name))
            return "Success"
        else:
            return "Invalid Room"

    async def fight(self, name):
        #TODO get players with join battle + named character
        #TODO fight clalculations
        #TODO update all characters of new stats
        pass

    async def send_message(self, recipient, sender, message):
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

    async def full_update_for_player_pack(self):
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
