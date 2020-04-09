import asyncio
import socket
import struct
import logging
from .room import Room
from .character import Character
from .game import Game
from .lurktype import LurkType

# TODO: make sure struct.unpack return a value and not a tuple of length 1: (a,)

# MESSAGE
# Sent by the client to message other players. Can also be used by the server to send "presentable" information to the client (information that can be displayed to the user with no further processing). Clients should expect to receive this type of message at any time, and servers should expect to relay messages for clients at any time. If using this to send game information, the server can use the name of an NPC or some such, and should expect that the client will just display the message to the user and not attempt to parse it.
# Byte	Meaning
# 0	Type, 1
# 1-2	Message Length, 16 bits unsigned.
# 3-34	Recipient Name, 32 bytes total.
# 35-66	Sender Name, 32 bytes total.
# 67+	Message. Length was specified earlier.
def OLD_receive_MESSAGE(soc):
    logging.debug('Enter receive_MESSAGE...')
    length = soc.recv(2, socket.MSG_WAITALL)
    length = struct.unpack('<H', length)[0]
    recipient = soc.recv(32, socket.MSG_WAITALL).decode('ascii').rstrip('\x00')
    sender = soc.recv(32, socket.MSG_WAITALL).decode('ascii').rstrip('\x00')
    message = soc.recv(length, socket.MSG_WAITALL).decode('ascii').rstrip('\x00')
    logging.debug(f"Recipient: {recipient}")
    logging.debug(f"Sender: {sender}")
    logging.debug(f"Message length: {length}")
    logging.debug(f"Message: {message}")
    return recipient, sender, message

async def receive_MESSAGE(reader):
    length = await reader.readexactly(2)
    length = struct.unpack('<H', length)[0]
    recipient = await reader.readexactly(32)
    recipient = recipient.decode('ascii').rstrip('\x00')
    sender = await reader.readexactly(32)
    sender = sender.decode('ascii').rstrip('\x00')
    message = await reader.readexactly(length)
    message = message.decode('ascii').rstrip('\x00')
    logging.debug(f"Recipient: {recipient}")
    logging.debug(f"Sender: {sender}")
    logging.debug(f"Message length: {length}")
    logging.debug(f"Message: {message}")
    return recipient, sender, message

def pack_MESSAGE(recipient, sender, message):
    length_bytes = struct.pack('<H', len(message))
    recipient_bytes = bytes(recipient, 'ascii')[:31].ljust(32, bytes(1))
    sender_bytes = bytes(sender, 'ascii')[:31].ljust(32, bytes(1))
    message_bytes = bytes(message, 'ascii')
    packet = LurkType.MESSAGE + length_bytes + recipient_bytes + sender_bytes + message_bytes
    return packet

async def send_MESSAGE(writer, recipient, sender, message):
    length_bytes = struct.pack('<H', len(message))
    recipient_bytes = bytes(recipient, 'ascii')[:31].ljust(32, bytes(1))
    sender_bytes = bytes(sender, 'ascii')[:31].ljust(32, bytes(1))
    message_bytes = bytes(message, 'ascii')
    packet = LurkType.MESSAGE + length_bytes + recipient_bytes + sender_bytes + message_bytes
    writer.write(packet)
    await writer.drain()

def OLD_send_MESSAGE(soc, recipient, sender, message):
    logging.debug('Enter send_MESSAGE...')
    length_bytes = struct.pack('<H', len(message))
    recipient_bytes = bytes(recipient, 'ascii')[:31].ljust(32, bytes(1))
    sender_bytes = bytes(sender, 'ascii')[:31].ljust(32, bytes(1))
    message_bytes = bytes(message, 'ascii')
    packet = LurkType.MESSAGE + length_bytes + recipient_bytes + sender_bytes + message_bytes
    
    logging.debug(f'Send Message: {LurkType.MESSAGE}')
    logging.debug(f'length: {len(message)}, bytes: {length_bytes}')
    logging.debug(f'recipient: {recipient}, bytes: {recipient_bytes}')
    logging.debug(f'sender: {sender}, bytes: {sender_bytes}')
    logging.debug(f'message: {message}')
    logging.debug(f'bytes: {message_bytes}')
    logging.info(f'MESSAGE packet bytes: {packet}')

    sent = soc.sendall(packet)
    logging.debug(f'total bytes sent: {sent}')

async def serv_send_MESSAGE(writer, recipient, sender, message):
    logging.debug(f'{sender} sending to {recipient}: {message}')
    length_bytes = struct.pack('<H', len(message))
    recipient_bytes = bytes(recipient, 'ascii')[:31].ljust(32, bytes(1))
    sender_bytes = bytes(sender, 'ascii')[:31].ljust(32, bytes(1))
    message_bytes = bytes(message, 'ascii')
    packet = LurkType.MESSAGE + length_bytes + recipient_bytes + sender_bytes + message_bytes
    writer.write(packet)
    await writer.drain()



# CHANGEROOM
# Sent by the client only, to change rooms. If the server changes the room a client is in, it should send an updated room, character, and connection message(s) to explain the new location. If not, for example because the client is not ready to start or specified an inappropriate choice, and error should be sent.
# Byte	Meaning
# 0	Type, 2
# 1-2	Number of the room to change to. The server will send an error if an inappropriate choice is made.

async def receive_CHANGE_ROOM(reader):
    number_bytes = await reader.readexactly(2)
    number = struct.unpack('<H', number_bytes)[0]
    return number

def send_CHANGE_ROOM(soc, room):
    logging.debug('Enter send_CHANGE_ROOM...')
    room_bytes = struct.pack('<H', room)
    packet = LurkType.CHANGE_ROOM + room_bytes
    
    logging.debug(f'Send Change Room: {LurkType.CHANGE_ROOM}')
    logging.debug(f'Room number: {room}, bytes: {room_bytes}')
    logging.info(f'CHANGE_ROOM packet bytes: {packet}')

    sent = soc.sendall(packet)
    logging.debug(f'total bytes sent: {sent}')

# FIGHT
# Initiate a fight against monsters. This will start a fight in the current room against the monsters which are presently in the room. Players with the join battle flag set, who are in the same room, will automatically join in the fight. The server will allocate damage and rewards after the battle, and inform clients appropriately. Clients should expect a slew of messages after starting a fight, especially in a crowded room. This message is sent by the client. If a fight should ensue in the room the player is in, the server should notify the client, but not by use of this message. Instead, the players not initiating the fight should receive an updated CHARACTER message for each entity in the room. If the server wishes to send additional narrative text, this can be sent as a MESSAGE. Note that this is not the only way a fight against monsters can be initiated. The server can initiate a fight at any time.
# Byte	Meaning
# 0	Type, 3

def send_FIGHT(soc):
    logging.debug('Enter send_FIGHT...')
    logging.debug(f'Send Fight: {LurkType.FIGHT}')
    logging.info(f'FIGHT packet bytes: {LurkType.FIGHT}')
    
    sent = soc.sendall(LurkType.FIGHT)
    logging.debug(f'total bytes sent: {sent}')

# PVPFIGHT
# Initiate a fight against another player. The server will determine the results of the fight, and allocate damage and rewards appropriately. The server may include players with join battle in the fight, on either side. Monsters may or may not be involved in the fight as well. This message is sent by the client. If the server does not support PVP, it should send error 8 to the client.
# Byte	Meaning
# 0	Type, 4
# 1-32	Name of target player

async def receive_PVPFIGHT(reader):
    data = reader.readexactly(32)
    name = data.decode('ascii').rstrip('\x00')
    return name

def send_PVPFIGHT(soc, target):
    logging.debug('Enter send_PVPFIGHT...')
    target_bytes = bytes(target, 'ascii')[:31].ljust(32, bytes(1))
    packet = LurkType.PVPFIGHT + target_bytes

    logging.debug(f'Send PVPFIGHT: {LurkType.PVPFIGHT}')
    logging.debug(f'Target: {target}, bytes: {target_bytes}')
    logging.info(f'PVPFIGHT packet bytes: {packet}')

    sent = soc.sendall(packet)
    logging.debug(f'total bytes sent: {sent}')

# LOOT
# Loot gold from a dead player or monster. The server may automatically gift gold from dead monsters to the players who have killed them, or wait for a LOOT message. The server is responsible for communicating the results of the LOOT to the player, by sending an updated CHARACTER message. This message is sent by the client.
# Byte	Meaning
# 0	Type, 5
# 1-32	Name of target player

async def receive_LOOT(reader):
    data = reader.readexactly(32)
    name = data.decode('ascii').rstrip('\x00')
    return name

def send_LOOT(soc, target):
    logging.debug('Enter send_LOOT...')
    target_bytes = bytes(target, 'ascii')[:31].ljust(32, bytes(1))
    packet = LurkType.LOOT + target_bytes
    
    logging.debug(f'Send LOOT: {LurkType.LOOT}')
    logging.debug(f'Target: {target}, bytes: {target_bytes}')
    logging.info(f'LOOT packet bytes: {packet}')

    sent = soc.sendall(packet)
    logging.debug(f'total bytes sent: {sent}')

# START
# Start playing the game. A client will send a CHARACTER message to the server to explain character stats, which the server may either accept or deny (by use of an ERROR message). If the stats are accepted, the server will not enter the player into the game world until it has received START. This is sent by the client. Generally, the server will reply with a ROOM, a CHARACTER message showing the updated room, and a CHARACTER message for each player in the initial room of the game.
# Byte	Meaning
# 0	Type, 6

def send_START(soc):
    logging.debug('Enter send_START...')
    logging.debug(f'Send START: {LurkType.START}')
    logging.info(f'START packet bytes: {LurkType.START}')

    sent = soc.sendall(LurkType.START)
    logging.debug(f'total bytes sent: {sent}')

# ERROR
# Notify the client of an error. This is used to indicate stat violations, inappropriate room connections, attempts to loot nonexistent or living players, attempts to attack players or monsters in different rooms, etc.
# Byte	Meaning
# 0	Type, 7
# 1	Error code. List is given below.
# 2-3	Error message length.
# 4+	Actual error message, of the specified length.
# Error codes:
# Code	Meaning
# 0	Other (not covered by any below error code)
# 1	Bad room. Attempt to change to an inappropriate room
# 2	Player Exists. Attempt to create a player that already exists.
# 3	Bad Monster. Attempt to loot a nonexistent or not present monster.
# 4	Stat error. Caused by setting inappropriate player stats.
# 5	Not Ready. Caused by attempting an action too early, for example changing rooms before sending START or CHARACTER.
# 6	No target. Sent in response to attempts to loot nonexistent players, fight players in different rooms, etc.
# 7	No fight. Sent if the requested fight cannot happen for other reasons (i.e. no live monsters in room)
# 8	No player vs. player combat on the server. Servers do not have to support player-vs-player combat.

def receive_ERROR(soc):
    logging.debug('Enter Receive_ERROR...')
    error_code = soc.recv(1, socket.MSG_WAITALL)
    logging.debug(f'Received error code {error_code}')
    msg_length_bytes = soc.recv(2, socket.MSG_WAITALL)
    msg_length = struct.unpack('<H', msg_length_bytes)[0]
    message = soc.recv(msg_length, socket.MSG_WAITALL).decode('ascii').rstrip('\x00')

    logging.debug(f'Message Length bytes: {msg_length_bytes}, Length: {msg_length}')
    logging.warning(f'Received _{error_code}_ error code: {message}')
    return error_code, message

async def send_ERROR(writer, code, msg):
    code_bytes = struct.pack('<B', code)
    msg_length_bytes = struct.pack('<H', len(msg))
    msg_bytes = bytes(msg, 'ascii')
    packet = LurkType.ERROR + code_bytes + msg_length_bytes + msg_bytes
    writer.write(packet)
    await writer.drain()

# ACCEPT
# Sent by the server to acknowledge a non-error-causing action which has no other direct result. This is not needed for actions which cause other results, such as changing rooms or beginning a fight. It should be sent in response to clients sending messages, setting character stats, etc.
# Byte	Meaning
# 0	Type, 8
# 1	Type of action accepted.

def receive_ACCEPT(soc):
    action = soc.recv(1, socket.MSG_WAITALL)
    return action

async def send_ACCEPT(writer, accept_type):
    writer.write(LurkType.ACCEPT + accept_type)
    await writer.drain()

# ROOM
# Sent by the server to describe the room that the player is in. This should be an expected response to CHANGEROOM or START. Can be re-sent at any time, for example if the player is teleported or falls through a floor. Outgoing connections will be specified with a series of CONNECTION messages. Monsters and players in the room should be listed using a series of CHARACTER messages.
# Byte	Meaning
# 0	Type, 9
# 1-2	Room number. This is the same room number used for CHANGEROOM
# 3-34	Room name, 32 bytes in length
# 35-36	Room description length
# 37+	Room description. This can be shown to the player.

# def receive_ROOM(soc):
#     room = Room()
#     room.receive(soc)

#     return room


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
# When a client uses CHARACTER to describe a new player, the server may (should) ignore the client's initial specification for health, gold, and room. The monster flag is used when describing monsters found in the game rather than other human players.

## DO NOT USE, USE CHARACTER CLASS INSTEAD
# def receive_CHARACTER(soc):
#     character = Character()
#     character.receive(soc)
#     return character

# def send_CHARACTER(soc, char):
#     char.send(soc)

# GAME
# Used by the server to describe the game. The initial points is a combination of health, defense, and regen, and cannot be exceeded by the client when defining a new character. The stat limit is a hard limit for the combination for any player on the server regardless of experience. If unused, it should be set to 65535, the limit of the unsigned 16-bit integer. This message will be sent upon connecting to the server, and not re-sent.
# Byte	Meaning
# 0	Type, 11
# 1-2	Initial Points
# 3-4	Stat limit
# 5-6	Description Length
# 7+	Game description

def receive_GAME(soc):
    g = Game()
    g.receive(soc)
    return g

async def send_GAME(writer, game):
    writer.write(game.pack())
    await writer.drain()



# LEAVE
# Used by the client to leave the game. This is a graceful way to disconnect. The server never terminates, so it doesn't send LEAVE.
# Byte	Meaning
# 0	Type, 12
def send_LEAVE(soc):
    soc.sendall(LurkType.LEAVE)


# CONNECTION
# Used by the server to describe rooms connected to the room the player is in. The client should expect a series of these when changing rooms, but they may be sent at any time. For example, after a fight, a secret staircase may extend out of the ceiling enabling another connection. Note that the room description may be an abbreviated version of the description sent when a room is actually entered. The server may also provide a different room description depending on which room the player is in. So a description on the connection could read "A strange whirr is heard through the solid oak door", and the description attached to the message once the player has entered could read "Servers line the walls, softly lighting the room in a cacophony of red, green, blue, and yellow flashes".
# Byte	Meaning
# 0	Type, 13
# 1-2	Room number. This is the same room number used for CHANGEROOM
# 3-34	Room name, 32 bytes in length
# 35-36	Room description length
# 37+	Room description. This can be shown to the player.
# def receive_CONNECTION(soc):
#     connection = Room()
#     connection.receive(soc)
#     return connection


# VERSION
# Sent by the server upon initial connection along with GAME. If no VERSION is received, the server can be assumed to support only LURK 2.0 or 2.1.
# Byte	Meaning
# 0	Type, 14
# 1	LURK major revision, as an 8-bit unsigned int
# 2	LURK minor revision, as an 8-bit unsigned int
# 3-4	Size of the list of extensions, in bytes.
# 5+	List of extensions.
# The list of extensions is formatted like this:
# Byte	Meaning
# 0-1	Length of the first extension, as an unsigned 16-bit integer.
# 2+	First extension

def receive_VERSION(soc):
    buf = soc.recv(4, socket.MSG_WAITALL)
    major, minor, size = struct.unpack('<BBH', buf)
    #Throw away the list of extensions because we do not handle them
    if size:
        _ = soc.recv(size, socket.MSG_WAITALL)
    return major, minor, size

async def send_VERSION(writer):
    version = struct.pack('<BB', 2, 2)
    # no extension supported
    extensions = struct.pack('<H', 0)
    writer.write(LurkType.VERSION + version + extensions)
    await writer.drain()
