import asyncio
from derplib.character import Character
from derp_game import derp_game
import derplib.net as dnet
from derplib.errors import CharacterInUse, InvalidCharacter

async def handle_CHARACTER(reader, writer, game):
    c = Character()
    await c.receive(reader)
    try:
        c = game.initialize_character(c, writer)
    except CharacterInUse as err:
        await dnet.send_ERROR(writer, 2, f'Player "{err.name}" is already in use... Terminating')
        raise err
    except InvalidCharacter as err:
        await dnet.send_ERROR(writer, 4, f'{err.name}: {err.message}')
        raise err
    return c.name

async def handle_MESSAGE(reader, writer, name, game):
    pass

async def handle_CHANGE_ROOM():
    pass

async def handle_FIGHT():
    pass

async def handle_PVPFIGHT():
    pass

async def handle_LOOT():
    pass

async def handle_START():
    pass

async def handle_ROOM():
    pass

async def handle_LEAVE():
    pass

