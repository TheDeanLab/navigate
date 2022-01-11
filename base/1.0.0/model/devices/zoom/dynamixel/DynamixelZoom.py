"""
Module for controlling Dynamixel discrete zoom changer

Previously initialize as:
def __init__(self, zoomdict, COMport, identifier=2, baudrate=1000000):

Adopted from mesoSPIM

"""
# Standard library imports
import time

# Local Imports
from model.devices.zoom.ZoomBase import ZoomBase
from model.devices.zoom.dynamixel import dynamixel_functions as dynamixel

class Zoom(ZoomBase):
    def __init__(self, model, verbose):
        self.verbose = verbose
        comport = model.ZoomParameters['COMport']
        self.comport = comport
        self.devicename = comport.encode('utf-8')
        self.zoomdict = model.ZoomParameters['zoom_position']
        self.id = 2
        self.dynamixel = dynamixel
        self.baudrate = model.ZoomParameters['baudrate']
        self.addr_mx_torque_enable = 24
        self.addr_mx_goal_position = 30
        self.addr_mx_present_position = 36
        self.addr_mx_p_gain = 28
        self.addr_mx_torque_limit = 34
        self.addr_mx_moving_speed = 32

        ''' Specifies how much the goal position can be off (+/-) from the target '''
        self.goal_position_offset = 10

        ''' Specifies how long to sleep for the wait until done function'''
        self.sleeptime = 0.05
        self.timeout = 15

        # the dynamixel library uses integers instead of booleans for binary information
        self.torque_enable = 1
        self.torque_disable = 0

        self.port_num = dynamixel.portHandler(self.devicename)
        self.dynamixel.packetHandler()

        if self.verbose:
            print('Dynamixel Zoom initialized')

    def set_zoom(self, zoom, wait_until_done=False):
        """
        Changes zoom after checking that the commanded value exists
        """
        if zoom in self.zoomdict:
            self._move(self.zoomdict[zoom], wait_until_done)
            self.zoomvalue = zoom
        else:
            raise ValueError('Zoom designation not in the configuration')
        if self.verbose:
            print('Zoom set to {}'.format(zoom))

    def move(self, position, wait_until_done=False):
        # open port and set baud rate
        self.dynamixel.openPort(self.port_num)
        self.dynamixel.setBaudRate(self.port_num, self.baudrate)

        # Enable servo
        self.dynamixel.write1ByteTxRx(self.port_num, 1, self.id, self.addr_mx_torque_enable, self.torque_enable)

        # Write Moving Speed
        self.dynamixel.write2ByteTxRx(self.port_num, 1, self.id, self.addr_mx_moving_speed, 100)

        # Write Torque Limit
        self.dynamixel.write2ByteTxRx(self.port_num, 1, self.id, self.addr_mx_torque_limit, 200)

        # Write P Gain
        self.dynamixel.write1ByteTxRx(self.port_num, 1, self.id, self.addr_mx_p_gain, 44)

        # Write Goal Position
        self.dynamixel.write2ByteTxRx(self.port_num, 1, self.id, self.addr_mx_goal_position, position)

        # Check position
        ''' 
        This works even though the positions returned during movement are just crap
        - they have 7 to 8 digits. Only when the motor stops, positions are accurate
        '''
        if wait_until_done:
            start_time = time.time()
            upper_limit = position + self.goal_position_offset
            if self.verbose:
                print('Upper Limit: ', upper_limit)
            lower_limit = position - self.goal_position_offset
            if self.verbose:
                print('lower_limit: ', lower_limit)
            cur_position = self.dynamixel.read4ByteTxRx(self.port_num, 1, self.id, self.addr_mx_present_position)

            while (cur_position < lower_limit) or (cur_position > upper_limit):
                # Timeout function
                if time.time()-start_time > self.timeout:
                    break
                time.sleep(0.05)
                cur_position = self.dynamixel.read4ByteTxRx(self.port_num, 1, self.id, self.addr_mx_present_position)
                if self.verbose:
                    print(cur_position)
        self.dynamixel.closePort(self.port_num)
        if self.verbose:
            print('Zoom moved to {}'.format(position))

    def read_position(self):
        '''
        Returns position as an int between 0 and 4096
        Opens & closes the port
        '''
        self.dynamixel.openPort(self.port_num)
        self.dynamixel.setBaudRate(self.port_num, self.baudrate)
        cur_position = self.dynamixel.read4ByteTxRx(self.port_num, 1, self.id, self.addr_mx_present_position)
        self.dynamixel.closePort(self.port_num)
        if self.verbose:
            print('Zoom position: {}'.format(cur_position))
        return cur_position
