# dcam_show_device_list.py : Jun 18, 2021
#
# Copyright (C) 2021 Hamamatsu Photonics K.K.. All right reserved.
#
# This sample source code just shows how to use DCAM-API.
# The performance is not guranteed.

"""
Sample script for showing device list with dcam.py
"""

from dcam import *


def dcam_show_device_list():
    """
    Show device list
    """
    if Dcamapi.init() is not False:
        n = Dcamapi.get_devicecount()
        for i in range(0, n):
            dcam = Dcam(i)
            output = '#{}: '.format(i)

            model = dcam.dev_getstring(DCAM_IDSTR.MODEL)
            if model is False:
                output = output + 'No DCAM_IDSTR.MODEL'
            else:
                output = output + 'MODEL={}'.format(model)

            cameraid = dcam.dev_getstring(DCAM_IDSTR.CAMERAID)
            if cameraid is False:
                output = output + ', No DCAM_IDSTR.CAMERAID'
            else:
                output = output + ', CAMERAID={}'.format(cameraid)

            print(output)
    else:
        print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

    Dcamapi.uninit()


if __name__ == '__main__':
    dcam_show_device_list()
