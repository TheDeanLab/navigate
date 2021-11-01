from pyvcam import pvc
from pyvcam.camera import Camera
from matplotlib import pyplot as plt
import time
import cv2
import numpy as np
import auxiliary_code.concurrency_tools as ct
import gc

class Photo_Camera:
    def __init__(self, camera_name):
        pvc.init_pvcam()
        print("pvcam initialized")

        camera_names = Camera.get_available_camera_names()
        print('Available cameras: ' + str(camera_names))

        self.cam = Camera.select_camera(camera_name)
        print('start camera: ' + camera_name)
        print("camera detected")
        self.cam.open()
        print("camera open")

        self.cam.gain = 1

        return None

    def close(self):
        self.cam.close()
        pvc.uninit_pvcam()
        print("camera closed")

    def getinfo(self):
        print(self.cam.trigger_table)

    def getimagesize(self):
        self.cam.roi

    def get_imageroi(self):
        return self.cam.roi

    def set_imageroi(self, startx, endx, starty, endy):
        roi = (startx, endx, starty, endy)
        self.cam.roi = roi

    def take_snapshot(self, exposure):
        frame = self.cam.get_frame(exp_time=exposure).reshape(self.cam.sensor_size[::-1])
        plt.imshow(frame, cmap="gray")
        plt.show()

    def record(self, out, exposure=20):
        import numpy as np
        out[:] = self.cam.get_frame(exp_time=exposure).reshape(self.cam.sensor_size[::-1])

    def prepare_stack_acquisition(self, exposure_time=20):
        """Changes the settings of the low res camera to start stack acquisitions."""
        self.cam.exp_mode = 'Edge Trigger'
        self.cam.exp_out_mode = "Any Row"
        self.cam.speed_table_index = 0

        # Collect frames in live mode
        self.cam.start_live(exp_time=exposure_time)
        print("camera ready")

    def init_camerabuffer(self, nbplanes, width, height):
        self.camerabuffer = np.zeros([nbplanes, width, height], dtype="uint16")

    def init_camerabuffer2(self, buffer):
        self.camerabuffer = buffer

    def get_camerabuffer(self):
        print(self.camerabuffer.shape)
        return self.camerabuffer

    def prepare_stack_acquisition_highres(self, exposure_time=20):
        """Changes the settings of the highres camera to start stack acquisitions."""
        self.cam.exp_mode = 'Edge Trigger'
        self.cam.exp_out_mode = "Any Row"
        self.cam.speed_table_index = 1
        self.cam.readout_port = 0
        self.cam.gain = 1
        self.cam.prog_scan_mode = 0

        # Collect frames in live mode
        self.cam.start_live(exp_time=exposure_time)
        print("camera ready")

    def return_camera_readouttime(self):
        return self.cam.readout_time

    def prepare_ASLM_acquisition(self, exposure_time, scandelay):
        """Changes the settings of the camera to ASLM acquisitions."""
        self.cam.exp_mode = 'Edge Trigger'
        self.cam.speed_table_index = 1 # 1 for 100 MHz
        self.cam.readout_port = 0
        self.cam.gain = 1
        self.cam.prog_scan_mode = 1 # Scan mode options: {'Auto': 0, 'Line Delay': 1, 'Scan Width': 2}
        self.cam.prog_scan_dir = 0 # Scan direction options: {'Down': 0, 'Up': 1, 'Down/Up Alternate': 2}
        self.cam.prog_scan_line_delay = scandelay  # 11.2 us x factor, e.g. a factor = 6 equals 67.2 us

        #The   Line   Output   Mode   is   used   for   synchronization   purposes   when
        # uses   Programmable Scan mode. Line Output Mode creates a rising edge for each
        # row that the rolling shutter read out mechanism of the sensor advances
        self.cam.exp_out_mode = 4

        self.cam.start_live(exp_time=exposure_time)


    def run_stack_acquisition_buffer(self, nb_planes, buffer, maxproj_xy, maxproj_xz, maxproj_yz):
        """Run a stack acquisition."""
        framesReceived = 0
        while framesReceived < nb_planes:
            # time.sleep(0.001)

            try:
                fps, frame_count = self.cam.poll_frame2(out=buffer[framesReceived, :, :])

                def maxprojection_generation(framenb, bufferimage):
                    maxproj_xy[:] = np.maximum(maxproj_xy, bufferimage)
                    maxproj_xz[framenb, :] = np.max(bufferimage, axis=0)
                    maxproj_yz[:, framenb] = np.max(bufferimage, axis=1)
                    print(framenb, flush=True)

                maxprojection_thread = ct.ResultThread(target=maxprojection_generation, args=(framesReceived, buffer[framesReceived, :, :])).start()

                framesReceived += 1
                print("{}:{}".format(framesReceived, fps), flush=True)


            except Exception as e:
                print(str(e))
                break
        self.cam.finish()
        return

    # def run_stack_acquisition_buffer_fast(self, nb_planes, buffer):
    #     """Run a stack acquisition."""
    #     framesReceived = 0
    #     while framesReceived < nb_planes:
    #         # time.sleep(0.001)
    #
    #         try:
    #             #fps, frame_count = self.cam.poll_frame2(out=buffer[framesReceived, :, :])
    #             frame, fps, frame_count = self.cam.poll_frame()
    #
    #             framesReceived += 1
    #             print("{}:{}".format(framesReceived, fps), flush=True)
    #
    #             buffer[framesReceived, :, :] = np.copy(frame['pixel_data'])
    #             frame = None
    #             del frame
    #
    #         except Exception as e:
    #             print(str(e))
    #             break
    #     self.cam.finish()

    def run_stack_acquisition_buffer_fast(self, nb_planes, buffer):
        """Run a stack acquisition."""
        framesReceived = 0
        while framesReceived < nb_planes:
            # time.sleep(0.001)

            try:
                #frame, fps, frame_count = self.cam.poll_frame()
                fps, frame_count = self.cam.poll_frame2(out=buffer[framesReceived, :, :])

                #buffer[framesReceived, :, :] = np.copy(frame['pixel_data'][:])
                #frame['pixel_data'][:] = None
                #frame = None
                #del frame
                #gc.collect()

                #buffer[framesReceived,:,:] = np.zeros([2960, 5056],dtype='uint16')
                framesReceived += 1
                #print("{}:{}".format(framesReceived, fps), flush=True)

            except Exception as e:
                print(str(e))
                break

        self.cam.finish()
        return

    def run_stack_acquisitionV2_preallocated(self, nb_planes):
        """Run a stack acquisition."""
        framesReceived = 0
        while framesReceived < nb_planes:
            # time.sleep(0.001)

            try:
                fps, frame_count = self.cam.poll_frame2(out=self.camerabuffer[framesReceived, :, :])
                framesReceived += 1
                print("{}:{}".format(framesReceived, fps), flush=True)
            except Exception as e:
                print(str(e))
                break
        self.cam.finish()
        return


    # def run_stack_acquisition_buffer_fastOLD(self, nb_planes, buffer):
    #     """Run a stack acquisition."""
    #     framesReceived = 0
    #     while framesReceived < nb_planes:
    #         # time.sleep(0.001)
    #
    #         try:
    #             fps, frame_count = self.cam.poll_frame2(out=buffer[framesReceived, :, :])
    #             # buffer[framesReceived,:,:] = np.zeros([2960, 5056],dtype='uint16')
    #             framesReceived += 1
    #             # print("{}:{}".format(framesReceived, fps), flush=True)
    #
    #         except Exception as e:
    #             print(str(e))
    #             break
    #
    #     self.cam.finish()
    #     return

    def run_stack_acquisition_buffer_pull(self):
        """Run a stack acquisition."""
        try:
            #fps, frame_count = self.cam.poll_frame2(out=buffer)
            frame, fps, frame_count = self.cam.poll_frame()
            return frame['pixel_data'][:]
        except Exception as e:
            print(str(e))
        return


    def set_up_lowres_preview(self, exposure=20):
        self.cam.exp_mode = "Internal Trigger"
        self.cam.exp_out_mode = "Any Row"
        self.cam.speed_table_index = 0
        self.cam.start_live(exp_time=exposure)

    def set_up_highrespreview(self, exposure=20):
        self.cam.exp_mode = "Internal Trigger"
        self.cam.exp_out_mode = "Any Row"
        self.cam.speed_table_index = 1
        self.cam.gain = 1
        self.cam.prog_scan_mode = 0

        self.cam.start_live(exp_time=exposure)

    def run_preview(self, out):
        fps, frame_count = self.cam.poll_frame2(out)

    def run_preview_ASLM(self, out):
        framesReceived = 0
        while framesReceived < 1:
            try:
                fps, frame_count = self.cam.poll_frame2(out)
                framesReceived += 1
                print("{}:{}".format(framesReceived, fps))
            except Exception as e:
                print(str(e))
                break

    def end_stackacquisition(self):
        self.cam.finish()

    def end_preview(self):
        self.cam.finish()


if __name__ == '__main__':
    camera = Photo_Camera('PMUSBCam00')
    # camera = Photo_Camera('PMPCIECam00')

    camera.take_snapshot(20)
    camera.getinfo()
    #camera.preview_live()
    camera.take_snapshot(20)
    camera.close()