import socket
import logging
import struct

class Room():
    
    name = ''
    number = 0
    description = ''
    connections = [] # list of rooms this one is connected to

    def receive(self, soc):
        logging.debug('Enter receive_ROOM...')
        room_num_bytes = soc.recv(2, socket.MSG_WAITALL)
        self.number = struct.unpack('<H', room_num_bytes)[0]
        room_name_bytes = soc.recv(32, socket.MSG_WAITALL)
        self.name = room_name_bytes.decode('ascii').rstrip('\x00')
        description_length_bytes = soc.recv(2, socket.MSG_WAITALL)
        description_length = struct.unpack('<H', description_length_bytes)[0]
        description_bytes = soc.recv(description_length, socket.MSG_WAITALL)
        self.description = description_bytes.decode('ascii').rstrip('\x00')

        logging.debug(f'Room number: {self.number}, Bytes: {room_num_bytes}')
        logging.debug(f'Room name: {self.name}, Bytes: {room_name_bytes}')
        logging.debug(f'Room description length: {description_length}, Bytes: {description_length_bytes}')
        logging.info(f'Room name: {self.name}, Description: {self.description}')