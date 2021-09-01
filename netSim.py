#!/usr/bin/python

from socket import *

import pickle
import configparser
from datetime import datetime
from random import seed
from random import randint
import random
import time

config = configparser.ConfigParser()
config.read('netSim.config')
clientIP = config.get('default', 'clientIP')
serverIP = config.get('default', 'serverIP')
portNetSim = int(config.get('default', 'portNetSim'))
portCliServ = int(config.get('default', 'portCliServ'))
dropRate = float(config.get('default', 'dropRate'))
delayMax = float(config.get('default', 'delayMax'))

packetnum = 0

print("printing config")
print("clientIp = " + clientIP)
print("serverIp = " + serverIP)
print("portNetSim =", portNetSim)
print("portCliServ =", portCliServ)
print("dropRate = " + str(dropRate))
print("delayMax = " + str(delayMax))

def delayPacket():
    print("delaying packet")

def dropPacket():
    print("dropping packet")

def main():
    global packetnum

    seed(1) #seed the rng
    logWrite = open("netSimLog.txt", "w")

    sockRecieve = socket(AF_INET, SOCK_DGRAM)
    sockRecieve.bind(("", portNetSim))
    print("waiting on port:", portNetSim)

    sockSend = socket(AF_INET, SOCK_DGRAM)
    sockSend.bind(("", portCliServ))

    while 1:
        data, addr = sockRecieve.recvfrom(1024)
        pack = pickle.loads(data)

        randomDelay = random.uniform(0, delayMax)
        time.sleep(randomDelay)

        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S:%f')

        randomDrop = randint(0,100)
        if(randomDrop > dropRate):
            #check what address if its from
            if addr[0] == clientIP:
                outputStr = timestamp + " " + str(packetnum) + ". " + clientIP + " -> " + serverIP + " type=" + str(
                    pack.packetType) + " sleep=" + str(randomDelay)
                #print(timestamp, packetnum,".", clientIP, "->", serverIP, "type=",pack.packetType, "sleep=", randomDelay)#pack.payload
                sockSend.sendto(data, (serverIP, portCliServ))

            elif addr[0] == serverIP:
                outputStr = timestamp + " " + str(packetnum) + ". " + clientIP + " <- " + serverIP + " type=" + str(
                    pack.packetType) + " sleep=" + str(randomDelay)
                #print(timestamp, packetnum,".", clientIP, "<-", serverIP, "type=",pack.packetType, "sleep=", randomDelay)
                sockSend.sendto(data, (clientIP, portCliServ))
        else:
            if addr[0] == clientIP:
                outputStr = timestamp + " " + str(packetnum) + ". " + clientIP + " -> " + serverIP + " type=" + str(
                    pack.packetType) + " sleep=" + str(randomDelay) + " DROPPED"
                #print(timestamp, packetnum,".", clientIP, "->", serverIP, "type=",pack.packetType, "sleep=", randomDelay, "DROPPED")#pack.payload

            elif addr[0] == serverIP:
                outputStr = timestamp + " " + str(packetnum) + ". " + clientIP + " <- " + serverIP + " type=" + str(
                    pack.packetType) + " sleep=" + str(randomDelay) + " DROPPED"
                #print(timestamp, packetnum,".", clientIP, "<-", serverIP, "type=",pack.packetType, "sleep=", randomDelay, "DROPPED",)
        print(outputStr)
        logWrite.write(outputStr + "\n")

        packetnum += 1


main()
