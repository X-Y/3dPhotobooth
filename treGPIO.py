import time
import os
import subprocess

baseAddr="/sys/class/gpio/gpio"
pinMapping={110:"38",111:"39",112:"64",105:"33",117:"114",115:"66",113:"68",111:"39",109:"37",107:"35",105:"33"}

INPUT=0
OUTPUT=1


def getPinDire(pin, action):
	pinStr=pinMapping.get(pin)
	actionStr="value"
	if action=="pinMode":
		actionStr="direction"
	return "%s%s/%s"%(baseAddr,pinStr,actionStr)

def makeCmd_Write(pin, action, value):
	dire=getPinDire(pin,action)
	cmd="echo \"%s\" > %s"%(value,dire)		
	#print(cmd)
	return cmd

def makeCmd_Read(pin):
	dire=getPinDire(pin,None)
	return ("cat",dire)
	

def pinMode(pin,mode):
	modeStr="out"
	if mode==INPUT:
		modeStr="in"
	cmd=makeCmd_Write(pin,"pinMode",modeStr)
	os.system(cmd)

def digitalWrite(pin,direction):
	temp="0"
	if direction==True:
		temp="1"
	cmd=makeCmd_Write(pin,"value",temp)
	os.system(cmd)

def digitalRead(pin):
	cmd=makeCmd_Read(pin)
	res=subprocess.check_output([cmd[0],cmd[1]])
	return int(res.strip())

def test():
	pins=(117,115,113,111,109)
	pin=105
	pinMode(pin,OUTPUT)

	while True:
		digitalWrite(pin,True)
		time.sleep(0.5)
		digitalWrite(pin,False)
		time.sleep(0.5)
	
	'''
	for p in range(5):
		pinMode(pins[p],OUTPUT)

	cp=0
	while True:
		cp=(cp+1)%5
		for i in range(5):
		        digitalWrite(pins[i],False)
		digitalWrite(pins[cp],True)
		time.sleep(0.5)
	'''
	'''
	pinMode(pin, INPUT)
	while True:
		print(digitalRead(pin))
		time.sleep(0.01)
	'''

if __name__=="__main__":
	test()
	
