'''
Let packetType
0 = SYN seq number
1 = ACK acknowlegement
2 = EOT end of transmission
data will carry 128 bytes at most per packet
'''
class Packet:
    def __init__(self,
                 packetType=None,
                 seqNum = None,
                 ackNum = None,
                 windowSize = None,
                 payload = None):
        self.packetType = packetType
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.windowSize = windowSize
        self.payload = payload
