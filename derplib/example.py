import socket
import struct

# USER (both ways)
# 	type (1 byte): 1
# 	name (32 bytes): The actual name with at least one null terminator

def receive_USER(soc):
    buf = soc.recv(32)
    name = buf.decode('ascii').split('\0')[0]
    return name

def send_USER(soc, name):
    buf = bytearray(name, 'ascii')
    buf = buf[:31]
    buf = buf.ljust(32, bytes(1))
    soc.sendall(b'\x01' + buf)

# TEXT (send from both client and server)
# 	type (1 byte): 2
# 	sender (32 bytes): The sender of the message
# 	length (2 bytes):  The length of the message, little endian
# 	text (length bytes):  The actual message, does not need a null terminator

def receive_TEXT(soc):
    buf = soc.recv(32, socket.MSG_WAITALL) 
    sender = list(struct.unpack('='+'c'*32, buf)) 
    sender = b''.join(sender).decode('ascii').split('\0')[0]
    buf = soc.recv(2, socket.MSG_WAITALL) 
    message_length = struct.unpack('<H', buf) 
    buf = soc.recv(message_length[0], socket.MSG_WAITALL) 
    message = buf.decode('ascii') 
    return (message_length, sender, message)

def send_TEXT(soc, sender, message):
    sender = bytearray(sender, 'ascii').ljust(32, b'\0')
    message = bytes(message, 'ascii')
    buf = b'\x02' + sender + struct.pack('<H', len(message)) + message
    soc.sendall(buf)
    return len(buf)

# LEFT (server to client)
# 	type (1 byte): 3
# 	name (32 bytes): The actual name with at least one null terminator
def receive_LEFT(soc):
    buf = soc.recv(32, socket.MSG_WAITALL)
    name = b''.join(buf).decode('ascii').split('\0')[0]
    return name


# NAME TAKEN (server to client)
# 	type (1 byte): 4
def receive_NAME_TAKEN():
    """Don't call, nothing to do"""
    pass

# PM (both ways) (This is the same as the LURK MESSAGE, except for the type)
# 	type (1 byte):  5
# 	length (2 bytes):  The length of the message, little endian
# 	recipient (32 bytes): The name of the recipient
# 	sender (32 bytes): The name of the sender
# 	message (length bytes):  The actual message

def receive_PM(soc):
    buf = soc.recv(2, socket.MSG_WAITALL) # Length 2 bytes, Recipient name: 4 bytes, Sender name: 4 bytes
    message_length = struct.unpack('<H', buf) # decode to integer
    buf = soc.recv(32, socket.MSG_WAITALL) # recieve 32 bytes for name
    recipient = list(struct.unpack('<'+'c'*32, buf)) # create a list of 32 bytes
    recipient = b''.join(recipient).decode('ascii').split('\0')[0] 
    buf = soc.recv(32, socket.MSG_WAITALL) # same for second name
    sender = list(struct.unpack('<'+'c'*32, buf)) # same
    sender = b''.join(sender).decode('ascii').split('\0')[0] # same
    buf = soc.recv(message_length[0], socket.MSG_WAITALL) # recieve message_length bytes for message
    message = buf.decode('ascii') # simply decode into a string
    return (message_length, recipient, sender, message)

def send_PM(soc, recipient, sender, message):
    recipient = bytearray(recipient, 'ascii').ljust(32, b'\0')
    sender = bytearray(sender, 'ascii').ljust(32, b'\0')
    message = bytes(message, 'ascii')
    buf = struct.pack('<BH', 5, len(message)) + recipient + sender + message
    soc.sendall(buf)
    return len(buf)
