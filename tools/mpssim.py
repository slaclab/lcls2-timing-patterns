import socket
import struct
import logging

class MpsSim(object):
    def __init__(self, host, port):
        #  Connect to TCP port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        info = socket.getaddrinfo(host,port,socket.AF_INET,socket.SOCK_STREAM)
        logging.info('MPS info {}'.format(info))
        self.s.connect(info[0][4])

    def update(self, d):
        for key,v in d.items():
            self.setstate(key,v)

    def setstate(self, destn, pc):
        #  Build message and send
        n = self.s.sendall(struct.pack('BBH',destn,pc,0))
        v = self.s.recv(4)
