import pytest

@pytest.fixture(scope='package')
def dummy_model():
    from aslm.model.dummy import DummyModel
    
    model = DummyModel()

    return model


@pytest.fixture()
def image_writer(dummy_model):
    from aslm.model.features.image_writer import ImageWriter

    model = dummy_model

    writer = ImageWriter(dummy_model)

    yield writer
    
    writer.close()

def test_generate_metadata(image_writer):
    assert image_writer.generate_meta_data()

def test_image_write(image_writer):
    import os
    from pathlib import Path

    from numpy.random import rand

    # Randomize the data buffer
    for i in range(image_writer.model.data_buffer.shape[0]):
        image_writer.model.data_buffer[i,...] = rand(image_writer.model.img_width, image_writer.model.img_height)

    image_writer.save_image(list(range(image_writer.model.number_of_frames)))

    # TODO: Delete files


@pytest.mark.skip('Modified writer structure')
def test_zarr_byslice():
    """
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
    """
    
    # Test Setup
    dummy_model = DummyModel()

    # Set parameters in dummy_model to be passed to zarr writer
    n_pixels = 2048
    dummy_model.experiment.CameraParameters['x_pixels'] = n_pixels
    dummy_model.experiment.CameraParameters['y_pixels'] = n_pixels
    dummy_model.experiment.MicroscopeState['stack_cycling_mode'] = 'per_z'

    # set number of slices = 4
    num_of_slices = dummy_model.experiment.MicroscopeState['number_z_steps'] = 4 

    # grid [0,1] with n_pixels
    x = np.linspace(0, 1, n_pixels)
    X, Y = np.meshgrid(x, x)
    # construct a F shape on this grid
    f_shape = (X < 0.2) | ((Y > 0.4) & (Y < 0.6) & (X < 0.6)) | ((Y < 0.2) & (X < 0.8)) # 3D numpy array

    rot_f = np.rot90(f_shape, 1, (0,1))        # rotate 90 in the plane (x, y)
    inverted_f = np.rot90(f_shape, 2, (0,1))   # rotate 180 in the plane (x, y)

    # Creating dummy channels
    dummy_model.experiment.MicroscopeState['channels'] = {'channel_2': {'is_selected' : True}, 
                                                          'channel_3': {'is_selected' : True}, 
                                                          'channel_4': {'is_selected' : True}}

    num_of_chans = len(dummy_model.experiment.MicroscopeState['channels'].keys()) # n chans

    duration = 3  # time

    total_time = num_of_slices * num_of_chans * duration
    buffer = np.zeros((total_time, n_pixels, n_pixels))
    
    buffer[::num_of_chans,...] = f_shape[None,...]
    buffer[1::num_of_chans,...] = rot_f[None,...]
    buffer[2::num_of_chans,...] = inverted_f[None,...]
    
    frame_ids = np.arange(total_time)

    # Set data buffer with fake frame list
    dummy_model.data_buffer = buffer

    slicetest = ImageWriter(dummy_model) # creating class to run func

    # End of Setup
    zarr = slicetest.copy_to_zarr(frame_ids) # Running function to test

    # Make sure each channel is identical to its expected shape at every moment in time
    for t in range(duration):
        assert(np.all(zarr[...,0,t] == f_shape[...,None]))
        assert(np.all(zarr[...,1,t] == rot_f[...,None]))
        assert(np.all(zarr[...,2,t] == inverted_f[...,None]))

@pytest.mark.skip(reason='file path not found')
def test_zarr_bystack(self):

    # Test Setup
    dummy_model = DummyModel()
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
