import socket
import struct
from .lurktype import LurkType

class Game():
    initial_points = 0
    stat_limit = 65535
    description = ''

    def receive(self, soc):
        buf = soc.recv(6, socket.MSG_WAITALL)
        points, limit, length = struct.unpack('<HHH', buf)
        self.initial_points = points
        self.stat_limit = limit
        desc_bytes = soc.recv(length, socket.MSG_WAITALL)
        self.description = desc_bytes.decode('ascii')

    def pack(self):
        points_bytes = struct.pack('<H', self.initial_points)
        limit_bytes = struct.pack('<H', self.stat_limit)
        desc_length = struct.pack('<H', len(self.description))
        desc_bytes = bytes(self.description, 'ascii')
        return LurkType.GAME + points_bytes + limit_bytes + desc_length + desc_bytes
    
    def send(self, soc):
        soc.sendall(self.pack())
