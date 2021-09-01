#!/usr/bin/python

from socket import *

import Packet
import pickle
import configparser
import time

#setup ip
#Globals
config = configparser.ConfigParser()
config.read('netSim.config')
netSimIP = config.get('default', 'netSimIp')
portNetSim = int(config.get('default', 'portNetSim'))
portCliServ = int(config.get('default', 'portCliServ'))
windowSize = int(config.get('default', 'window'))
packetSize = int(config.get('default', 'packetSize'))

expectedSyn = int(config.get('starting', 'syn')) #
currentAck = int(config.get('starting', 'ack'))

sendoutdelay = float(config.get("default", "sendOutDelay"))

filePath = config.get('filepath', 'dest')

print("printing config")
print("netSimIp =", netSimIP)
print("portNetSim =", portNetSim)
print("portCliServ =", portCliServ)
print("windowSize =", windowSize)
print("packetSize =", packetSize)
print("expectedSyn =", expectedSyn)
print("currentAck =", currentAck)
print("filePath =", filePath)

def sendEOT(socket):
    eotPack = Packet.Packet(2, 0, 0, 0, 0)
    socket.sendto(pickle.dumps(eotPack), (netSimIP, portNetSim))

def receiveCheck(receiveQueue, currentPacket, totalPackets):
    isDuplicate = checkDuplicate(receiveQueue)
    alreadyAcked = checkAlreadyAcked(receiveQueue, currentPacket)

    if (len(receiveQueue) + currentPacket == totalPackets): # last packets
        return 0
    elif (len(receiveQueue) == windowSize): #full window, possible correct data
        # check if it has already been acked
        if (alreadyAcked): # already acked, send packets equal packets received with duplicate ack of what to request
            return 1 # data already acked by receiver, sender probably lost acks
        else: # not acked and seqNum in order, to proceed
            return 2 # write to file and send correct acks
    elif (len(receiveQueue) == 0): # empty queue, do nothing and wait for sender timeout
        return 3
    elif (receiveQueue != windowSize): # incomplete window, send duplicate acks containing current ack number eg 4 4 4 4
        return 4


def checkAlreadyAcked(receiveQueue, currentPacket):
    alreadyAcked = False
    for packet in receiveQueue:
        if(currentPacket > packet.seqNum): # if the packet number is smaller than the currentAck, the packet has already
            # been acked before, request for the next window
            alreadyAcked = True
            break
    return alreadyAcked

#check if syn in order
def checkInOrder(receiveQueue):
    inOrder = True
    if(len(receiveQueue) < 2):
        inOrder = False
        return False
    else:
        prevSeq = receiveQueue[0].seqNum
        for x in [1,len(receiveQueue)]:
            currentSeq = receiveQueue[x].seqNum
            if(prevSeq+1 == currentSeq):
                inOrder = True
            else:
                inOrder = False
                return False
    return inOrder


def checkDuplicate(receiveQueue):
    isDuplicate = False
    previousSeq = receiveQueue[0].seqNum
    for x in range(1, len(receiveQueue)): #may need to edit this
        currentSeq = receiveQueue[x].seqNum
        if previousSeq == currentSeq:
            isDuplicate = True
            break
        previousAck = currentAck
    return isDuplicate

def main():
    global expectedSyn
    global currentAck

    sockobj = socket(AF_INET, SOCK_DGRAM)
    sockobj.bind(("", portCliServ))
    data, addr = sockobj.recvfrom(1024)
    packet = pickle.loads(data)
    totalPackets = packet.payload
    #get packet count
    print("Packet count:", packet.payload)
    print("waiting on port:", portCliServ)

    receiveQueue = []
    sendQueue = []

    opNum = 0 #used for keeping track of which number

    #print("finished writing file", totalPackets)

    #while 1:

    #expecting syn = 0
    #data, addr = sockobj.recvfrom(1024) #
    #packet = pickle.loads(data)
    #print("Received: ", packet.payload,packet.seqNum,packet.ackNum,  "From: ", addr)

    logWrite = open('receiverLog.txt', 'w')
    fileWrite = open(filePath, 'wb')

    while (currentAck < totalPackets):
        # keep waiting for packets until EOT arrives

        while 1:
            data, addr = sockobj.recvfrom(1024)

            incomingPacket = pickle.loads(data)
            if (incomingPacket.packetType == 0):  # if SYN packet, add to receiveQueue
                receiveQueue.append(incomingPacket)
                outputStr = str(opNum) + ". Recieving " + \
                            "type =" + str(incomingPacket.packetType) + \
                            " syn=" + str(incomingPacket.seqNum) + \
                            " ack=" + str(incomingPacket.ackNum) + \
                            " payload=" + str(incomingPacket.payload)
                print(outputStr)
                logWrite.write(outputStr + "\n")
                #print(opNum ,". Recieving", "type=", incomingPacket.packetType, "syn=", incomingPacket.seqNum, "ack=", incomingPacket.ackNum, "payload=", incomingPacket.payload)  # currentAck
                #logWrite.write(opNum ,". Recieving", "type=", incomingPacket.packetType, "syn=", incomingPacket.seqNum, "ack=", incomingPacket.ackNum, "payload=", incomingPacket.payload)
                opNum = opNum + 1
            elif (incomingPacket.packetType == 2):  # if EOT packet, break out of loop
                break  # finished getting data

        #for packet in receiveQueue:
            #print(packet.seqNum, packet.payload)
        # process the len(receiveQueue) packets
        # prepare packets to send here


        #something wrong here getting wrong code, error code 1, error code 4 problems
        #generates packets to send back to sender
        receiveCode = receiveCheck(receiveQueue, expectedSyn, totalPackets) #currentAck
        print("Receivecode=", receiveCode)
        logWrite.write("Receivecode= " + str(receiveCode) + "\n")


        if receiveCode == 0:  # got the last data
            # expectedSyn = expectedSyn + len(receiveQueue)
            for receivePacket in receiveQueue:
                #writeFile.write(receivePacket.payload)
                fileWrite.write(receivePacket.payload) #write to dest.txt
                sendPacket = Packet.Packet(1, expectedSyn, currentAck, windowSize, None)
                sendQueue.append(sendPacket)
                expectedSyn = expectedSyn + 1
                currentAck = currentAck + 1
            # write the last data to the file
            # send final acks
        elif receiveCode == 1:  # resend previous acks again
            # go back windowsize amount, and send acks in order again
            currentAck = currentAck - windowSize
            for x in range(currentAck, currentAck + windowSize):  # go back one windowsize and load the acks again to send
                sendPacket = Packet.Packet(1, expectedSyn, x, windowSize, None)
                sendQueue.append(sendPacket)
            currentAck = currentAck + windowSize
        elif receiveCode == 2:  # seq is in order
            # write to file
            # send windowsize amount acks in order

            for receivePacket in receiveQueue:
                #writeFile.write(receivePacket.payload)
                fileWrite.write(receivePacket.payload) #write to dest.txt
                sendPacket = Packet.Packet(1, expectedSyn, currentAck, windowSize, None)
                sendQueue.append(sendPacket)
                expectedSyn = expectedSyn + 1
                currentAck = currentAck + 1
        # elif receiveCode == 3 # empty queue, do nothing, wait for sender timeout receive
        # do nothing wait for sender timeout to receive
        elif receiveCode == 4:  # incomplete weapon, ask sender to send again by sending duplicate
            # send 4 4 4 4, if you received 4 packets and are wanting packet4,5,6,7
            for recievePacket in receiveQueue:
                sendPacket = Packet.Packet(1, expectedSyn, currentAck, windowSize, None)
                sendQueue.append(sendPacket)

        # send packets here
        #print("sleeping 1 sec")
        time.sleep(0.2)
        for packet in sendQueue:
            time.sleep(sendoutdelay)
            outputStr = str(opNum) + ". Sending " + \
                        "type =" + str(packet.packetType) + \
                        " syn=" + str(packet.seqNum) + " ack=" + str(packet.ackNum)
            print(outputStr)
            logWrite.write(outputStr + "\n")
            #print(opNum, ". Sending " + "type=", packet.packetType, "syn=", packet.seqNum, "ack=", packet.ackNum)
            #logWrite(opNum, ". Sending type=", packet.packetType, "syn=", packet.seqNum, "ack=", packet.ackNum)
            opNum = opNum + 1
            sockobj.sendto(pickle.dumps(packet), (netSimIP, portNetSim))
        sendEOT(sockobj)
        print("Sending EOT")



        receiveQueue.clear()
        sendQueue.clear()
    fileWrite.close()
    logWrite.close()






main()
