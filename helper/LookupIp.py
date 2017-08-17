__author__ = 'alessio.rocchi'
from struct import *
from socket import *


def lookup(ip):
    f = unpack('!I', inet_pton(AF_INET, ip))[0]
    private = (
        [2130706432, 4278190080],
        [3232235520, 4294901760],
        [2886729728, 4293918720],
        [167772160, 4278190080],
    )
    for net in private:
        if f & net[1] == net[0]:
            return True
    return False
