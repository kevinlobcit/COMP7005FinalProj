clientIp, serverIp, netSimIp: can be freely changed to any IP address you wish

portNetSim, portCliServ: are the port numbers corrosponding incoming traffic, data enters the transmitter or receiver through the
	portNetSim or portCliServ

window: can be any range from 4 and above, it determins how many packets are sent before an EOT is sent

packetSize: it determines how much data to load into the packet as the packet.payload when reading a file into packets

dropRate: 0-100 number of the % rate to drop packets. set to -1 to disable packet dropping

delayMax: the time delay caused by time.sleep(delayMax) in the net simulator, it should be lower than than 4 seconds which is the timeout

sendOutDelay: the time delay on the transmitter/receiver to delay how fast packets are sent out
	this is to prevent external interference such as the home router dropping packets instead of
	the network simulator dropping packets.

src: source file to read from
dest: destination file to read to
 
