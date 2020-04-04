import asyncio
import logging
import sys
import derp_game as dg
import derplib.net as dnet
from derplib.lurktype import LurkType
from derplib.character import Character
from derplib.errors import CharacterInUse, InvalidCharacter

SERVER_ADDRESS = ('0.0.0.0', 10_000)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s: %(message)s',
    stream=sys.stderr,
)

log = logging.getLogger('main')
event_loop = asyncio.get_event_loop()
derp = dg.derp_game()

async def client_connection(reader, writer):
    address = writer.get_extra_info('peername')
    log = logging.getLogger('echo_{}_{}'.format(*address))
    log.debug('connection accepted')

    character_name = ''

    # send version info to client
    await dnet.send_VERSION(writer)
    await dnet.send_GAME(writer, derp.game)

    # Initial receive, accept only character or send Error
    try:
        data = await reader.readexactly(1)
        if data == LurkType.CHARACTER:
            character_name = await handle_CHARACTER(reader, writer)
        else:
            await dnet.send_ERROR(writer, 5, 'Sent message before character message... Disconnecting')
            writer.close()
            return

    except asyncio.IncompleteReadError:
        #maybe log?
        return
    except:
        #character error, close socket and return
        writer.close()
        return
    
    await dnet.send_ACCEPT(writer, LurkType.CHARACTER)

    # main loop for client
    while True:
        #get lurktype
        try:
            data = await reader.readexactly(1)
        except asyncio.IncompleteReadError:
            break

        if data == LurkType.MESSAGE:
            handle_MESSAGE(reader, writer, character_name, derp)
        elif data == LurkType.CHANGE_ROOM:
            pass
        elif data == LurkType.FIGHT:
            pass
        elif data == LurkType.PVPFIGHT:
            pass
        elif data == LurkType.LOOT:
            pass
        elif data == LurkType.START:
            pass
        elif data == LurkType.ROOM:
            pass
        elif data == LurkType.LEAVE:
            await dnet.send_ACCEPT(writer, LurkType.LEAVE)
            break   # break out of while loop and disconnect character from game
        elif data == LurkType.CHARACTER:
            await dnet.send_ERROR(writer, 0, 'Character already selected')
        else:
            await dnet.send_ERROR(writer, 0, 'Invalid Type sent')

    #TODO clean up connection, remove it from active list in game, VERIFY
    derp.disconnect_character(character_name)
    #Does this auto cleanup sockets by just ending?


async def handle_CHARACTER(reader, writer):
    c = Character()
    await c.receive(reader)
    try:
        c = derp.initialize_character(c, writer)
    except CharacterInUse as err:
        await dnet.send_ERROR(writer, 2, f'Player "{err.name}" is already in use... Terminating')
        raise err
    except InvalidCharacter as err:
        await dnet.send_ERROR(writer, 4, f'{err.name}: {err.message}')
        raise err
    return c.name

async def handle_MESSAGE(reader, writer, name):
    recipient, sender, message = await dnet.receive_MESSAGE(reader)
    recipient_writer = derp.get_character_writer(recipient)
    if recipient_writer == None:
        await dnet.send_ERROR(writer, 6, 'Recipient does not exist or is not connected')
    else:
        await dnet.send_MESSAGE(recipient_writer, recipient, sender, message)
        await dnet.send_ACCEPT(LurkType.MESSAGE)

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


if __name__ == '__main__':
    factory = asyncio.start_server(client_connection, *SERVER_ADDRESS)
    server = event_loop.run_until_complete(factory)
    log.debug('starting up on {} port {}'.format(*SERVER_ADDRESS))

    try:
        event_loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        log.debug('closing server')
        server.close()
        event_loop.run_until_complete(server.wait_closed())
        log.debug('closing event loop')
        event_loop.close()import asyncio
