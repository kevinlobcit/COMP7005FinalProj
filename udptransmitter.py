#!/usr/bin/python
import sys
from socket import *

import Packet
import pickle
import configparser
import time

# setup ip
# Globals
config = configparser.ConfigParser()
config.read('netSim.config')
netSimIP = config.get('default', 'netSimIp')
portNetSim = int(config.get('default', 'portNetSim'))
portCliServ = int(config.get('default', 'portCliServ'))
windowSize = int(config.get('default', 'window'))
packetSize = int(config.get('default', 'packetSize'))

currentSyn = int(config.get('starting', 'syn'))
expectedAck = int(config.get('starting', 'ack'))

sendoutdelay = float(config.get("default", "sendOutDelay"))

max_retries = int(config.get("default", "maxretries"))

filePath = config.get('filepath', 'src')

timeout

print("printing config")
print("netSimIp =", netSimIP)
print("portNetSim =", portNetSim)
print("portCliServ =", portCliServ)
print("windowSize =", windowSize)
print("packetSize =", packetSize)
print("expectedSyn =", currentSyn)
print("currentAck =", expectedAck)


# loads the
def prepareSend(filePackets, sendQueue, currentSyn, windowSize):
    pktRange = currentSyn + windowSize
    if (pktRange > len(filePackets)):
        pktRange = len(filePackets)
    for x in range(currentSyn, pktRange):
        sendQueue.append(filePackets[x])


def sendEOT(socket):
    eotPack = Packet.Packet(2, 0, 0, 0, 0)
    socket.sendto(pickle.dumps(eotPack), (netSimIP, portNetSim))


def receiveCheck(receiveQueue, currentPacket, totalPackets):
    isDuplicate = checkDuplicate(receiveQueue)
    if (len(receiveQueue) + currentPacket == totalPackets):
        # it is the last data, write to file and close program
        return 0
    elif (len(receiveQueue) == windowSize):
        # check if duplicate acks
        if (isDuplicate):  # is duplicate acks  |receiver duplicate acks/out of order, resend from the ack number described, currentSyn = packet.ackNum
            return 1
            # return 1
        else:  # not duplicate acks means      |its in order can write to file and proceed
            return 2
        # return 2

    elif (len(receiveQueue) == 0):  # empty queue, wait for, receiver timeout
        return 3
        # return 3
    elif (receiveQueue != windowSize):  # check if duplicate acks    |resend starting from the ack number described
        if (isDuplicate):  # is duplicate acks, resend starting from currentSyn = packet.ackNum
            return 1
            # return 1
        else:  # not duplicate  |go back and resend the window again, an ack has been lost, currentSyn - windowsize
            return 4
        # return 4

        # if len(receiveQueue) == 0, it is empty
            # let timeout on receiver and wait for timeout resend ACKS
        # if len(receiveQueue) + currentPackets == totalPackets
            # completed sending the file, close and break
        # if len(receiveQueue) == windowSize
            # if duplicate,
                # resend from ack# described
            # else #its not duplicate
                # received acks in order
                # expectedAck = expectedAck + windowSize
                # proceed to next set of window
        # if len

# works
def checkDuplicate(receiveQueue):
    previousAck = receiveQueue[0].ackNum
    isDuplicate = False
    #print(len(receiveQueue))
    for x in range(1, len(receiveQueue)):
        #print("x=",x)
        currentAck = receiveQueue[x].ackNum
        if previousAck == currentAck:
            isDuplicate = True
            break
        previousAck = currentAck
    return isDuplicate

def main():
    global currentSyn
    global expectedAck  # need to implement ack checking

    logWrite = open("transmitterLog.txt", "w")

    filePackets = []

    # load packetetized file into array
    loadFileSyn = currentSyn
    readFile = open(filePath, 'rb')  # open file to read
    dataBin = readFile.read(packetSize) ###
    while dataBin:
        dataPacket = Packet.Packet(0, loadFileSyn, 0, windowSize, dataBin)  # Put the data into a packet
        filePackets.append(dataPacket)  # Add the packet to the array
        dataBin = readFile.read(packetSize)  # Read the next packetSize data ##
        loadFileSyn = loadFileSyn + 1  # increment

    totalPackets = len(filePackets)  # 2730 packets with alice wonderland 64byte data packets
    print(totalPackets, "Packets total of data")

    # host is to the network simulator which will forward to the server
    sockobj = socket(AF_INET, SOCK_DGRAM)
    sockobj.bind(("", portCliServ))
    # send total packet amount to reciever
    totalPacket = Packet.Packet(-1,-1,-1,0,totalPackets)
    sockobj.sendto(pickle.dumps(totalPacket), (netSimIP, portNetSim))

    currentSyn = 0
    #currentAck = 0  # was 0
    sendQueue = []  # make array to hold packets to send
    receiveQueue = []
    # print (sendQueue)
    #max_retries = 5

    timeoutBreak = False

    #to go back to the beginning of current window, window-1

    opNum = 0

    # preparesend working ok
    while (currentSyn < totalPackets):
        time.sleep(0.2)
        prepareSend(filePackets, sendQueue, expectedAck, windowSize) #expected ack replace currentsyn
        for packet in sendQueue:
            # add the syn and ack nums to packet
            packet.seqNum = currentSyn
            packet.ackNum = expectedAck  # currentack
            time.sleep(sendoutdelay)
            sockobj.sendto(pickle.dumps(packet), (netSimIP, portNetSim))
            currentSyn = currentSyn + 1
            outputStr = str(opNum) + ". Sending type=" + str(packet.packetType) + " seq=" + str(packet.seqNum) + " ack=" + str(packet.ackNum) + " payload=" + str(packet.payload)
            logWrite.write(outputStr + "\n")
            print(outputStr)
            #print(opNum, ". Sending type=", packet.packetType, "seq=", packet.seqNum, "ack=", packet.ackNum, "payload=",packet.payload)  # currentSyn
            opNum = opNum + 1
        sendEOT(sockobj)
        print("Sending EOT")
        #logWrite.write("Sending EOT" + "\n")

        #print(currentSyn)
        #expectedAck += windowSize #tester stuff
        #sendQueue.clear()

        #wait for packets back
        EOTarrived = False
        while not EOTarrived: #1
            # check if it is an EOT packet
            for _ in range(max_retries): # retry sending until max retries for a certain window then break program
                try:
                    sockobj.settimeout(4)
                    data, addr = sockobj.recvfrom(1024)
                    incomingPacket = pickle.loads(data)
                    if incomingPacket.packetType == 1:  # if ack packet, add to receiveQueue
                        receiveQueue.append(incomingPacket)
                        outputStr = str(opNum) + ". Incoming type=" + str(incomingPacket.packetType) + " seq=" + str(
                            incomingPacket.seqNum) + " ack=" + str(incomingPacket.ackNum)
                        print(outputStr)
                        #print(opNum, ". Incoming type=", incomingPacket.packetType, "seq=", incomingPacket.seqNum, "ack=", incomingPacket.ackNum)  # currentSyn
                        logWrite.write(outputStr + "\n")

                        opNum = opNum + 1
                    elif incomingPacket.packetType == 2:  # if EOT packet, break out of loop
                        print("Got EOT")
                        logWrite.write("Got EOT" + "\n")
                        EOTarrived = True
                        break  # finished getting data
                except timeout:
                    print("Timed out")
                    logWrite.write("Timed out" + "\n")
                    for packet in sendQueue:
                        time.sleep(sendoutdelay)
                        sockobj.sendto(pickle.dumps(packet), (netSimIP, portNetSim))
                        outputStr = str(opNum) + ". Sending type=" + str(packet.packetType) + " seq=" + str(packet.seqNum) + " ack=" + str(packet.ackNum) + " payload=" + str(packet.payload)
                        print(outputStr)
                        logWrite.write(outputStr + "\n")
                        #print(opNum, ".Sending type=", packet.packetType, "seq=", packet.seqNum, "ack=", packet.ackNum, "payload=",packet.payload)  # currentSyn
                        opNum = opNum + 1
                    sendEOT(sockobj)
                    print("Sending EOT")
                    #logWrite.write("Sending EOT" + "\n")
            #print("Got packets")
            sockobj.settimeout(None)
        #EOTarrived = False

        # process the receiveQueue

        #print("Doing receiveCheck")
        receiveCode = receiveCheck(receiveQueue, expectedAck, totalPackets)
        print("Receivecode=", receiveCode)
        logWrite.write("Receivecode= " + str(receiveCode) + "\n")


        if receiveCode == 0:  # finished sending, program ends
            expectedAck = expectedAck + len(receiveQueue)  # expectedAck
            break
        elif receiveCode == 1:  # received duplicate ack in receiveQueue, acknum points to current syn it wants
            # set currentSyn = any received packet.ackNum
            currentSyn = receiveQueue[0].ackNum
            expectedAck = receiveQueue[0].ackNum

        elif receiveCode == 2:  # received #windowsize receiveQueue acks in order, ok to send next window
            expectedAck = expectedAck + len(receiveQueue)  # adds windowsize to currentAck #expectedAck
            #can write to file

            # elif receiveCode == 3: #empty receiveQueue, only got EOT all packets lost, let it timeout
            # do nothing receiever go timeout

        elif receiveCode == 4:  # out of order acks, resend the sendQueue again #something wrong here
            #|0 1 2 3|4 5 6 7| going from index 7 back to #4 is -(windowsize-1)
            # set currentSyn = currentSyn - windowSize
            currentSyn = currentSyn - windowSize

        receiveQueue.clear()
        sendQueue.clear()


main()
