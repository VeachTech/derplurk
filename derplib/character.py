import socket
import asyncio
import struct
import logging
from enum import IntFlag
from .lurktype import LurkType

# CHARACTER
# Sent by both the client and the server. The server will send this message to show the client changes to their player's status, such as in health or gold. The server will also use this message to show other players or monsters in the room the player is in or elsewhere. The client should expect to receive character messages at any time, which may be updates to the player or others. If the player is in a room with another player, and the other player leaves, a CHARACTER message should be sent to indicate this. In many cases, the appropriate room for the outgoing player is the room they have gone to. If the player goes to an unknown room, the room number may be set to a room that the player will not encounter (does not have to be part of the map). This could be accompanied by a narrative message (for example, "Glorfindel vanishes into a puff of smoke"), but this is not required.
# The client will use this message to set the name, description, attack, defense, regen, and flags when the character is created. It can also be used to reprise an abandoned or deceased character.
# Byte	Meaning
# 0	Type, 10
# 1-32	Name of the player
# 33	Flags: Starting from the highest bit, Alive, Join Battle, Monster, Started, Ready. The lowest three are reserved for future use.
# 34-35	Attack
# 36-37	Defense
# 38-39	Regen
# 40-41	Health (signed)
# 42-43	Gold
# 44-45	Current room number (may be unknown to the player)
# 46-47	Description length
# 48+	Player description
# Meaning of flags:
# Flag	Meaning
# Alive	Character is alive (1 = alive, 0 = not alive)
# Join Battle	Character will automatically join battles in the room they are in (1 = join battles, 0 = do not join battles)
# Monster	Character is a monster (1 = monster, 0 = player)
# Started	Character has started the game (1 = started, 0 = not started
# Ready	Character is ready to start the game (1 = started, 0 = not started
# When a client uses CHARACTER to 

class Character_Flags(IntFlag):
    ALIVE = 0b10000000
    JOIN_BATTLE = 0b01000000
    MONSTER = 0b00100000
    STARTED = 0b00010000
    READY = 0b00001000

def describe_flags(f):
    s = ''
    if f & Character_Flags.ALIVE:
        s += '[ALIVE]'
    if f & Character_Flags.JOIN_BATTLE:
        s += '[JOIN_BATTLE]'
    if f & Character_Flags.MONSTER:
        s += '[MONSTER]'
    return s

class Stats():

    def __init__(self):
        self.attack = 0
        self.defense = 0
        self.regen = 0
        self.health = 0
        self.gold = 0

    def pack(self):
        stat_bytes = struct.pack('<HHHhH',
                                self.attack,
                                self.defense,
                                self.regen,
                                self.health,
                                self.gold)
        return stat_bytes

class Character():



    def __init__(self):
        self.name = ''
        self.flags = Character_Flags(value=0)
        self.stats = Stats()
        self.current_room = 0
        self.description = ''
        self.writer = None

    async def receive(self, reader):
        name_bytes = await reader.readexactly(32)
        self.name = name_bytes.decode('utf-8').rstrip('\x00')
        flag_buf = await reader.readexactly(1)
        self.flags = struct.unpack('<B', flag_buf)[0]
        stats_buf = await reader.readexactly(14)
        a,d,r,h,g, room, desc_length = struct.unpack('<HHHhHHH', stats_buf)
        self.stats.attack = a
        self.stats.defense = d
        self.stats.regen = r
        self.stats.health = h
        self.stats.gold = g
        self.stats.current_room = room
        desc_bytes = await reader.readexactly(desc_length)
        self.description = desc_bytes.decode('utf-8').rstrip('\x00')
    # def receive(self, soc):
    #     name_bytes = soc.recv(32, socket.MSG_WAITALL)
    #     self.name = name_bytes.decode('ascii').rstrip('\x00')
    #     logging.debug(f'Name: {self.name}, bytes: {name_bytes}')
    #     flag_buf = soc.recv(1, socket.MSG_WAITALL)
    #     self.flags = struct.unpack('<B', flag_buf)[0]
    #     logging.debug(f'Flags: {self.flags}, bytes: {flag_buf}')
    #     stats_buf = soc.recv(14, socket.MSG_WAITALL)
    #     logging.debug(f'Stats bytes: {stats_buf}')
    #     a,d,r,h,g, room, desc_length = struct.unpack('<HHHhHHH', stats_buf)
    #     self.stats.attack = a
    #     self.stats.defense = d
    #     self.stats.regen = r
    #     self.stats.health = h
    #     self.stats.gold = g
    #     self.current_room = room
    #     desc_bytes = soc.recv(desc_length, socket.MSG_WAITALL)
    #     self.description = desc_bytes.decode('ascii').rstrip('\x00')
    #     logging.debug(f'Description: {self.description}')
    #     logging.debug(f'Description bytes: {desc_bytes}')


    def pack(self):
        name_bytes = bytes(self.name, 'utf-8')[:31].ljust(32, bytes(1))
        # print(f'Name: {self.name}, bytes: {name_bytes}')
        flag_byte = struct.pack('<B', self.flags)
        # print(f'Flags: {self.flags}, byte: {flag_byte}')
        stat_bytes = self.stats.pack()
        room_bytes = struct.pack('<H', self.current_room)
        desc_length_bytes = struct.pack('<H', len(self.description))
        description_bytes = bytes(self.description, 'utf-8')
        packet = LurkType.CHARACTER + name_bytes + flag_byte + stat_bytes + room_bytes + desc_length_bytes + description_bytes
        return packet

    async def send(self, writer):
        writer.write(self.pack())
        await writer.drain()
