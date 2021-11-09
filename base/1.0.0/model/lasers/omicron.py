'''
Omicron Laser Classes
Omicron Laser Source uses Coherent OBIS and LUXX Lasers.
OBIS561, 150 mW, is COM22
LUXX488, 200 mW, is COM19
LUXX642, 140 mW, is COM20
'''
#from luxx import Laser as luxx
import pyvisa as visa
from threading import Timer

''' class Luxx_Laser(port):
    #LUXX: https://pypi.org/project/luxx_communication/
    #pip install luxx_communication

    #A programmers guide and command list is available on the USB stick that came with the laser.
    def __init__(self, port):
        self.laser = luxx(port)

    def on(self):
        self.laser.on()

    def off(self):
        self.laser.off()

    def set_power(self, power):
        # power is in mW
        self.laser.set_power(power)

    def set_wavelength(self, wavelength):
        # wavelength is in nm
        self.laser.set_wavelength(wavelength)

    def get_wavelength(self):
        # wavelength is in nm
        return self.laser.get_wavelength()

    def set_mode(self, mode):
        # mode is 'CW' or 'Pulsed'
        self.laser.set_mode(mode)
'''
class Obis_Laser():
    """
    pip install pyvisa.
    VISA is standard for interacting with instruments from a computer.
    VISA uses SCPI commands which is even more common.
    pyVISA essentially  uses SCPI (skippy!) commands (e.g "syst1:diod:hour?")
    """

    def __init__(self, port):
        # self.obis = visa.instrument(com)
        # self.obis.write("*RST")
        # self.obis.write("*CLS")
        # self.obis.write("*IDN?")
        # self.obis.read()
        self.rm = visa.ResourceManager()
        self.obis = self.rm.open_resource(port)
        self.turnoff = False

    def on(self):
        # self.obis.write("sour1:am:stat ON")
        self.change_status(True)
        print("The OBIS Laser is ON")

    def off(self):
        # self.obis.write("sour1:am:stat OFF")
        # self.obis.read()
        # self.obis.close()
        # self.obis.write("*RST")
        # self.obis.write("*CLS")
        # self.obis.write("*IDN?")
        # self.obis.read()
        self.change_status(False)
        self.t.cancel()
        self.turnoff=False
        print("The OBIS Laser is OFF")

    def set_wavelength(self, wavelength):
        self.obis.write("syst1:inf:wav {}".format(wavelength))
        self.obis.read()

    def get_wavelength(self):
        # wavelength is in nm
        self.obis.write("syst1:inf:wav?")
        wavelength=self.obis.read()
        self.obis.write("*CLS")
        self.obis.write("*IDN?")
        self.obis.read()
        return wavelength

    def set_mode(self, mode):
        # mode is 'CW' or 'Pulsed'
        self.obis.write("sour1:pul:mode {}".format(mode))
        self.obis.read()

    def get_mode(self):
        """Only returns two of the possible modes"""
        modes={"CWP":'Constant Power', "CWC":'Constant Current'}
        mode=self.obis.query("sour1:am:sour?",0.1).split('\r')
        self.obis.read()
        return modes[mode[0]]

    def get_status(self):
        status=self.obis.query("sour1:am:stat?",0.1).split('\r')
        self.obis.read()
        return status[0]

    def get_max_power_level(self):
        power=self.obis.query("sour1:pow:nom?",0.1).split('\r')
        self.obis.read()
        print("OBIS Maximum Power: ", power[0])
        return power[0]

    def get_power_level(self):
        power=self.obis.query("sour1:pow:lev:imm:ampl?",0.1).split('\r')
        self.obis.read()
        return power[0]

    def change_status(self, on=False):
        if on:
            command="ON"
        else:
            command = "OFF"
        self.obis.write("sour1:am:stat {}".format(command))
        self.obis.read()

    def set_power_level(self,level):
        """mW input and is converted to watts"""
        level=level/1000 # convert to watts
        max1=self.get_max_power_level()
        #self.obis.read()
        if eval(max1) < level:
            return ("ERROR: Too Power Level Too High!!")
        else:
            power=self.obis.write("sour1:pow:lev:imm:ampl {}".format(level))
            self.obis.read()
            return ("Change Succesful")

    def set_timer(self, minutes=60):
        seconds=minutes*60
        self.t=Timer(seconds, self.change_status)
        self.t.start()

    def gui_set_timer(self,minutes=60):
        seconds=minutes*60
        self.t=Timer(seconds,self.changeflag)
        self.t.start()

    def changeflag(self):
        self.turnoff=True

    def close(self):
        self.obis.close()



if (__name__ == "__main__"):    
    print("Running Testing Section")
    laser=Obis_Laser("COM22")
    laser.on()

    laser.set_mode('CW')
    laser.set_timer(5)
    laser.off()
    laser.close()
    print("OBIS OFF & CLOSED")

    #laser=Luxx_Laser("COM19")
    #laser.on()
    #laser.set_wavelength(1550)
    #laser.set_power(0.1)
    #laser.set_mode('CW')
    #laser.set_timer(5)
    #while not laser.turnoff:
    #    pass
    #laser.off()
