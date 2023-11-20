import time
import cv2
import numpy as np

from pyvcam import pvc
from pyvcam.camera import Camera

def main():
    pvc.init_pvcam()
    cam = next(Camera.detect_camera())
    cam.open()
    cam.readout_port = 0

    cam.prog_scan_mode = 1  # Scan mode options: {'Auto': 0, 'Line Delay': 1, 'Scan Width': 2}
    cam.prog_scan_dir = 0  # Scan direction options: {'Down': 0, 'Up': 1, 'Down/Up Alternate': 2}


    def calculate_ASLMparameters(desired_exposuretime):
        """
        calculate the parameters for an ASLM acquisition
        :param desired_exposuretime: the exposure time that is desired for the whole acquisition
        :return: set the important parameters for ASLM acquisitions
        """
        linedelay = 0.00375 #10.16us
        nbrows = 3200
        ASLM_scanWidth=70

        ASLM_lineExposure = int(np.ceil(desired_exposuretime / (1 + nbrows / ASLM_scanWidth)))
        ASLM_line_delay = int(np.ceil((desired_exposuretime - ASLM_lineExposure) / (nbrows * linedelay))) - 1
        ASLM_acquisition_time = (ASLM_line_delay + 1) * nbrows * linedelay + ASLM_lineExposure + (ASLM_line_delay + 1) * linedelay

        print(
            "ASLM parameters are: {} exposure time, and {} line delay factor, {} total acquisition time for {} scan width".format(
                ASLM_lineExposure, ASLM_line_delay, ASLM_acquisition_time, ASLM_scanWidth))
        return ASLM_lineExposure, ASLM_line_delay

    exp, linedelay = calculate_ASLMparameters(200)
    cam.prog_scan_line_delay = linedelay


    cam.start_live(exp_time=exp)
    cnt = 0
    tot = 0
    t1 = time.time()
    start = time.time()
    width = 800
    height = int(cam.sensor_size[1] * width / cam.sensor_size[0])
    dim = (width, height)
    fps = 0

    while True:
        frame, fps, frame_count = cam.poll_frame()
        frame['pixel_data'] = cv2.resize(frame['pixel_data'], dim, interpolation = cv2.INTER_AREA)
        cv2.imshow('Live Mode', frame['pixel_data'])

        low = np.amin(frame['pixel_data'])
        high = np.amax(frame['pixel_data'])
        average = np.average(frame['pixel_data'])

        if cnt == 10:
                t1 = time.time() - t1
                fps = 10/t1
                t1 = time.time()
                cnt = 0
        if cv2.waitKey(10) == 27:
            break
        #print('Min:{}\tMax:{}\tAverage:{:.0f}\tFrame Rate: {:.1f}\n'.format(low, high, average, fps))
        cnt += 1
        tot += 1

    cam.finish()
    cam.close()
    pvc.uninit_pvcam()

    print('Total frames: {}\nAverage fps: {}\n'.format(tot, (tot/(time.time()-start))))
if __name__ == "__main__":
    main()
