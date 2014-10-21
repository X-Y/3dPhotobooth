# 
# Creates Anaglyph 3D Images from two USB cameras
# Version 1.1 2014-04-06
# Updates:
#	Trying to separate channels directly after capture, to save RAM

import cv2
import time
import multiprocessing
import numpy as np
import RPi.GPIO as GPIO
import cups
print "All libs imported"


# Define variables
paperwidth = 1240		# Paper width in pixels (should be 1240)
paperheight = 3508		# Paper height in pixels (should be 3508)
framecount = 4			# Number of photos per photostrip
timediff = 1			# Time between images
offsetw = 190			# Adjustment of anaglyph effect (left-right adj)
offseth = 0				# Adjust the height alignment of the two pictures
scalefactor = .3		# Scale down factor for saveimg
mask = 'mask.png'		# Black and white (monocrome) mask
logo = 'logo.png'		# Image for bottom row


# Define GPIO stuff
GPIO.cleanup()				# Clean up, just in case things got fubar last time
GPIO.setmode(GPIO.BOARD)	# Use board pin numbering
GPIO.setwarnings(False)		# Disable GPIO warnings
GPIO.setup(3,GPIO.IN)		# Pin 3 - Button
GPIO.setup(10, GPIO.OUT)	# Pin 10 - LED in button
GPIO.output(10,False)		# Turn LED off
GPIO.setup(8, GPIO.OUT)		# Pin 8 - Relay for lights 
GPIO.output(8,False)		# Turn lights off



# Set up printer using CUPS
conn = cups.Connection()			# Connect to CUPS
printer = conn.getDefault()			# Should probably remove this row. Try that once CUPS is avlafivasble. 
printers = conn.getPrinters()
for printer in printers: 
	printer_name = printers.keys()[0]
	print "Found printer", printer_name



# Multiprocessing function to grab frame from cam
# Input: num (camera device no), images (shared dictionary to contain images)
def multigrab(num, images):
	capture = cv2.VideoCapture(num)	# Capture the camera with device number 'num'
	capture.set(3, 1920)			# Width of the captured image (not sure if this is necessary)
	capture.set(4, 1080)			# Height of the captured image
	status, image = capture.read()	# Read one frame from camera
	timestamp = int(round(time.time() * 1000))
	capture.release()				# Release the camera
	print "Camera ", num, timestamp, status
	channel = {}
	if status:						# Only if the capture was sucessful
		if (num == 0):
			images[b], images[g], r = cv2.split(image)	# Save the blue and green channels to the shared dictionary
														# Try to find out if the r channel can be discarded
		else:
			b, g, images[r] = cv2.split(image)			# Save the red channel to the shared dictionary
	else:
		print "Failed to read image from camera ", num, "."



# Function for cropping and creating anaglyph image
# Input: list of two images, desired image width and desired image height
# Return: one anaglyph image
def anaglyph(images, imagewidth, imageheight):
	# Crop image
	#dim = images[0].shape								# Get height, width of first image
	dim = []		# Temporary solution for image resolution 
	dim[0] = 1080
	dim[1] = 1920
	print "The captured image is", dim[1], "x", dim[0]
	deltah = (dim[0] - imageheight)/2 - offseth			# Define first row of final image
	endh = deltah + imageheight							# Define last row of final image
	deltaw = (dim[1] - imagewidth)/2 - offsetw			# Define first column of final image
	endw = deltaw + imagewidth							# Define last column of final image

	images[b] = images[b][deltah:endh, deltaw:endw]		# Crop left image
	images[g] = images[g][deltah:endh, deltaw:endw]		# Crop left image

	deltaw = (dim[1] - imagewidth)/2					# Redefine first column for the other image
	endw = deltaw + imagewidth 							# Redefine last column for the other image
														# We don't include the offset this time
	images[r] = images[r][deltah:endh, deltaw:endw]		# Crop right image
	
	# Anaglyph
	#b1,g1,r1 = cv2.split(images[0])			# Split the first image into BGR
	#b2,g2,r2 = cv2.split(images[1])			# Split the second image into BGR
	anaglyphimage = cv2.merge((images[b],images[g],images[r])) 	# Merge B and G channel from left camera with R channel from right camera
	return anaglyphimage



# Function for initating image capture, image save and image print
# Called from the main function
def photo():
	timestart = int(round(time.time()))

	# Do some basic calculations for image dimenstions
	logoimage = cv2.imread(logo)						# Open the logo file (maybe it is uneccessary to store it in the memory?)
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
	rawimgs = []							# This is where we will store the unprocessed images
	for i in range(framecount):				# This will loop for each anaglyph photo we want
		print "Starting cycle for photo", i	
		jobs = []								# This is a list where we will store the jobs
		manager = multiprocessing.Manager()		# A Manager() is some sort of magic shared variable for multiprocessing
		images = manager.dict()					# Our two (L+R) images will be a dictionary stuffed into the manger
		GPIO.output(8,True)						# Turn the camera lights on
		for i in range(2):						# Create two jobs, one for each camera 
			p = multiprocessing.Process(target=multigrab, args=(i, images))		# Create the job, send the index i and the shared manager dictionary
			print "Created job for camera", i
			jobs.append(p)						# Append the job to the jobs list
			p.start()							# Start the jobs in the job list
		print "Waiting for the two camera processes to finish."
		p.join()								# Wait for the two camera processes to finish.
		print "The two camera processes has finished."							
		GPIO.output(8,False)					# Turn lights off
		rawimgs.append(images)					# Add recieved channels to array
		
	# Should try cleaning some variables here
	del jobs
	del manager
	del images
	del p
	
	
	imglist = []						# Create a list where we can store our finished photos
	
	
	# Crop and make anaglyph images 
	for i in range(framecount):					# Loop for each frame on the finished photo slip
		threedimage = anaglyph(rawimgs[i], imagewidth, imageheight)	# Send the two photos and the desired dimensions to the anaglyph function
		imglist.append(threedimage)				# Add the created anaglyph image to the image list
		del threedimage							# Clear the variables, hoping to save some RAM
		
			
	# Mask the images
	maskimage = cv2.imread(mask)				# Open the mask file
	if (imglist[0].shape != maskimage.shape):	# Check the dimensions of the mask and compare it to the dimension of the anaglyph images
		print "The mask is the wrong size and will be stretched."
		y, x, d = imglist[0].shape				# Fetch the dimensions from the first anaglyph image
		maskimage = cv2.resize(maskimage,(x,y))	# Rezise the mask (proportions will be skewed if necessary)
	maskimagegray = cv2.cvtColor(maskimage,cv2.COLOR_BGR2GRAY)
	ret, masklayer = cv2.threshold(maskimagegray, 10, 255, cv2.THRESH_BINARY)
	maskimage_fg = cv2.bitwise_and(maskimage,maskimage,mask = masklayer)
	for i in range (framecount):						
		imglist[i] = cv2.add(imglist[i],maskimage_fg)	# Mask each image
	del maskimage		# Remove the mask from memory
	
	# Make the photoslip (this is the only thing that is absolute and not dependent on 'framecount')
	photoslip = np.concatenate((imglist[0], imglist[1], imglist[2], imglist[3], logoimage), axis=0)
	del imglist
	
	timeneed =  int(round(time.time())) - timestart
	print "Total tid: ", timeneed, " s"


	# Save the high resolution photoslip in a temporary file, for the printer
	cv2.imwrite('printfile.jpg', photoslip)
	
	
	# Print the photostrip from the saved file
#	printed = conn.printFile(printer, "printfile.jpg", "Photoslip", {})
#	print "Photostrip sent to", printer_name, "queue as", printed, "."
	
	
	# Scale the photoslip for saving
	y = int(round(paperheight * scalefactor))		# Set x dimenstion for saved photostrip
	x = int(round(paperwidth * scalefactor))		# Set y dimenstion for saved photostrip
	saveimg = cv2.resize(photoslip,(x,y))			# Scale the photostrip
	filename = "photoslips/Photoslip " + str(time.strftime("%H.%M.%S")) + ".jpg"	# Define file name
	print "Saving photoslip as:", filename
	cv2.imwrite(filename, saveimg)		# Save the photostrip
	print "Photoslip saved"
	del photoslip
	del saveimg
	
	# Ready for next photostrip. Heading back to main() to wait for button input
	print "Ready..."

def main():
	try:
		print "Ready..."
		while True:
			if (GPIO.input(3)):
				GPIO.output(10,False)
				photo()
			else:
				GPIO.output(10,True)
	except KeyboardInterrupt:
		GPIO.cleanup()
    
if __name__ == '__main__':
	main()



