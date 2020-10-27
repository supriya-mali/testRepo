#!/usr/bin/env python3 
#coding=utf-8

import serial
import time
import struct
import threading
import csv
import os, stat
import platform
from goto import goto, label
from datetime import datetime, timedelta
fields = ['Date','Time','Voltage','Current','Power']
filename = "VoltageReadings_";

class BTPOWER:

	setAddrBytes 		=	[0xB4,0xC0,0xA8,0x01,0x01,0x00,0x1E]
	readVoltageBytes 	= 	[0xB0,0xC0,0xA8,0x01,0x01,0x00,0x1A]
	readCurrentBytes 	= 	[0XB1,0xC0,0xA8,0x01,0x01,0x00,0x1B]
	readPowerBytes 		= 	[0XB2,0xC0,0xA8,0x01,0x01,0x00,0x1C]
	readRegPowerBytes 	= 	[0XB3,0xC0,0xA8,0x01,0x01,0x00,0x1D]

	def __init__(self, com="/dev/ttyUSB0", timeout=10.0):
		self.ser = serial.Serial(
			port=com,
			baudrate=9600,
			parity=serial.PARITY_NONE,
			stopbits=serial.STOPBITS_ONE,
			bytesize=serial.EIGHTBITS,
			timeout = timeout
		)
		if self.ser.isOpen():
			self.ser.close()
		self.ser.open()

	def checkChecksum(self, _tuple):
		_list = list(_tuple)
		_checksum = _list[-1]
		_list.pop()
		_sum = sum(_list)
		if _checksum == _sum%256:
			return True
		else:
			raise Exception("Wrong checksum")
			
	def isReady(self):
		self.ser.write(serial.to_bytes(self.setAddrBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				return True
		else:
			raise serial.SerialTimeoutException("Timeout setting address")

	def readVoltage(self):
		self.ser.write(serial.to_bytes(self.readVoltageBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				tension = unpacked[2]+unpacked[3]/10.0
				return tension
		else:
			raise serial.SerialTimeoutException("Timeout reading tension")

	def readCurrent(self):
		self.ser.write(serial.to_bytes(self.readCurrentBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				current = unpacked[2]+unpacked[3]/100.0
				return current
		else:
			raise serial.SerialTimeoutException("Timeout reading current")

	def readPower(self):
		self.ser.write(serial.to_bytes(self.readPowerBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				power = unpacked[1]*256+unpacked[2]
				return power
		else:
			raise serial.SerialTimeoutException("Timeout reading power")

	def readRegPower(self):
		self.ser.write(serial.to_bytes(self.readRegPowerBytes))
		rcv = self.ser.read(7)
		if len(rcv) == 7:
			unpacked = struct.unpack("!7B", rcv)
			if(self.checkChecksum(unpacked)):
				regPower = unpacked[1]*256*256+unpacked[2]*256+unpacked[3]
				return regPower
		else:
			raise serial.SerialTimeoutException("Timeout reading registered power")

	def readAll(self):
		if(self.isReady()):
			return(self.readVoltage(),self.readCurrent(),self.readPower(),self.readRegPower())

	def close(self):
		self.ser.close()

#fields date time voltage current power		
if __name__ == "__main__":
    try:
        #get sensor 
        sensor = BTPOWER()
        today = datetime.today()
        now = datetime.now()
        #checking readines
        print("checking readiness")
        print(sensor.isReady())
        
        while 1:            #this one is main loop
            #open the file in write 
            past = datetime.now()
            filename = filename+today.strftime("%d_%m_%Y")+'.csv'
            with open(filename,'a') as csvfile:            #To open file in write mode use 'w' and  for append use 'a'
                print("filename",filename)
                filename = 'VoltageReadings_'
                fileDate = datetime.today()                     #file creation date
                #creting a csv writer object
                csvwriter = csv.writer(csvfile)
                #writing the fields
                csvwriter.writerow(fields)
                #start while from here
                while 1:                                    #day loop
                    d1 = datetime.now()
                    current_time = now.strftime("%H: %M: %S")
                    #get data in row
                    try:
                        rows = [d1.strftime("%D"), current_time, sensor.readVoltage(), sensor.readCurrent(), sensor.readPower()]        #add exception handling for no data
                    except serial.SerialTimeoutException:
                        print("No Electricity")
                        csvwriter.writerow("No Electricity", now.strftime("%H: %M: %S"))
                        sensor.close()
                        time.sleep(60)
                        main()
                        
                    #writing the data rows
                    csvwriter.writerow(rows)
                    if past.strftime("%D") < d1.strftime("%D"):
                        print("past.strf",strftime("%D"))
                        break

    #except serial.SerialTimeoutException:           #return from here
     #   print("Printing")

    finally:
        sensor.close()
