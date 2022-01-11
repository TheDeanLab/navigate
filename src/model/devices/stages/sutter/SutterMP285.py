import serial
import struct
import time
import sys
from numpy import *

# sutterMP285 : A python class for using the Sutter MP-285 positioner
# SUTTERMP285 implements a class for working with a Sutter MP-285
#   micro-positioner. The Sutter must be connected with a Serial
#   cable.

class SutterMP285():
	# Class which allows interaction with the Sutter Manipulator 285
	def __init__(self):
		# time_out in sec
		self.verbose = True
		self.baudrate = 9600
		self.bytesize = serial.EIGHTBITS
		self.parity = serial.PARITY_NONE
		self.stopbits = serial.STOPBITS_ONE
		self.time_out = 30

		# initialize serial connection to controller
		try:
			self.ser = serial.Serial(port='COM1',self.baudrate,self.bytesize,self.parity,self.stopbits,self.time_out)
			self.connected = 1
			if self.verbose:
			  print(self.ser)
		except serial.SerialException:
			print('No connection to Sutter MP-285 could be established!')
			sys.exit(1)

		# set move velocity to 200
		self.set_velocity(200,10)

		# update controller panel
		self.update_panel()

		# get status
		(stepM,currentV,vScaleF)= self.get_status()

		if currentV == 200:
			print('SutterMP285 ready')
		else:
			print('sutterMP285: WARNING Sutter did not respond at startup.')

	# destructor
	def __del__(self):
		self.ser.close()
		if self.verbose :
			print('Connection to Sutter MP-285 closed')

	def get_position(self):
		# send commend to get position
		self.ser.write('c\r')

		# read position from controller
		xyzb = self.ser.read(13)

		# convert bytes into 'signed long' numbers
		xyz_um = array(struct.unpack('lll', xyzb[:12]))/self.step_multiplier

		if self.verbose:
			print('sutterMP285 : Stage position ')
			print('X: %g um \n Y: %g um\n Z: %g um' % (xyz_um[0],xyz_um[1],xyz_um[2]))
		return xyz_um

	def go_to_position(self,pos):
		# Moves the three axes to specified location.
		if len(pos) != 3:
			print('Length of position argument has to be three')
			sys.exit(1)

		# convert integer values into bytes
		xyzb = struct.pack('lll',int(pos[0]*self.step_multiplier),int(pos[1]*self.step_multiplier),int(pos[2]*self.step_multiplier))

		# start timer
		start_t = time.time()

		# send command to move to position
		# add the "m" and the CR to create the move command
		self.ser.write('m'+xyzb+'\r')
		cr = []

		# read carriage return and ignore
		cr = self.ser.read(1)

		# stop timer
		end_t = time.time()

		if len(cr)== 0:
			print('Sutter did not finish moving before time_out (%d sec).' % self.time_out)
		else:
			print('sutterMP285: Sutter move completed in (%.2f sec)' % (end_t-start_t))

	def set_velocity(self,Vel,vScalF=10):
		# this function changes the velocity of the sutter motions
		# Change velocity command 'V'xxCR where xx= unsigned short (16bit) int velocity
		# set by bits 14 to 0, and bit 15 indicates ustep resolution  0=10, 1=50 uSteps/step
		# V is ascii 86

		# convert velocity into unsigned short - 2-byte - integeter
		velb = struct.pack('H',int(Vel))

		# change last bit of 2nd byte to 1 for ustep resolution = 50
		if vScalF == 50:
		velb2 = double(struct.unpack('B',velb[1])) + 128
		velb = velb[0] + struct.pack('B',velb2)
		self.ser.write('V'+velb+'\r')
		self.ser.read(1)

	def update_panel(self):
		# Update Panel - causes the Sutter to display the XYZ info on the front panel

		# Sutter replies with a CR
		self.ser.write('n\r')
		# read and ignore the carriage return
		self.ser.read(1)


	def set_origin(self):
		## Set Origin - sets the origin of the coordinate system to the current position
		self.ser.write('o\r') # Sutter replies with a CR
		self.ser.read(1) # read and ignor the carrage return

	def send_reset(self):
		# Reset controller
		self.ser.write('r\r') # Sutter does not reply

	def get_status(self):
		# Queries the status of the controller.
		if self.verbose:
			print('SutterMP285: get status info')

		# send status command
		self.ser.write('s\r')

		# read return of 32 bytes without carriage return
		rrr = self.ser.read(32)

		# read and ignore the carriage return
		self.ser.read(1)

		status_bytes = struct.unpack(32*'B',rrr)
		if self.verbose:
			print(status_bytes)

		# the value of STEP_MUL ("Multiplier yields msteps/nm") is at bytes 25 & 26
		self.step_multiplier = double(status_bytes[25])*256 + double(status_bytes[24])

		# the value of "XSPEED"  and scale factor is at bytes 29 & 30
		if status_bytes[29] > 127:
			self.voltage_scale_factor = 50
		else:
			self.voltage_scale_factor = 10

		self.current_velocity = double(127 & status_bytes[29])*256+double(status_bytes[28])
		if self.verbose:
			print('step_mul (usteps/um): %g' % self.step_multiplier)
			print('xspeed" [velocity] (usteps/sec): %g' % self.current_velocity)
			print('velocity scale factor (usteps/step): %g' % self.voltage_scale_factor)
		return (self.step_multiplier,self.current_velocity,self.voltage_scale_factor)

if (__name__ == "__main__"):
	# Sutter MP285 Testing Code

	# Initialize the SutterMP285 object
	sutter = SutterMP285()

	# Get the current position
	pos = sutter.get_position()

	# Move to a new position
	posnew = (pos[0]+10.,pos[1]+10.,pos[2]+10.)
	sutter.go_to_position(posnew)

	# Get the current status
	status = sutter.get_status()

	# close the sutter stage
	del sutter
    print('SutterMP285: Done')
