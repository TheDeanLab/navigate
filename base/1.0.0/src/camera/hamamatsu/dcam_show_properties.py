# dcam_show_properties.py : Jun 18, 2021
#
# Copyright (C) 2021 Hamamatsu Photonics K.K.. All right reserved.
#
# This sample source code just shows how to use DCAM-API.
# The performance is not guranteed.

"""
Sample script for showing device list with dcam.py
"""

from dcam import *

def dcam_show_properties(iDevice=0):
    """
    Show supported properties
    """
    if Dcamapi.init() is not False:
        dcam = Dcam(iDevice)
        if dcam.dev_open() is not False:
            idprop = dcam.prop_getnextid(0)
            while idprop is not False:
                output = '0x{:08X}: '.format(idprop)

                propname = dcam.prop_getname(idprop)
                if propname is not False:
                    output = output + propname

                print(output)
                idprop = dcam.prop_getnextid(idprop)

            dcam.dev_close()
        else:
            print('-NG: Dcam.dev_open() fails with error {}'.format(dcam.lasterr()))
    else:
        print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

    Dcamapi.uninit()


if __name__ == '__main__':
    dcam_show_properties()
