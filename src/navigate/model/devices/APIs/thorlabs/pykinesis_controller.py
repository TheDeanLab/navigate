"""
API for connection to Thorlabs.MotionControl.KCube.StepperMotor.dll.
See Thorlabs.MotionControl.KCube.StepperMotor.h for more functions to implement.
"""

"""
2024/10/23 Sheppard: Initialized to control Kinesis Stepper motor in Linux
"""
from pylablib.devices import Thorlabs
import logging
# Local Imports

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class KinesisStage():
    def __init__(self, dev_path: str, verbose: bool):
        """_summary_

        Args:
            connection (_type_): _description_
        """
        connection = {"port":dev_path,"baudrate":115200,"rtscts":True} 
        self.verbose = verbose
        self.dev_path = dev_path
        self.defualt_axes = ["f"]
        
        self.move_params = {"min_velocity":None,
                            "max_velocity":None,
                            "acceleration":None}
        
        self.open(connection)
        
        
    def __str__(self) -> str:
        """Returns the string representation of the MS2000 Controller class"""
        return "KinesisController"

    def open(self, connection):
        """
        Open the device for communications.

        Parmeters
        ---------
        serial_number : str
            Serial number of Thorlabs Kinesis Stepper Motor (KST) device.

        Returns
        -------
        int
            The error code or 0 if successful.
        """
        try:
            self.stage = Thorlabs.KinesisMotor(("serial", connection), scale="step")
            success = True
        except Exception as e:
            success = False
            raise ConnectionError(f"KST101 stage connection failed! \nError: {e}")
        
    def close(self):
        """
        Disconnect and close the device.

        Parmeters
        ---------
        serial_number : str
            Serial number of Thorlabs Kinesis Stepper Motor (KST) device.

        Returns
        -------
        None
        """
        self.stage.stop()
        self.stage.close()
        
    def move_to_position(self, position, steps_per_um, wait_till_done):
        """Move to position (um)
        """
        self.stage.get_position(channel=1, scale=False)
        cur_pos = self.stage.get_position(channel=1, scale=False)
        position_um = cur_pos / steps_per_um
        # calculate the distance needed to move
        distance = position - position_um
        # convert total distance to steps
        steps = steps_per_um * distance
        # TODO: Does steps need to be an int?
        self.stage.move_by(steps, channel=1, scale=False)
        if wait_till_done:
            self.stage.wait_move(channel=1)
        return 0

    def get_current_position(self, steps_per_um):
        """Get the current position      

        Parmeters
        ---------
        serial_number : str
            Serial number of Thorlabs Kinesis Stepper Motor (KST) device.

        Returns
        -------
        int
            Current position.
        """    
        self.stage.get_position(channel=1, scale=False)
        position = self.stage.get_position(channel=1, scale="False")
        position_um = position / steps_per_um 
        return round(position_um, 2)

    def stop(self):
        """
        Halt motion

        Parmeters
        ---------
        serial_number : str
            Serial number of Thorlabs Kinesis Stepper Motor (KST) device.
        channel : int
            The device channel. One of SCC_Channels.

        Returns
        -------
        int
            The error code or 0 if successful.
        """
        self.stage.stop()
        return 0

    def home_stage(self):
        """Home Device
        """
        self.stage.home()
        return 0

    def set_velocity_params(self,
                            min_velocity, 
                            max_velocity,
                            acceleration,
                            steps_per_um):
        """Set velocity profile required for move
        """        
        min_velocity *= steps_per_um
        max_velocity *= steps_per_um
        acceleration *= steps_per_um
        self.stage.set_move_params(min_velocity, max_velocity, acceleration)
        self.move_params = {"min_velocity":min_velocity,
                            "max_velocity":max_velocity,
                            "acceleration":acceleration}
        return 0