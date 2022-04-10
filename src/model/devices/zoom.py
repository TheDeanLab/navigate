"""
Parent class for controlling a discrete zoom changer
"""

# Standard Library Imports
import time

# Third Party Imports

# Local Imports
from model.devices.APIs.dynamixel import dynamixel_functions as dynamixel


class ZoomBase:
    def __init__(self, model, verbose):
        self.model = model
        self.verbose = verbose
        self.zoomdict = model.ZoomParameters['zoom_position']
        self.zoomvalue = None

    def set_zoom(self, zoom_position, wait_until_done=False):
        if zoom_position in self.zoomdict:
            if self.verbose:
                print('Setting zoom to {}'.format(zoom_position))
            if wait_until_done:
                time.sleep(1)

    def move(self, position, wait_until_done=False):
        return True

    def read_position(self):
        return True


class SyntheticZoom(ZoomBase):
    """
    Virtual Zoom Device
    """

    def __init__(self, model, verbose):
        super().__init__(model, verbose)
        if self.verbose:
            print('Synthetic Zoom Initialized')

    def set_zoom(self, zoom, wait_until_done=False):
        """
        # Changes zoom after checking that the commanded value exists
        """
        if zoom in self.zoomdict:
            self.zoomvalue = zoom
        else:
            raise ValueError('Zoom designation not in the configuration')
        if self.verbose:
            print('Zoom set to {}'.format(zoom))

    def move(self, position=0, wait_until_done=False):
        if self.verbose:
            print("Changing Virtual Zoom")

    def read_position(self):
        """
        # Returns position as an int between 0 and 4096
        # Opens & closes the port
        """
        if self.verbose:
            print("Reading Virtual Zoom Position")


class DynamixelZoom(ZoomBase):
    def __init__(self, model, verbose):
        super().__init__(model, verbose)
        self.dynamixel = dynamixel
        self.id = model.ZoomParameters['servo_id']
        self.comport = model.ZoomParameters['COMport']
        self.devicename = self.comport.encode('utf-8')
        self.baudrate = model.ZoomParameters['baudrate']
        self.addr_mx_torque_enable = 24
        self.addr_mx_goal_position = 30
        self.addr_mx_present_position = 36
        self.addr_mx_p_gain = 28
        self.addr_mx_torque_limit = 34
        self.addr_mx_moving_speed = 32

        # Specifies how much the goal position can be off (+/-) from the target
        self.goal_position_offset = 10

        # Specifies how long to sleep for the wait until done function

        self.sleeptime = 0.05
        self.timeout = 15

        # the dynamixel library uses integers instead of booleans for binary
        # information
        self.torque_enable = 1
        self.torque_disable = 0

        self.port_num = dynamixel.portHandler(self.devicename)
        self.dynamixel.packetHandler()

        if self.verbose:
            print('Dynamixel Zoom initialized')

    def set_zoom(self, zoom, wait_until_done=False):
        """
        # Changes zoom after checking that the commanded value exists
        """
        if zoom in self.zoomdict:
            self.move(self.zoomdict[zoom], wait_until_done)
            self.zoomvalue = zoom
        else:
            raise ValueError('Zoom designation not in the configuration')
        if self.verbose:
            print('Zoom set to {}'.format(zoom))
            print("Zoom position:", self.read_position())

    def move(self, position, wait_until_done=False):
        """
        # Moves the Dynamixel Zoom Device
        """
        # Open port and set baud rate
        self.dynamixel.openPort(self.port_num)
        self.dynamixel.setBaudRate(self.port_num, self.baudrate)

        # Enable servo
        self.dynamixel.write1ByteTxRx(
            self.port_num,
            1,
            self.id,
            self.addr_mx_torque_enable,
            self.torque_enable)

        # Write Moving Speed
        self.dynamixel.write2ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_moving_speed, 100)

        # Write Torque Limit
        self.dynamixel.write2ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_torque_limit, 200)

        # Write P Gain
        self.dynamixel.write1ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_p_gain, 44)

        # Write Goal Position
        self.dynamixel.write2ByteTxRx(
            self.port_num,
            1,
            self.id,
            self.addr_mx_goal_position,
            position)

        # Check position
        if wait_until_done:
            start_time = time.time()
            upper_limit = position + self.goal_position_offset
            if self.verbose:
                print('Upper Limit: ', upper_limit)
            lower_limit = position - self.goal_position_offset
            if self.verbose:
                print('lower_limit: ', lower_limit)
            cur_position = self.dynamixel.read4ByteTxRx(
                self.port_num, 1, self.id, self.addr_mx_present_position)

            while (cur_position < lower_limit) or (cur_position > upper_limit):
                # Timeout function
                if time.time() - start_time > self.timeout:
                    break
                time.sleep(0.05)
                cur_position = self.dynamixel.read4ByteTxRx(
                    self.port_num, 1, self.id, self.addr_mx_present_position)
                if self.verbose:
                    print(cur_position)
        self.dynamixel.closePort(self.port_num)
        if self.verbose:
            print('Zoom moved to {}'.format(position))

    def read_position(self):
        """
        # Returns position as an int between 0 and 4096
        # Opens & closes the port
        """
        self.dynamixel.openPort(self.port_num)
        self.dynamixel.setBaudRate(self.port_num, self.baudrate)
        cur_position = self.dynamixel.read4ByteTxRx(
            self.port_num, 1, self.id, self.addr_mx_present_position)
        self.dynamixel.closePort(self.port_num)
        if self.verbose:
            print('Zoom position: {}'.format(cur_position))
        return cur_position
