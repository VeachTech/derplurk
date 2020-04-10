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

    # while character_name == '':
    #     # Initial receive, accept only character or send Error
    #     try:
    #         data = await reader.readexactly(1)
    #         if data == LurkType.CHARACTER:
    #             character_name = await handle_CHARACTER(reader, writer)
    #         else:
    #             await dnet.send_ERROR(writer, 5, 'Sent message before character message... Disconnecting')
    #             continue

    #     except InvalidCharacter:
    #         continue
    #     except asyncio.IncompleteReadError:
    #         writer.close()
    #         return
    #     except:
    #         writer.close()
    #         return
    
    #await dnet.send_ACCEPT(writer, LurkType.CHARACTER)

    # initial update for client
    #await derp.update_client_room(character_name)

    # Close connection after 5 errors in a row
    num_errors = 0

    # main loop for client
    try:
        while True:
            #get lurktype
            try:
                data = await reader.readexactly(1)
            except asyncio.IncompleteReadError:
                log.debug('IncompleteReadError, closing connection')
                break

            if data == LurkType.MESSAGE:
                await handle_MESSAGE(reader, writer, character_name)
            elif data == LurkType.CHANGE_ROOM:
                await handle_CHANGE_ROOM(reader, writer, character_name)
            elif data == LurkType.FIGHT:
                await handle_FIGHT(writer, character_name)
            elif data == LurkType.PVPFIGHT:
                await handle_PVPFIGHT(reader, writer, character_name)
            elif data == LurkType.LOOT:
                await handle_LOOT(reader, writer, character_name)
            elif data == LurkType.START:
                await handle_START(writer, character_name)
            elif data == LurkType.LEAVE:
                await dnet.send_ACCEPT(writer, LurkType.LEAVE)
                break   # break out of while loop and disconnect character from game
            elif data == LurkType.CHARACTER:
                if character_name != '':
                    await dnet.send_ERROR(writer, 0, 'Character already selected')
                else:
                    try:
                        character_name = await handle_CHARACTER(reader, writer)

                    except InvalidCharacter:
                        continue
                    except asyncio.IncompleteReadError:
                        writer.close()
                        return
                    except:
                        writer.close()
                        return
            else:
                await dnet.send_ERROR(writer, 0, 'Invalid Type sent')
                num_errors += 1
                if num_errors >= 5:
                    break
                else:
                    continue

            # if we have reached here, there was a successful message
            num_errors = 0
    
    finally:
        if character_name != '':
            derp.disconnect_character(character_name)
            log.debug(f'Character "{character_name}" disconnected, closing connection')
        writer.close()
        log.debug('Connection closed')
        

async def handle_CHARACTER(reader, writer):
    c = Character()
    await c.receive(reader)
    try:
        c = await derp.initialize_character(c, writer)
        log.debug(f'Successfully found character: {c.name}')
    except CharacterInUse as err:
        await dnet.send_ERROR(writer, 2, f'Player "{err.name}" is already in use... Terminating')
        raise err
    except InvalidCharacter as err:
        await dnet.send_ERROR(writer, 4, f'{err.name}: {err.message}')
        raise err
    await c.send(writer)
    return c.name

#TODO Verify handle_MESSAGE
async def handle_MESSAGE(reader, writer, name):
    if name == '':
        await dnet.send_ERROR(writer, 5, "Character not selected")
        return
    recipient, sender, message = await dnet.receive_MESSAGE(reader)
    # ignore sender name, we already know who actually sent it
    code = await derp.send_message(recipient, name, message)
    if code == "DEAD":
        await dnet.send_ERROR(writer, 0, "Can't perform action, you are DEAD")
    elif code == "Success":
        await dnet.send_ACCEPT(writer, LurkType.MESSAGE)
    else:
        await dnet.send_ERROR(writer, 6, 'Cannot send message')

async def handle_CHANGE_ROOM(reader, writer, name):
    if name == '':
        await dnet.send_ERROR(writer, 5, "Character not selected")
        return
    room_number = await dnet.receive_CHANGE_ROOM(reader)
    result = await derp.change_room(name, room_number)
    if result == "DEAD":
        await dnet.send_ERROR(writer, 0, "Can't perform action, you are DEAD")
    elif result == "Success":
        await dnet.send_ACCEPT(writer, LurkType.CHANGE_ROOM)
    else:
        await dnet.send_ERROR(writer, 1, f"Can't change to room: {room_number}")

async def handle_FIGHT(writer, name):
    if name == '':
        await dnet.send_ERROR(writer, 5, "Character not selected")
        return
    result = await derp.fight(name)
    if result == "DEAD":
        await dnet.send_ERROR(writer, 0, "Can't perform action, you are DEAD")
    elif result == "nofight":
        await dnet.send_ERROR(writer, 7, "Can't perform action, no monsters")
    else:
        await dnet.send_ACCEPT(writer, LurkType.FIGHT)

async def handle_PVPFIGHT(reader, writer, name):
    if name == '':
        await dnet.send_ERROR(writer, 5, "Character not selected")
        return
    name = await dnet.receive_PVPFIGHT(reader)
    await dnet.send_ERROR(writer, 8, "No PVP in this server")

async def handle_LOOT(reader, writer, name):
    if name == '':
        await dnet.send_ERROR(writer, 5, "Character not selected")
        return
    target = await dnet.receive_LOOT(reader)
    code = await derp.loot(name, target)
    if code == "No Target":
        await dnet.send_ERROR(writer, 6, "No target")
    elif code == "Target Alive":
        await dnet.send_ERROR(writer, 0, "Target is alive")
    else:
        await dnet.send_ACCEPT(writer, LurkType.LOOT)

async def handle_START(writer, name):
    if name == '':
        await dnet.send_ERROR(writer, 5, "Character not selected")
        return
    await derp.start_character(name)
    await dnet.send_ACCEPT(writer, LurkType.START)

async def handle_LEAVE():
    pass


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: client.py server port")
        exit()
    #server.connect((sys.argv[1], int(sys.argv[2])))
    #factory = asyncio.start_server(client_connection, *SERVER_ADDRESS)
    factory = asyncio.start_server(client_connection, sys.argv[1], int(sys.argv[2]), limit=2**17)
    server = event_loop.run_until_complete(factory)
    log.debug('starting up on {} port {}'.format(sys.argv[1], int(sys.argv[2])))

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