from cmath import pi
from aslm.model.model_features.aslm_image_writer import ImageWriter
from aslm.model.dummy_model import get_dummy_model
import numpy as np


class TestImageWriter:
        

    def test_zarr_byslice(self):
        
        dummy_model = get_dummy_model()
        # Creating 3D simulated data in this case a 3D F shape
        pix_size = 10 # Setting pixel size smaller for test
        dummy_model.experiment.CameraParameters['x_pixels'] = pix_size
        dummy_model.experiment.CameraParameters['y_pixels'] = pix_size
        dummy_model.experiment.MicroscopeState['stack_cycling_mode'] = 'per_z' # setting slice flag
        x = np.linspace(0,1,pix_size)
        X, Y = np.meshgrid(x,x)
        f_shape = (X < 0.2) | ((Y > 0.4) & (Y < 0.6) & (X < 0.6)) | ((Y < 0.2) & (X < 0.8)) #2D numpy array
        # creating slice with each channel
        num_of_slices = dummy_model.experiment.MicroscopeState['number_z_steps'] = 4 # Assuming if multiple slices work that one slice will work
        # Creating dummy channels
        dummy_model.experiment.MicroscopeState['channels'] = {'channel_2': {'is_selected' : True}, 'channel_3': {'is_selected' : True}, 'channel_4':{'is_selected' : True}}
        num_of_chans = len(dummy_model.experiment.MicroscopeState['channels'].keys()) # Assuming that if three channels works that so does one
        duration = 3 # This can be changed, I'm assuming that if zarr copies over 3 timepoints worth of images that one timepoint is covered
        
        acq = []
        frame_ids = []
        total_time = num_of_slices * num_of_chans * duration
        # Create frame id list with the f_shape with amount of frames for acquisition should be 36 based  on above
        for i in range(total_time):
            acq.append(f_shape)
            frame_ids.append(i)

        # Set data buffer with fake frame list
        dummy_model.data_buffer = acq # Now data_buffer[frame_id] will be linked up

        slicetest = ImageWriter(dummy_model) # creating class to run func

        zarr = slicetest.copy_to_zarr(frame_ids) # Running function to test

        # Loop thru zarr array and check that all frames are still equal to what was put in
        same = True
        for time in range(duration):
            for slice in range(num_of_slices):
                for chans in range(num_of_chans):
                    if np.array_equal(zarr[:, :, slice, chans, time], f_shape) == False:
                        same = False


        # Test will fail if an image is not the same
        assert same, "Test failed because array was not equal to what was given"


    def test_zarr_bystack(self):
        
        assert True
