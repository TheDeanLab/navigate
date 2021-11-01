
'''
rotation_stage_cmd.py
========================================
Script containing all functions to initialize and operate the rotation stage SR2812 from Smaract
'''

# Import MCSControl_PythonWrapper.py
from .MCSControl.MCSControl_PythonWrapper import *
import time

# ### implement getchar() function for single character user input
class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()

getch = _GetchWindows()

class SR2812_rotationstage:

    def __init__(self, locator):
        '''
        Initialize rotation stage parameters, and print out some parameters for debugging
        Input: locator address of the rotation stage, e.g. usb:id:3948963323
        Output: an initialized and connected stage.
        '''
        # initialize some variables
        self.sensorEnabled = ct.c_ulong(0)  # initialize sensorEnbaled variable
        self.mcsHandle = ct.c_ulong()  # initialize MCS control handle
        self.numOfChannels = ct.c_ulong(0)
        self.channel = ct.c_ulong(0)
        self.sensorType = ct.c_ulong()
        self.position = ct.c_int()
        self.status = ct.c_ulong()



        # check dll version (not really necessary)
        version = ct.c_ulong()
        SA_GetDLLVersion(version)
        print('DLL-version: {}'.format(version.value))

        # /* Open the first MCS with USB interface in synchronous communication mode */
        self.ExitIfError(SA_OpenSystem(self.mcsHandle, bytes(locator, "utf-8"), bytes('sync,reset', "utf-8")))

        self.ExitIfError( SA_GetSensorEnabled_S(self.mcsHandle,self.sensorEnabled) )


        if (self.sensorEnabled.value == SA_SENSOR_ENABLED):
            print("Sensors are enabled: {}".format(self.sensorEnabled.value))
        else:
            print("Error: sensor not enabled: {}".format(self.sensorEnabled.value))

        self.ExitIfError(SA_GetNumberOfChannels(self.mcsHandle, self.numOfChannels))
        print("Number of Channels: {}".format(self.numOfChannels.value))

        # set channel
        self.channel = ct.c_ulong(int(0))

        #print out sensor type
        self.ExitIfError(SA_GetSensorType_S(self.mcsHandle, self.channel, self.sensorType))
        print("SensorType: {}".format(self.sensorType.value))



    def ExitIfError(self, status):
        '''
        MCS controller error message parser.
        Input: status report of the stage
        Output: print an error message if applicable
        '''
        #init error_msg variable
        error_msg = ct.c_char_p()
        if(status != SA_OK):
            SA_GetStatusInfo(status, error_msg)
            print('MCS error: {}'.format(error_msg.value[:].decode('utf-8')))
        return

    def moveToAngle(self, angle):
        angleposition = ct.c_int(int(angle))
        self.ExitIfError(SA_GotoAngleAbsolute_S(self.mcsHandle, self.channel, angleposition, 0, 1000))

    def getAngle(self):
        revolution = ct.c_ulong()
        position = ct.c_int()
        self.ExitIfError(SA_GetAngle_S(self.mcsHandle, self.channel, position, revolution))
        print("Position: {} ugrad (Press \'s\' to change step size. Press \'q\' to exit.)".format(position.value))

    def ManualMove(self):
        '''
        Use the _GetchWindows class to manually operate the initialized stage from the command line.
        '''
        step_angle = 1000000
        print("\nENTER COMMAND AND RETURN\n" \
              "+  Move positioner up by {}mgrad\n" \
              "-  Move positioner down by {}mgrad\n" \
              "s  Change step size\n" \
              "q  Quit program\n".format(step_angle / 1000, step_angle / 1000))

        # // ----------------------------------------------------------------------------------
        while True:
            key = getch().decode("utf-8")
            if key == 'q':
                break
            if (key == 's'):
                print("Enter step size (ugrad):\n")
                step_angle = int(input())
                print("\nENTER COMMAND AND RETURN\n" \
                      "+  Move positioner up by {}mgrad\n" \
                      "-  Move positioner down by {}mgrad\n" \
                      "s  Change step size\n" \
                      "q  Quit program\n".format(step_angle / 1000, step_angle / 1000))
            if (key == '-'):
                self.ExitIfError(SA_GotoAngleRelative_S(self.mcsHandle, self.channel, -step_angle, 0, 1000))

            if (key == '+'):
                self.ExitIfError(SA_GotoAngleRelative_S(self.mcsHandle, self.channel, step_angle, 0, 1000))

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # // wait until movement has finished
        # // in synchronous communication mode, the current status of each channel
        # // must be checked periodically ('polled') to know when a movement has
         # // finished:
        while True:
            self.ExitIfError(SA_GetStatus_S(self.mcsHandle, self.channel, self.status))
            time.sleep(0.05)
            print(self.status.value)
            if (self.status.value == SA_TARGET_STATUS) or (self.status.value == SA_STOPPED_STATUS):
                break

            # // - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

            revolution = ct.c_ulong()
            self.ExitIfError(SA_GetAngle_S(self.mcsHandle, self.channel, self.position, revolution))
            print("Position: {} ugrad (Press \'s\' to change step size. Press \'q\' to exit.)".format(self.position.value))
                # // - - - - - - - - - - -

    def close(self):
        # /* At the end of the program you should release all opened systems. */
        self.ExitIfError(SA_CloseSystem(self.mcsHandle))
        print('stage closed')

if __name__ == '__main__':
    ##test here code of this class

    stage_id = 'usb:id:3948963323'

    rotationstage = SR2812_rotationstage(stage_id)
    rotationstage.ManualMove()
    rotationstage.close()
