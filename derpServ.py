import asyncio
import logging
import sys
import derp_game as dg
import derplib.net as dnet
from derplib.lurktype import LurkType
from derplib.character import Character
from derplib.errors import CharacterInUse, InvalidCharacter
from handlers import *

SERVER_ADDRESS = ('localhost', 10_000)

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
            character_name = await handle_CHARACTER(reader, writer, derp)
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
            pass
        elif data == LurkType.CHARACTER:
            await dnet.send_ERROR(writer, 0, 'Character already selected')
        else:
            await dnet.send_ERROR(writer, 0, 'Invalid Type sent')

    #TODO clean up connection, remove it from active list in game




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
        event_loop.close()