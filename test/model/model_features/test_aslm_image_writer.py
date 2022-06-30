from aslm.model.model_features.aslm_image_writer import ImageWriter
from aslm.model.dummy_model import get_dummy_model
import numpy as np


class TestImageWriter(unittest.TestCase):
    def test_zarr_byslice(self):


        '''
        This function will create a simulated 3D data set that is in the shape of a capital F. The pixel size can be set to any desired size
        for testing.
        Numpy linspace and meshgrid are used to create the F shape. A boolean constraint is set to create the shape directly.
        The rest of the setup comes from setting the amount of zslices, channels and the duration of the acquisition. 
        A fake frame is list is created that is tied to a fake acquisition list of 'frames' just like the camera would provide.
        The data buffer for the dummy model is set, ImageWriter is instantiated for access to saving functions.
        Then the write_zarr function is called with the list of frame ids.
        The final check is to loop thru each frame and do a check to see if they all equal the original letter F we gave at
        the beginning. 
        A fail message will appear upon failure of test ie one of the frames did not match
        '''
        
        # Test Setup
        dummy_model = get_dummy_model()
        pix_size = 2048
        dummy_model.experiment.CameraParameters['x_pixels'] = pix_size
        dummy_model.experiment.CameraParameters['y_pixels'] = pix_size
        dummy_model.experiment.MicroscopeState['stack_cycling_mode'] = 'per_z'
        x = np.linspace(0,1,pix_size)
        X, Y = np.meshgrid(x,x)
        f_shape = (X < 0.2) | ((Y > 0.4) & (Y < 0.6) & (X < 0.6)) | ((Y < 0.2) & (X < 0.8)) #2D numpy array
        rot_f = np.rot90(f_shape, 1, (1,0))
        inverted_f = np.rot90(f_shape, 2, (1,0))
        num_of_slices = dummy_model.experiment.MicroscopeState['number_z_steps'] = 4 
        # Creating dummy channels
        dummy_model.experiment.MicroscopeState['channels'] = {'channel_2': {'is_selected' : True}, 'channel_3': {'is_selected' : True}, 'channel_4':{'is_selected' : True}}
        num_of_chans = len(dummy_model.experiment.MicroscopeState['channels'].keys()) 
        duration = 3 
        
        acq = []
        frame_ids = []
        total_time = num_of_slices * num_of_chans * duration
        # Create frame id list with the f_shape with amount of frames for acquisition should be 36 based  on above
        for i in range(total_time):
            cycle = i % num_of_chans
            if cycle == 0:
                acq.append(f_shape)
            elif cycle == 1:
                acq.append(rot_f)
            elif cycle == 2:
                acq.append(inverted_f)
            frame_ids.append(i)

        # Set data buffer with fake frame list
        dummy_model.data_buffer = acq 

        slicetest = ImageWriter(dummy_model) # creating class to run func

        # End of Setup

        zarr = slicetest.write_zarr(frame_ids) # Running function to test

        # Checking results of function
        # Loop thru zarr array and check that all frames are still equal to what was put in
        same = True
        for time in range(duration):
            for slice in range(num_of_slices):
                for chans in range(num_of_chans):
                    if chans == 0:
                        shape = f_shape
                    elif chans == 1:
                        shape = rot_f
                    elif chans == 2:
                        shape = inverted_f
                    if np.array_equal(zarr[:, :, slice, chans, time], shape) == False:
                        same = False


        # Test will fail if an image is not the same
        assert same, "Test failed because array was not equal to what was given"


    def test_zarr_bystack(self):

        # Test Setup
        dummy_model = get_dummy_model()
        # Creating 3D simulated data in this case a 3D F shape
        pix_size = 10 #dummy_model.experiment.CameraParameters['x_pixels'] #10 
        dummy_model.experiment.CameraParameters['x_pixels'] = pix_size
        dummy_model.experiment.CameraParameters['y_pixels'] = pix_size
        dummy_model.experiment.MicroscopeState['stack_cycling_mode'] = 'per_stack'
        x = np.linspace(0,1,pix_size)
        X, Y = np.meshgrid(x,x)
        f_shape = (X < 0.2) | ((Y > 0.4) & (Y < 0.6) & (X < 0.6)) | ((Y < 0.2) & (X < 0.8)).astype(int) #2D numpy array
        rot_f = np.rot90(f_shape, 1, (1,0)).astype(int)
        inverted_f = np.rot90(f_shape, 2, (1,0)).astype(int)
        num_of_slices = dummy_model.experiment.MicroscopeState['number_z_steps'] = 4 
        # Creating dummy channels
        dummy_model.experiment.MicroscopeState['channels'] = {'channel_2': {'is_selected' : True}, 'channel_3': {'is_selected' : True}, 'channel_4':{'is_selected' : True}}
        num_of_chans = len(dummy_model.experiment.MicroscopeState['channels'].keys()) 
        duration = 3 
        
        acq = []
        frame_ids = []
        total_time = num_of_slices * num_of_chans * duration
        # Create frame id list with the f_shape with amount of frames for acquisition should be 36 based  on above
        c = 0
        for i in range(total_time):
            s = i % num_of_slices
            if c == 0:
                acq.append(f_shape)
            if c == 1:
                acq.append(rot_f)
            if c == 2:
                acq.append(inverted_f)
            if c == num_of_chans - 1 and s == num_of_slices - 1:
                c = 0
            elif s == num_of_slices - 1:
                c += 1
            
            frame_ids.append(i)

        for frame in range(len(acq)):
            print("Frame ID: ", frame + 1)
            print(acq[frame])
            print()

        # Set data buffer with fake frame list
        dummy_model.data_buffer = acq 

        stacktest = ImageWriter(dummy_model) # creating class to run func

        zarr = stacktest.write_zarr(frame_ids) # Function being tested

        # Checking results of function
        # Loop thru zarr array and check that all frames are still equal to what was put in
        same = True
        for time in range(duration):
            for chans in range(num_of_chans):
                for slice in range(num_of_slices):
                    if chans == 0:
                        shape = f_shape
                    elif chans == 1:
                        shape = rot_f
                    elif chans == 2:
                        shape = inverted_f
                    if np.array_equal(zarr[:, :, slice, chans, time], shape) == False:
                        same = False
                        print("Same? ", same)
                        print("Time, Channel, Slice: ", time, chans, slice)
                        print("Shape expected: \n", shape.astype(int))
                        print("Actual shape: \n", zarr[:, :, slice, chans, time])


        
        print(zarr.info)
        
        # Test will fail if an image is not the same
        assert same, "Test failed because array was not equal to what was given"

if (__name__ == "__main__"):
    unittest.main()
