import socket
import struct
import random
import sys

def main(port, fileName, p):

    def checksumCalc(message):
        add = 0
        for i in range(0, len(message) - len(message) % 2, 2):
            message = str(message)
            w = ord(message[i]) + (ord(message[i + 1]) << 8)
            add = ((add + w) & 0xffff) + ((add + w) >> 16)
        return ~add & 0xffff

    print("server running at port " + str(port) + " and writing to file " + fileName)

    expSeq = 0
    ReceiverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    host_address = '127.0.0.1'
    print(host_address)
    ReceiverSocket.bind((host_address, port))

    def unpacketize(message):
        seq_num = message[0:4]
        seq_num = struct.unpack('=L', seq_num)
        checksum = message[4:6]
        checksum = struct.unpack('=H', checksum)
        identifier = message[6:8]
        identifier = struct.unpack('=H', identifier)
        data = (message[8:])
        actual_message = data.decode('ISO-8859-1', 'ignore')
        return seq_num, checksum, identifier, actual_message

    def packetize(expSeq):
        seq_number = struct.pack('=I', expSeq)
        acknowledgment_sent = struct.pack('=H', 43690)
        ackPacket = seq_number + acknowledgment_sent
        return ackPacket

    def SSA(data, expSeq, address):
        with open(fileName, 'ab') as file:
            file.write(str.encode(data))
            ackPacket = packetize(expSeq)
            ReceiverSocket.sendto(ackPacket, address)

    while True:
        message, address = ReceiverSocket.recvfrom(2048)
        print("Received from: "+ str(address))
        seq_num, checksum, identifier, data = unpacketize(message)
        print('Sequence Number: ' +str(seq_num[0]))

        if(random.random()<p):
            print('Packet loss, sequence number = '+ str(seq_num[0]))
        else:
            if expSeq == seq_num[0]:
                if checksum[0] == checksumCalc(data):
                    print("\nPacket Received of size : " + str(len(data)))
                    SSA(data, expSeq, address)
                    expSeq += 1

if __name__ == '__main__':
    port = int(sys.argv[1])
    fileName = sys.argv[2]
    p = float(sys.argv[3])

    main(port, fileName, p)
