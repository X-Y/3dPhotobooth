from wave import open as waveOpen
from ossaudiodev import open as ossOpen

dat={"gfname":0,"s":0,"nc":0,"sw":0,"fr":0,"nf":0,"comptype":0,"compname":0,"dsp":0}

def openWave(fname):
	if fname!=None:
		dat["gfname"]=fname
	 
	dat["s"] = waveOpen(dat["gfname"],'rb')
	nc,sw,fr,nf,comptype, compname 	= dat["s"].getparams()
	dat["nf"]=nf
	dat["nc"]=nc
	dat["sw"]=sw
	dat["fr"]=fr
	dat["comptype"]=comptype
	dat["compname"]=compname

def initDev():
	dat["dsp"] = ossOpen('/dev/dsp','w')
	try:
		from ossaudiodev import AFMT_S16_NE
	except ImportError:
 		if byteorder == "little":
			AFMT_S16_NE = ossaudiodev.AFMT_S16_LE
		else:
			AFMT_S16_NE = ossaudiodev.AFMT_S16_BE
	dat["AFMT_S16_NE"]=AFMT_S16_NE

def initSound():
	dat["debugTest"]=dat["dsp"].setparameters(dat["AFMT_S16_NE"], dat["nc"], dat["fr"])
	
def playWave():
	dat["s"].rewind()
	data = dat["s"].readframes(dat["nf"])
	dat["dsp"].write(data)


def closeDev():
	dat["dsp"].close()
	dat.clear()

def closeWave():
	dat["s"].close()
	 
		
def test():
	import time
	initDev()
	
	openWave("beep-3.wav")
	initSound()
	playWave()
	
	for i in range(3):	
		print "beep"
		playWave()
		time.sleep(1.2)
	
	closeWave()
	
	openWave("camera-shutter-click-03.wav")
	initSound()
	print "click"
	playWave()
	closeWave()
	
	closeDev()
	'''
	openWave("camera-shutter-click-03.wav")
	initSound()
	time.sleep(1.2)
	playWave()
	closeWave()'''

if __name__=="__main__":
	print "wtf"
	test()
