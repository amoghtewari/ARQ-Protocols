import socket
import threading
import time
import struct
import sys

lock = threading.Lock()
threadx = threading.Thread

TIMEOUT_TIMER = 3
ackN = 0
packet_list = []
window = {}
totalPackets=0
packets_sent = 0
packet_ack = 0

def packetize(data, sn):

    def checksumCalc(message):
        add = 0
        for i in range(0, len(message) - len(message) % 2, 2):
            message = str(message)
            w = ord(message[i]) + (ord(message[i + 1]) << 8)
            add = ((add + w) & 0xffff) + ((add + w) >> 16)
        return ~add & 0xffff

    sequenceNumber = struct.pack('=L', sn)
    mat = str(data,'UTF-8')
    checksumVal = struct.pack('=H', checksumCalc(mat))
    content=mat.encode('UTF-8')
    identifier = struct.pack('=H', 43690)
    packet=sequenceNumber+checksumVal+identifier+content
    return packet

def unpacketize(ACKTHREAD):
    snr = int(struct.unpack('=I', ACKTHREAD[0:4])[0])
    ac = int(struct.unpack('=H', ACKTHREAD[4:6])[0])
    return ac, snr

def prepare_data(FILE, MSS):
    FILE.seek(0)
    data = FILE.read(MSS)
    sequence_number = 0
    while data:
        packet = packetize(data, sequence_number)
        packet_list.append(packet)
        data = FILE.read(MSS)
        sequence_number += 1
    return len(packet_list)

class GBNTHREAD(threadx):
    def __init__(self, host, port, file, N, MSS, socket_client):
        threading.Thread.__init__(self)
        self.host = host
        self.port = port
        self.file = file
        self.N    = N
        self.MSS  = MSS
        self.socket_client = socket_client
        self.start()

    def run(self):
        global window
        global lock
        global ackN
        global packet_list
        global packet_ack
        global totalPackets

        def timeOut(self, current_number, server):
            if window.get(ackN):
                try:
                    if (time.time() - ((window[ackN])[1])) >= TIMEOUT_TIMER:
                        for packet in range(ackN, current_number):
                            data = window[packet][0]
                            window[packet] = (data, time.time())
                            self.socket_client.sendto(data, server)
                            print('Timeout, sequence number = ' + str(packet))
                except KeyError:
                    print("Resetting, Ack not received!")

        current_number = 0
        server = (self.host, self. port)

        while packet_ack < totalPackets:
            while current_number - ackN >= self.N:
                lock.acquire()
                if ackN < totalPackets and ackN < current_number:
                    timeOut(self, current_number, server)
                lock.release()

            lock.acquire()
            if totalPackets <= self.N and ackN < current_number:
                timeOut(self, current_number, server)
            lock.release()

            lock.acquire()
            if ackN < totalPackets and ackN < current_number:
                timeOut(self, current_number, server)
            lock.release()

            lock.acquire()
            if current_number < totalPackets:
                window[current_number] = (packet_list[current_number], time.time())
                self.socket_client.sendto(packet_list[current_number], server)
                print("Sending Packet!")
                current_number = current_number + 1
            lock.release()

class ACKTHREAD(threadx):
    def __init__(self, socket_client):
        threading.Thread.__init__(self)
        self.socket_client = socket_client
        self.start()
        self.totalPackets = totalPackets

    def run(self):
        global window
        global lock
        global ackN
        global packet_list
        global packet_ack
        global totalPackets

        while packet_ack < totalPackets:
            ACKTHREAD, address = self.socket_client.recvfrom(2048)
            ac, snr = unpacketize(ACKTHREAD)
            packet_ack  = packet_ack + 1
            ackN = ackN+1
            if ac == 43690:
                lock.acquire()
                del window[snr]
                lock.release()

def main(host, port, file, N, mss):

    Client_IP = '127.0.0.1'
    Client_Port = 4443
    socket_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_client.bind((Client_IP, Client_Port))

    start = time.time()
    FILE = open(file, 'rb')

    global totalPackets
    totalPackets = prepare_data(FILE, mss)

    ACKs = ACKTHREAD(socket_client)
    sendThreads = GBNTHREAD(host, port, file, N, mss, socket_client)
    sendThreads.join()
    ACKs.join()

    end = time.time()
    socket_client.close()
    FILE.close()

    print('Maximum Segment Size:\t'+str(mss))
    print('Window Size:\t' + str(N))
    print('End Time\t'+str(end))
    print('Total Time\t'+str(end-start))

if __name__ == '__main__':
    host = sys.argv[1]
    port = int(sys.argv[2])
    file = sys.argv[3]
    N = int(sys.argv[4])
    mss = int(sys.argv[5])

    main(host, port, file, N, mss)
