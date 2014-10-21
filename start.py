#!/usr/bin/python
# Creates Anaglyph 3D Images from two USB cameras
# Version 1.0 2014-04-12

import cv2
import time
import multiprocessing
import numpy as np
#import RPi.GPIO as GPIO
import cups
import math

import pbSound as ps
import treGPIO as gp
print "All libs imported"

DO_PRINT=True
camera_dim=[(1920,1080,1),(1280,720,1.5),(960,540,2)]
cdSel=1
countDown=4
Mfactor=camera_dim[cdSel][2]
cupsIP="192.168.1.103"

# Define variables
paperwidth = 1240		# Paper width in pixels (should be 1240)
paperheight = 3508		# Paper height in pixels (should be 3508)
framecount = 4			# Number of photos per photostrip
timediff = 4			# Minimum time between images (only has an effect if cameras are faster)

'''
#AVTRE
offsetw = math.ceil(135/Mfactor)			# Adjustment of anaglyph effect (left-right adj)
offseth = math.ceil(-10/Mfactor)			# Adjust the height alignment of the two pictures
'''
'''
#tre2
offsetw = math.ceil(90/Mfactor)			# Adjustment of anaglyph effect (left-right adj)
offseth = math.ceil(0/Mfactor)			# Adjust the height alignment of the two pictures
'''

#TRE3
offsetw = math.ceil(170/Mfactor)			# Adjustment of anaglyph effect (left-right adj)
offseth = math.ceil(-30/Mfactor)			# Adjust the height alignment of the two pictures



scalefactor = .3*Mfactor		# Scale down factor for saveimg
mask = 'mask.png'		# Black and white (monocrome) mask
logo = 'logo.png'		# Image for bottom row


# Define GPIO stuff
pinBtn=107
pinBtnLed=117
pinLeds=(115,113,111,109)
pinRelay=105

gp.pinMode(pinBtn,gp.INPUT)
gp.pinMode(pinBtnLed,gp.OUTPUT)
gp.pinMode(pinRelay,gp.OUTPUT)
for i in range(4):
	gp.pinMode(pinLeds[i],gp.OUTPUT)

def turnLedsOn(num):
	for i in range(4-num):
		gp.digitalWrite(pinLeds[i],False)
	for j in range(4-num,4):
		gp.digitalWrite(pinLeds[j],True)

# Set up rke ps.inter using CUPS
cups.setServer(cupsIP)
conn = cups.Connection()			# Connect to CUPS
printer = conn.getDefault()	# Get the default printer
printers = conn.getPrinters()
for printer in printers: 
	printer_name = printers.keys()[0]
	print "Found printer", printer_name



# Multiprocessing function to grab frame from cam
# Input: num (camera device no), images (shared dictionary to contain images)
def multigrab(num, images):
	capture = cv2.VideoCapture(num)	# Capture the camera with device number 'num'
	capture.set(3,camera_dim[cdSel][0])	# Width of the captured image
	capture.set(4,camera_dim[cdSel][1])	# Height of the captured image
	status, image = capture.read()	# Read one frame from camera
	timestamp = int(round(time.time() * 1000))
	capture.release()				# Release the camera
	print "Camera ", num, timestamp, status
	if status:						# Only if the capture was sucessful
		images[num] = image			# Save image to the shared dictionary
	else:
		print "Failed to read image from camera ", num, "."
		errorflash()




# Function for cropping and creating anaglyph image
# Input: list of two images, desired image width and desired image height
# Return: one anaglyph image
def anaglyph(images, imagewidth, imageheight):
	# Crop image
	dim = images[0].shape						
	# Get height, width of first image
	print "The captured image is", dim[1], "x", dim[0]
	if imagewidth>dim[1] or imageheight>dim[0]:
		if offsetw<0:
			param32=0
			param3=-offsetw
			if dim[1]+offsetw>imagewidth:
				param4=-offsetw+imagewidth
				param42=imagewidth
			else:
				param4=dim[1]
				param42=dim[1]+offsetw
		else:
			param32=offsetw
			param3=0
			if dim[1]-offsetw>imagewidth:
				param42=offsetw+imagewidth
				param4=imagewidth
			else:
				param42=dim[1]
				param4=dim[1]-offsetw
				
		if offseth>0:
			param1=0
			param2=dim[0]-offseth
			param12=offseth
			param22=dim[0]
		else:
			param1=-offseth
			param2=dim[0]
			param12=0
			param22=dim[0]+offseth
		images[0]=images[0][param1:param2,param3:param4]
		images[1]=images[1][param12:param22,param32:param42]
		'''images[0]=images[0][0:dim[0]-offseth,-offsetw:dim[1]]
		images[1]=images[1][offseth:dim[0],0:dim[1]+offsetw]'''
		#print images[0].shape,images[1].shape
	else:	
		deltah = (dim[0] - imageheight)/2 - offseth			# Define first row of final image
		endh = deltah + imageheight							# Define last row of final image
		deltaw = (dim[1] - imagewidth)/2 - offsetw			# Define first column of final image
		endw = deltaw + imagewidth							# Define last column of final image

		images[0] = images[0][deltah:endh, deltaw:endw]		# Crop left image
		deltaw = (dim[1] - imagewidth)/2			# ReDefine first column of final image
		endw = deltaw + imagewidth 							# Redefine last column for the other image
		deltah = (dim[0] - imageheight)/2					# Redefine first row for the other image
		endh = deltah + imageheight 							# Redefine last row for the other image
														# We don't include the offset this time
		images[1] = images[1][deltah:endh, deltaw:endw]		# Crop right image
		
	# Anaglyph
	b1,g1,r1 = cv2.split(images[0])			# Split the first image into BGR
	b2,g2,r2 = cv2.split(images[1])			# Split the second image into BGR
	anaglyphimage = cv2.merge((b1,g1,r2)) 	# Merge B and G channel from left camera with R channel from right camera
	
	#print "sth sth",type(anaglyphimage)
 
	if imagewidth>dim[1] or imageheight>dim[0]:
		dim=anaglyphimage.shape
		tmp=np.zeros((imageheight,imagewidth,3),np.uint8)
		tmp[:,:]=[255,255,255]
		starth=(imageheight-dim[0])/2
		endh=starth+dim[0]
		startw=(imagewidth-dim[1])/2
		endw=startw+dim[1]
		
		tmp[starth:endh,startw:endw]=np.array(anaglyphimage)
		return  tmp
	else:
		return anaglyphimage


def errorflash():
	for i in range(50):
		gp.digitalWrite(pinBtnLed,True)
		time.sleep(.1)
		gp.digitalWrite(pinBtnLed,False)
		time.sleep(.1)		



# Function for initating image capture, image save and image print
# Called from the main function
def photo():
	try:
		timestart = int(round(time.time()))
	
		# Do some basic calculations for image dimenstions
		logoimage = cv2.imread(logo)						# Open the logo file
		logodim = []
		logodim = logoimage.shape							# Get height, width and depth of the logo file in a list
		if (logodim[1] != paperwidth):						# Adjust the dimensions of the logo if necessary
			print "The logo is the wrong width and will be scaled." 
			logoheight = logodim[0]*paperwidth/logodim[1]	# This will be the new height of the logo
															# (The width of the logo is decided by the paper width)
	
		totalimageheight = paperheight - logodim[0]			# Calculate space avalible for the photos
		imageheight = totalimageheight/ framecount			# Calculate the heiht of each photo
		imagewidth = paperwidth								# The images are as wide as the paper
		print "Each photo will be", imageheight, "px high and", imagewidth, "px wide."
		print "The logo will be ", logodim[0], "px high and", imagewidth, "px wide."
		
	
		# Try to grab images from the cameras in two parallel threads	
		leftimgs = []							# This is where we will store the left images
		rightimgs = []							# This is where we will store the right images
		
		ps.initDev()
		for i in range(framecount):				# This will loop for each anaglyph photo we want
			print "Starting cycle for photo", i	
			framestart = time.time()
			jobs = []								# This is a list where we will store the jobs
			manager = multiprocessing.Manager()		# A Manager() is some sort of magic shared variable for multiprocessing
			images = manager.dict()					# Our two (L+R) images will be a dictionary stuffed into the manger
			#GPIO.output(8,True)						# Turn the camera lights on
			#ledsOn=4
			ps.openWave("beep-3.wav")
			ps.initSound()
			for effTimer in range(countDown):
				ps.playWave()
				time.sleep(1.0)
			ps.closeWave()
			ps.openWave("camera-shutter-click-03.wav")
			ps.initSound()
			ps.playWave()
			ps.closeWave()
			
			gp.digitalWrite(pinRelay,True)	
			for j in range(2):						# Create two jobs, one for each camera 
				p = multiprocessing.Process(target=multigrab, args=(j, images))		# Create the job, send the index i and the shared manager dictionary
				print "Created job for camera", j
				jobs.append(p)						# Append the job to the jobs list
				p.start()							# Start the jobs in the job list
				print "Waiting for the two camera processes to finish."
				p.join()								# Wait for the two camera processes to finish.
			print "The two camera processes has finished."							
			#GPIO.output(8,False)					# Turn lights off
			leftimgs.append(images[0])				# Add photos from camera 0 to the list of the left hand photos
			rightimgs.append(images[1])				# Add photos from camera 1 to the list of the right hand photos
			# Wait function
			gp.digitalWrite(pinRelay,False)
			for j in range(i+1):
				gp.digitalWrite(pinLeds[j],True)
			for j in range(i+1,framecount-i):
				gp.digitalWrite(pinLeds[j],False)
			time.sleep(1)
			'''
			if (i < (framecount - 1)):				# We don't need to pause after last image
				while (time.time() < (framestart + timediff)):
					time.sleep(.01)
			'''
		ps.closeDev()
		imglist = []						# Create a list where we can store our finished photos
		
		
		# Crop and make anaglyph images 
		for i in range(framecount):					# Loop for each frame on the finished photo slip
			thisimg = [leftimgs[i], rightimgs[i]]	# Make a list of one left hand photo and one right hand photo
			threedimage = anaglyph(thisimg, imagewidth, imageheight)	# Send the two photos and the desired dimensions to the anaglyph function
			imglist.append(threedimage)				# Add the created anaglyph image to the image list
			del threedimage						# Clear the variables, hoping to save some RAM
			del thisimg
			
				
		# Mask the images
		maskimage = cv2.imread(mask)				# Open the mask file
		if (imglist[0].shape != maskimage.shape):	# Check the dimensions of the mask and compare it to the dimension of the anaglyph images
			print "The mask is the wrong size and will be stretched."
			y, x, d = imglist[0].shape				# Fetch the dimensions from the first anaglyph image
			print "(Should be", x, "x", y, "pixels)"
			maskimage = cv2.resize(maskimage,(x,y))	# Rezise the mask (proportions will be skewed if necessary)
		maskimagegray = cv2.cvtColor(maskimage,cv2.COLOR_BGR2GRAY)
		ret, masklayer = cv2.threshold(maskimagegray, 10, 255, cv2.THRESH_BINARY)
		maskimage_fg = cv2.bitwise_and(maskimage,maskimage,mask = masklayer)
		for i in range (framecount):						
			imglist[i] = cv2.add(imglist[i],maskimage_fg)	# Mask each image
		
		del maskimage
		del maskimagegray
		del maskimage_fg
		
		# Make the photoslip (this is the only thing that is absolute and not dependent on 'framecount', because I was too lazy/stupid to figure it out)
		photoslip = np.concatenate((imglist[0], imglist[1], imglist[2], imglist[3], logoimage), axis=0)
		
		del imglist
		
		timeneed =  int(round(time.time())) - timestart
		print "Total tid: ", timeneed, " s"
	
		# Save the high resolution photoslip in a temporary file, for the printer
		cv2.imwrite('printfile.jpg', photoslip)
		
		
		# Print the photostrip from the saved file
		if DO_PRINT:
			printed = conn.printFile(printer, "printfile.jpg", "Photoslip", {})
			print "Photostrip sent to", printer_name, "queue as", printed, "."
		else:
			print "not really printed"
		
		# Scale the photoslip for saving
		y, x, d = photoslip.shape			# Get the total dimensions (should be same as defined paperheight/-width) Update?
		y = int(round(y * scalefactor))		# Set x dimenstion for saved photostrip
		x = int(round(x * scalefactor))		# Set y dimenstion for saved photostrip
		saveimg = cv2.resize(photoslip,(x,y))	# Scale the photostrip
		filename = "photoslips/Photoslip " + str(time.strftime("%H.%M.%S")) + ".jpg"	# Define file name
		print "Saving photoslip as:", filename
		cv2.imwrite(filename, saveimg)		# Save the photostrip
		print "Photoslip saved"
		
		del photoslip
		del saveimg
		
		for i in range(framecount):
			gp.digitalWrite(pinLeds[i],False)
		# Ready for next photostrip. Heading back to main() to wait for button input
		print "Ready..."
	except:
		print "There was an error, please try again"
		errorflash()
		raise

def main():
	try:
		print "Ready..."
		while True:
			
			#txt=raw_input()
			if gp.digitalRead(pinBtn)==False:#txt == "snap" or 
				photo()
				gp.digitalWrite(pinBtnLed,False)
			else:
				gp.digitalWrite(pinBtnLed,True)
			'''
			if gp.digitalRead(pinBtn)==False:
				gp.digitalWrite(pinBtnLed,False)
				photo()
			else:
				gp.digitalWrite(pinBtnLed,True)
			'''
			'''if (GPIO.input(3)):
				GPIO.output(10,False)
				photo()
			else:
				GPIO.output(10,True)'''
	except KeyboardInterrupt:
		pass
		#GPIO.cleanup()
    
if __name__ == '__main__':
	main()



