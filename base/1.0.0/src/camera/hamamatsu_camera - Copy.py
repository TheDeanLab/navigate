from hamamatsu.dcam import *
import numpy as np
import cv2


class HamamatsuCamera:
    """ Basic camera interface class.
       This version uses the Hamamatsu library to allocate camera buffers.
       Storage for the data from the camera is allocated dynamically and
       copied out of the camera buffers. """

    def __init__(self, camera_id=None, **kwds):
        """ Open the connection to the camera specified by camera_id. """
        super().__init__(**kwds)

        self.buffer_index = 0
        self.camera_id = camera_id
        print("The Camera ID is :", camera_id)
        self.debug = False
        self.encoding = 'utf-8'
        self.frame_bytes = 0
        self.frame_x = 0
        self.frame_y = 0
        self.last_frame_number = 0
        self.properties = None
        self.max_backlog = 0
        self.number_image_buffers = 0

        self.acquisition_mode = "run_till_abort"
        self.number_frames = 0

        # Get camera model.
        self.camera_model = self.get_model_info(camera_id)

        # Open the camera.
        paramopen = DCAMDEV_OPEN(0, self.camera_id, None)
        paramopen.size = ctypes.sizeof(paramopen)
        self.check_Status(dcam.dcamdev_open(ctypes.byref(paramopen)), "dcamdev_open")
        self.camera_handle = ctypes.c_void_p(paramopen.hdcam)  # TODO this is how to make multiple cameras

        # Set up wait handle
        paramwait = DCAMWAIT_OPEN(0, 0, None, self.camera_handle)
        paramwait.size = ctypes.sizeof(paramwait)
        self.check_Status(dcam.dcamwait_open(ctypes.byref(paramwait)), "dcamwait_open")
        self.wait_handle = ctypes.c_void_p(paramwait.hwait)

        # Get camera properties.
        self.properties = self.get_camera_Properties()

        # Get camera max width, height.
        self.max_width = self.get_property_value("image_width")
        self.max_height = self.get_property_value("image_height")

    def capture_Setup(self):
        """ Capture setup (internal use only). This is called at the start
        of new acquisition sequence to determine the current ROI and
        get the camera configured properly. """
        self.buffer_index = -1
        self.last_frame_number = 0

        # Set sub array mode.
        self.set_sub_array_mode()

        # Get frame properties.
        self.frame_x = self.get_property_value("image_width")[0]
        self.frame_y = self.get_property_value("image_height")[0]
        self.frame_bytes = self.get_property_value("image_framebytes")[0]

    def check_Status(self, fn_return, fn_name="unknown"):
        """ Check return value of the dcam function call.
        Throw an error if not as expected?  """
        # if (fn_return != DCAMERR_NOERROR) and (fn_return != DCAMERR_ERROR):
        #    raise DCAMException("dcam error: " + fn_name + " returned " + str(fn_return))
        if (fn_return == DCAMERR_ERROR):
            c_buf_len = 80
            c_buf = ctypes.create_string_buffer(c_buf_len)
            c_error = dcam.dcam_getlasterror(self.camera_handle,
                                             c_buf,
                                             ctypes.c_int32(c_buf_len))
            raise DCAMException("dcam error " + str(fn_name) + " " + str(c_buf.value))
            # print "dcam error", fn_name, c_buf.value
        return fn_return

    def get_camera_Properties(self):
        """
        Return the ids & names of all the properties that the camera supports. This
        is used at initialization to populate the self.properties attribute.
        """
        c_buf_len = 64
        c_buf = ctypes.create_string_buffer(c_buf_len)
        properties = {}
        prop_id = ctypes.c_int32(0)

        # Reset to the start.
        ret = dcam.dcamprop_getnextid(self.camera_handle,
                                      ctypes.byref(prop_id),
                                      ctypes.c_uint32(DCAMPROP_OPTION_NEAREST))
        if (ret != 0) and (ret != DCAMERR_NOERROR):
            self.check_Status(ret, "dcamprop_getnextid")

        # Get the first property.
        ret = dcam.dcamprop_getnextid(self.camera_handle,
                                      ctypes.byref(prop_id),
                                      ctypes.c_int32(DCAMPROP_OPTION_NEXT))
        if (ret != 0) and (ret != DCAMERR_NOERROR):
            self.check_Status(ret, "dcamprop_getnextid")
        self.check_Status(dcam.dcamprop_getname(self.camera_handle,
                                               prop_id,
                                               c_buf,
                                               ctypes.c_int32(c_buf_len)),
                         "dcamprop_getname")

        # Get the rest of the properties.
        last = -1
        while (prop_id.value != last):
            last = prop_id.value
            properties[convertPropertyName(c_buf.value.decode(self.encoding))] = prop_id.value
            ret = dcam.dcamprop_getnextid(self.camera_handle,
                                          ctypes.byref(prop_id),
                                          ctypes.c_int32(DCAMPROP_OPTION_NEXT))
            if (ret != 0) and (ret != DCAMERR_NOERROR):
                self.check_Status(ret, "dcamprop_getnextid")
            self.check_Status(dcam.dcamprop_getname(self.camera_handle,
                                                   prop_id,
                                                   c_buf,
                                                   ctypes.c_int32(c_buf_len)),
                             "dcamprop_getname")
        return properties

    def get_frames(self):
        """
        Gets all of the available frames.

        This will block waiting for new frames even if
        there new frames available when it is called.
        """
        frames = []
        for n in self.new_frames():
            paramlock = DCAMBUF_FRAME(0, 0, 0, n, None, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            paramlock.size = ctypes.sizeof(paramlock)

            # Lock the frame in the camera buffer & get address.
            self.check_Status(dcam.dcambuf_lockframe(self.camera_handle, ctypes.byref(paramlock)), "dcambuf_lockframe")

            # Create storage for the frame & copy into this storage.
            hc_data = HCamData(self.frame_bytes)
            hc_data.copyData(paramlock.buf)

            frames.append(hc_data)

        return [frames, [self.frame_x, self.frame_y]]

    def get_model_info(self, camera_id):
        """ Returns the model of the camera  """

        c_buf_len = 20
        string_value = ctypes.create_string_buffer(c_buf_len)
        paramstring = DCAMDEV_STRING(
            0,
            DCAM_IDSTR_MODEL,
            ctypes.cast(string_value, ctypes.c_char_p),
            c_buf_len)
        paramstring.size = ctypes.sizeof(paramstring)

        self.check_Status(dcam.dcamdev_getstring(ctypes.c_int32(camera_id),
                                                ctypes.byref(paramstring)),
                         "dcamdev_getstring")

        return string_value.value.decode(self.encoding)

    def get_properties(self):
        """
        Return the list of camera properties. This is the one to call if you
        want to know the camera properties.
        """
        return self.properties

    def get_property_attribute(self, property_name):
        """
        Return the attribute structure of a particular property.

        FIXME (OPTIMIZATION): Keep track of known attributes?
        """
        p_attr = DCAMPROP_ATTR()
        p_attr.cbSize = ctypes.sizeof(p_attr)
        p_attr.iProp = self.properties[property_name]
        ret = self.check_Status(dcam.dcamprop_getattr(self.camera_handle,
                                                     ctypes.byref(p_attr)),
                               "dcamprop_getattr")
        if (ret == 0):
            print("property", property_id, "is not supported")
            return False
        else:
            return p_attr

    def get_property_range(self, property_name):
        """
        Return the range for an attribute.
        """
        prop_attr = self.get_property_attribute(property_name)
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if (temp == DCAMPROP_TYPE_REAL):
            return [float(prop_attr.valuemin), float(prop_attr.valuemax)]
        else:
            return [int(prop_attr.valuemin), int(prop_attr.valuemax)]

    def get_property_read_write(self, property_name):
        """
        Return if a property is readable / writeable.
        """
        prop_attr = self.get_property_attribute(property_name)
        rw = []

        # Check if the property is readable.
        if (prop_attr.attribute & DCAMPROP_ATTR_READABLE):
            rw.append(True)
        else:
            rw.append(False)

        # Check if the property is writeable.
        if (prop_attr.attribute & DCAMPROP_ATTR_WRITABLE):
            rw.append(True)
        else:
            rw.append(False)

        return rw

    def get_property_text(self, property_name):
        """
        #Return the text options of a property (if any).
        """
        prop_attr = self.get_property_attribute(property_name)
        if not (prop_attr.attribute & DCAMPROP_ATTR_HASVALUETEXT):
            return {}
        else:
            # Create property text structure.
            prop_id = self.properties[property_name]
            v = ctypes.c_double(prop_attr.valuemin)

            prop_text = DCAMPROP_VALUETEXT()
            c_buf_len = 64
            c_buf = ctypes.create_string_buffer(c_buf_len)
            # prop_text.text = ctypes.c_char_p(ctypes.addressof(c_buf))
            prop_text.cbSize = ctypes.c_int32(ctypes.sizeof(prop_text))
            prop_text.iProp = ctypes.c_int32(prop_id)
            prop_text.value = v
            prop_text.text = ctypes.addressof(c_buf)
            prop_text.textbytes = c_buf_len

            # Collect text options.
            done = False
            text_options = {}
            while not done:
                # Get text of current value.
                self.check_Status(dcam.dcamprop_getvaluetext(self.camera_handle,
                                                            ctypes.byref(prop_text)),
                                 "dcamprop_getvaluetext")
                text_options[prop_text.text.decode(self.encoding)] = int(v.value)

                # Get next value.
                ret = dcam.dcamprop_queryvalue(self.camera_handle,
                                               ctypes.c_int32(prop_id),
                                               ctypes.byref(v),
                                               ctypes.c_int32(DCAMPROP_OPTION_NEXT))
                prop_text.value = v

                if (ret != 1):
                    done = True

            return text_options

    def get_property_value(self, property_name):
        """
        Return the current setting of a particular property.
        """

        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False
        prop_id = self.properties[property_name]

        # Get the property attributes.
        prop_attr = self.get_property_attribute(property_name)

        # Get the property value.
        c_value = ctypes.c_double(0)
        self.check_Status(dcam.dcamprop_getvalue(self.camera_handle,
                                                ctypes.c_int32(prop_id),
                                                ctypes.byref(c_value)),
                         "dcamprop_getvalue")

        # Convert type based on attribute type.
        temp = prop_attr.attribute & DCAMPROP_TYPE_MASK
        if (temp == DCAMPROP_TYPE_MODE):
            prop_type = "MODE"
            prop_value = int(c_value.value)
        elif (temp == DCAMPROP_TYPE_LONG):
            prop_type = "LONG"
            prop_value = int(c_value.value)
        elif (temp == DCAMPROP_TYPE_REAL):
            prop_type = "REAL"
            prop_value = c_value.value
        else:
            prop_type = "NONE"
            prop_value = False

        return [prop_value, prop_type]

    def is_camera_property(self, property_name):
        """
        Check if a property name is supported by the camera.
        """
        if (property_name in self.properties):
            return True
        else:
            return False

    def new_frames(self):
        """
        Return a list of the ids of all the new frames since the last check.
        Returns an empty list if the camera has already stopped and no frames
        are available.

        This will block waiting for at least one new frame.
        """
        # Wait for a new frame.
        # paramstart = DCAMWAIT_START(
        #         0, 0, DCAMCAP_EVENT_FRAMEREADY, DCAMWAIT_TIMEOUT_INFINITE)
        paramstart = DCAMWAIT_START(0, 0, DCAMCAP_EVENT_FRAMEREADY, 1000)

        paramstart.size = ctypes.sizeof(paramstart)

        self.check_Status(dcam.dcamwait_start(self.wait_handle, ctypes.byref(paramstart)),
                         "dcamwait_start")

        # Check how many new frames there are.
        paramtransfer = DCAMCAP_TRANSFERINFO(0, DCAMCAP_TRANSFERKIND_FRAME, 0, 0)
        paramtransfer.size = ctypes.sizeof(paramtransfer)
        self.check_Status(dcam.dcamcap_transferinfo(self.camera_handle, ctypes.byref(paramtransfer)),
                         "dcamcap_transferinfo")
        cur_buffer_index = paramtransfer.nNewestFrameIndex
        cur_frame_number = paramtransfer.nFrameCount

        # Check that we have not acquired more frames than we can store in our buffer.
        # Keep track of the maximum backlog.
        backlog = cur_frame_number - self.last_frame_number
        if (backlog > self.number_image_buffers):
            print(">> Warning! hamamatsu camera frame buffer overrun detected!")
        if (backlog > self.max_backlog):
            self.max_backlog = backlog
        self.last_frame_number = cur_frame_number

        # Create a list of the new frames.
        new_frames = []
        if (cur_buffer_index < self.buffer_index):
            for i in range(self.buffer_index + 1, self.number_image_buffers):
                new_frames.append(i)
            for i in range(cur_buffer_index + 1):
                new_frames.append(i)
        else:
            for i in range(self.buffer_index, cur_buffer_index):
                new_frames.append(i + 1)
        self.buffer_index = cur_buffer_index

        if self.debug:
            print(new_frames)

        return new_frames

    def set_property_value(self, property_name, property_value):
        """
        Set the value of a property.
        """

        # Check if the property exists.
        if not (property_name in self.properties):
            print(" unknown property name:", property_name)
            return False

        # If the value is text, figure out what the
        # corresponding numerical property value is.
        if (isinstance(property_value, str)):
            text_values = self.get_property_text(property_name)
            if (property_value in text_values):
                property_value = float(text_values[property_value])
            else:
                print(" unknown property text value:", property_value, "for", property_name)
                return False

        # Check that the property is within range.
        [pv_min, pv_max] = self.get_property_range(property_name)
        if (property_value < pv_min):
            print(" set property value", property_value, "is less than minimum of", pv_min, property_name,
                  "setting to minimum")
            property_value = pv_min
        if (property_value > pv_max):
            print(" set property value", property_value, "is greater than maximum of", pv_max, property_name,
                  "setting to maximum")
            property_value = pv_max

        # Set the property value, return what it was set too.
        prop_id = self.properties[property_name]
        p_value = ctypes.c_double(property_value)
        self.check_Status(dcam.dcamprop_setgetvalue(self.camera_handle,
                                                   ctypes.c_int32(prop_id),
                                                   ctypes.byref(p_value),
                                                   ctypes.c_int32(DCAM_DEFAULT_ARG)),
                         "dcamprop_setgetvalue")
        return p_value.value

    def set_sub_array_mode(self):
        """
        This sets the sub-array mode as appropriate based on the current ROI.
        """

        # Check ROI properties.
        roi_w = self.get_property_value("subarray_hsize")[0]
        roi_h = self.get_property_value("subarray_vsize")[0]

        # If the ROI is smaller than the entire frame turn on subarray mode
        if ((roi_w == self.max_width) and (roi_h == self.max_height)):
            self.set_property_value("subarray_mode", "OFF")
        else:
            self.set_property_value("subarray_mode", "ON")

    def set_acquisition_mode(self, mode, number_frames=None):
        '''  Set the acquisition mode to either run until aborted or to
        stop after acquiring a set number of frames.
        mode should be either "fixed_length" or "run_till_abort"
        if mode is "fixed_length", then number_frames indicates the number
        of frames to acquire.'''

        self.stop_acquisition()

        if self.acquisition_mode is "fixed_length" or \
                self.acquisition_mode is "run_till_abort":
            self.acquisition_mode = mode
            self.number_frames = number_frames
        else:
            raise DCAMException("Unrecognized acqusition mode: " + mode)

    def start_acquisition(self):
        """ Start data acquisition. """
        self.capture_Setup()

        #
        # Allocate Hamamatsu image buffers.
        # We allocate enough to buffer 2 seconds of data or the specified
        # number of frames for a fixed length acquisition
        #
        if self.acquisition_mode is "run_till_abort":
            n_buffers = int(2.0 * self.get_property_value("internal_frame_rate")[0])
        elif self.acquisition_mode is "fixed_length":
            n_buffers = self.number_frames

        self.number_image_buffers = n_buffers
        self.check_Status(dcam.dcambuf_alloc(self.camera_handle, ctypes.c_int32(self.number_image_buffers)), "dcambuf_alloc")

        # Start acquisition.
        if self.acquisition_mode is "run_till_abort":
            self.check_Status(dcam.dcamcap_start(self.camera_handle, DCAMCAP_START_SEQUENCE), "dcamcap_start")
        if self.acquisition_mode is "fixed_length":
            self.check_Status(dcam.dcamcap_start(self.camera_handle, DCAMCAP_START_SNAP), "dcamcap_start")

    def stop_acquisition(self):
        """ Stop data acquisition. """
        self.check_Status(dcam.dcamcap_stop(self.camera_handle), "dcamcap_stop")
        print("max camera backlog was", self.max_backlog, "of", self.number_image_buffers)
        self.max_backlog = 0

        # Free image buffers.
        self.number_image_buffers = 0
        self.check_Status(dcam.dcambuf_release(self.camera_handle, DCAMBUF_ATTACHKIND_FRAME),
                         "dcambuf_release")

    def shutdown(self):
        """ Close down the connection to the camera. """
        self.check_Status(dcam.dcamwait_close(self.wait_handle), "dcamwait_close")
        self.check_Status(dcam.dcamdev_close(self.camera_handle), "dcamdev_close")

    def sorted_property_text_options(self, property_name):
        """ Returns the property text options a list sorted by value. """
        text_values = self.get_property_text(property_name)
        return sorted(text_values, key=text_values.get)


class HamamatsuCameraMR(HamamatsuCamera):
    """
    Memory recycling camera class.
    This version allocates "user memory" for the Hamamatsu camera
    buffers. This memory is also the location of the storage for
    the np_array element of a HCamData() class. The memory is
    allocated once at the beginning, then recycled. This means
    that there is a lot less memory allocation & shuffling compared
    to the basic class, which performs one allocation and (I believe)
    two copies for each frame that is acquired.

    WARNING: There is the potential here for chaos. Since the memory
             is now shared there is the possibility that downstream code
             will try and access the same bit of memory at the same time
             as the camera and this could end badly.
    FIXME: Use lockbits (and unlockbits) to avoid memory clashes?
           This would probably also involve some kind of reference
           counting scheme.
    """

    def __init__(self, **kwds):
        super().__init__(**kwds)

        self.hcam_data = []
        self.hcam_ptr = False
        self.old_frame_bytes = -1

        self.set_property_value("output_trigger_kind[0]", 2)

    def get_frames(self):
        """
        Gets all of the available frames.

        This will block waiting for new frames even if there new frames
        available when it is called.

        FIXME: It does not always seem to block? The length of frames can
               be zero. Are frames getting dropped? Some sort of race condition?
        """
        frames = []
        for n in self.new_frames():
            frames.append(self.hcam_data[n])

        return [frames, [self.frame_x, self.frame_y]]

    def start_acquisition(self):
        """
        Allocate as many frames as will fit in 2GB of memory and start data acquisition.
        """
        self.capture_Setup()

        # Allocate new image buffers if necessary. This will allocate
        # as many frames as can fit in 2GB of memory, or 2000 frames,
        # which ever is smaller. The problem is that if the frame size
        # is small than a lot of buffers can fit in 2GB. Assuming that
        # the camera maximum speed is something like 1KHz 2000 frames
        # should be enough for 2 seconds of storage, which will hopefully
        # be long enough.
        #
        if (self.old_frame_bytes != self.frame_bytes) or \
                (self.acquisition_mode is "fixed_length"):

            n_buffers = min(int((2.0 * 1024 * 1024 * 1024) / self.frame_bytes), 2000)
            if self.acquisition_mode is "fixed_length":
                self.number_image_buffers = self.number_frames
            else:
                self.number_image_buffers = n_buffers

            # Allocate new image buffers.
            ptr_array = ctypes.c_void_p * self.number_image_buffers
            self.hcam_ptr = ptr_array()
            self.hcam_data = []
            for i in range(self.number_image_buffers):
                hc_data = HCamData(self.frame_bytes)
                self.hcam_ptr[i] = hc_data.getDataPtr()
                self.hcam_data.append(hc_data)

            self.old_frame_bytes = self.frame_bytes

        # Attach image buffers and start acquisition.
        #
        # We need to attach & release for each acquisition otherwise
        # we'll get an error if we try to change the ROI in any way
        # between acquisitions.

        paramattach = DCAMBUF_ATTACH(0, DCAMBUF_ATTACHKIND_FRAME,
                                     self.hcam_ptr, self.number_image_buffers)
        paramattach.size = ctypes.sizeof(paramattach)

        if self.acquisition_mode is "run_till_abort":
            self.check_Status(dcam.dcambuf_attach(self.camera_handle,
                                                 paramattach),
                             "dcam_attachbuffer")
            self.check_Status(dcam.dcamcap_start(self.camera_handle,
                                                DCAMCAP_START_SEQUENCE),
                             "dcamcap_start")
        if self.acquisition_mode is "fixed_length":
            paramattach.buffercount = self.number_frames
            self.check_Status(dcam.dcambuf_attach(self.camera_handle,
                                                 paramattach),
                             "dcambuf_attach")
            self.check_Status(dcam.dcamcap_start(self.camera_handle,
                                                DCAMCAP_START_SNAP),
                             "dcamcap_start")

    def stop_acquisition(self):
        """
        Stop data acquisition and release the memory associates with the frames.
        """

        # Stop acquisition.
        self.check_Status(dcam.dcamcap_stop(self.camera_handle),
                         "dcamcap_stop")

        # Release image buffers.
        if (self.hcam_ptr):
            self.check_Status(dcam.dcambuf_release(self.camera_handle,
                                                  DCAMBUF_ATTACHKIND_FRAME),
                             "dcambuf_release")

        ''' Print backlog only when it is large '''
        if self.max_backlog > 1:
            print("max camera backlog was:", self.max_backlog)
        self.max_backlog = 0

    # Testing.


if (__name__ == "__main__"):
    ''' import time
    import random

    print("found:", n_cameras, "cameras")
    if (n_cameras > 0):

        hcam = HamamatsuCameraMR(camera_id=1)
        print(hcam.set_property_value("defect_correct_mode", 1))
        print("camera 0 model:", hcam.get_model_info(0))

        # List support properties.
        if True:
            print("Supported properties:")
            props = hcam.get_properties()
            for i, id_name in enumerate(sorted(props.keys())):
                [p_value, p_type] = hcam.get_property_value(id_name)
                p_rw = hcam.get_property_read_write(id_name)
                read_write = ""
                if (p_rw[0]):
                    read_write += "read"
                if (p_rw[1]):
                    read_write += ", write"
                print("  ", i, ")", id_name, " = ", p_value, " type is:", p_type, ",", read_write)
                text_values = hcam.get_property_text(id_name)
                if (len(text_values) > 0):
                    print("          option / value")
                    for key in sorted(text_values, key=text_values.get):
                        print("         ", key, "/", text_values[key])

        # Test setting & getting some parameters.
        if False:
            print(hcam.set_property_value("exposure_time", 0.001))
            print(hcam.set_property_value("subarray_hpos", 512))
            print(hcam.set_property_value("subarray_vpos", 512))
            print(hcam.set_property_value("subarray_hsize", 1024))
            print(hcam.set_property_value("subarray_vsize", 1024))
            print(hcam.set_property_value("binning", "1x1"))
            print(hcam.set_property_value("readout_speed", 2))

            hcam.set_sub_array_mode()
            # hcam.start_acquisition()
            # hcam.stop_acquisition()

            params = ["internal_frame_rate",
                      "timing_readout_time",
                      "exposure_time"]

            #                      "image_height",
            #                      "image_width",
            #                      "image_framebytes",
            #                      "buffer_framebytes",
            #                      "buffer_rowbytes",
            #                      "buffer_top_offset_bytes",
            #                      "subarray_hsize",
            #                      "subarray_vsize",
            #                      "binning"]
            for param in params:
                print(param, hcam.get_property_value(param)[0])

        # Test 'run_till_abort' acquisition.
        if False:
            print("Testing run till abort acquisition")
            hcam.start_acquisition()
            cnt = 0
            for i in range(300):
                [frames, dims] = hcam.get_frames()
                for aframe in frames:
                    print(cnt, aframe[0:5])
                    cnt += 1

            print("Frames acquired: " + str(cnt))
            hcam.stop_acquisition()

        # Test 'fixed_length' acquisition.
        if False:
            for j in range(10):
                print("Testing fixed length acquisition")
                hcam.set_acquisition_mode("fixed_length", number_frames=10)
                hcam.start_acquisition()
                cnt = 0
                iterations = 0
                while cnt < 11 and iterations < 20:
                    [frames, dims] = hcam.get_frames()
                    waitTime = random.random() * 0.03
                    time.sleep(waitTime)
                    iterations += 1
                    print('Frames loaded: ' + str(len(frames)))
                    print('Wait time: ' + str(waitTime))
                    for aframe in frames:
                        print(cnt, aframe[0:5])
                        cnt += 1
                if cnt < 10:
                    print('##############Error: Not all frames found#########')
                    input("Press enter to continue")
                print("Frames acquired: " + str(cnt))
                hcam.stop_acquisition()

                hcam.set_acquisition_mode("run_till_abort")
                hcam.start_acquisition()
                time.sleep(random.random())
                contFrames = hcam.get_frames()
                hcam.stop_acquisition()


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

    def dcamtest_show_framedata(data, windowtitle, iShown):
        """
        Show numpy buffer as an image

        Arg1:   NumPy array
        Arg2:   Window name
        Arg3:   Last window status.
            0   open as a new window
            <0  already closed
            >0  already openend
        """
        if iShown > 0 and cv2.getWindowProperty(windowtitle, 0) < 0:
            return -1  # Window has been closed.
        if iShown < 0:
            return -1  # Window is already closed.

        if data.dtype == np.uint16:
            imax = np.amax(data)
            if imax > 0:
                imul = int(65535 / imax)
                # print('Multiple %s' % imul)
                data = data * imul

            cv2.imshow(windowtitle, data)
            return 1
        else:
            print('-NG: dcamtest_show_image(data) only support Numpy.uint16 data')
            return -1

    def dcamtest_thread_live(dcam):
        """
        Show live image

        Arg1:   Dcam instance
        """
        if dcam.cap_start() is not False:

            timeout_milisec = 100
            iWindowStatus = 0
            while iWindowStatus >= 0:
                if dcam.wait_capevent_frameready(timeout_milisec) is not False:
                    data = dcam.buf_getlastframedata()
                    iWindowStatus = dcamtest_show_framedata(data, 'test', iWindowStatus)
                else:
                    dcamerr = dcam.lasterr()
                    if dcamerr.is_timeout():
                        print('===: timeout')
                    else:
                        print('-NG: Dcam.wait_event() fails with error {}'.format(dcamerr))
                        break

                key = cv2.waitKey(1)
                if key == ord('q') or key == ord('Q'):  # if 'q' was pressed with the live window, close it
                    break

            dcam.cap_stop()
        else:
            print('-NG: Dcam.cap_start() fails with error {}'.format(dcam.lasterr()))

    def dcam_live_capturing(iDevice=0):
        """
        Capture and show a image
        """
        if Dcamapi.init() is not False:
            dcam = Dcam(iDevice)
            if dcam.dev_open() is not False:
                if dcam.buf_alloc(3) is not False:
                    # th = threading.Thread(target=dcamtest_thread_live, args=(dcam,))
                    # th.start()
                    # th.join()
                    dcamtest_thread_live(dcam)

                    # release buffer
                    dcam.buf_release()
                else:
                    print('-NG: Dcam.buf_alloc(3) fails with error {}'.format(dcam.lasterr()))
                dcam.dev_close()
            else:
                print('-NG: Dcam.dev_open() fails with error {}'.format(dcam.lasterr()))
        else:
            print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))

        Dcamapi.uninit()
    ''' 
    HamamatsuCamera.dcam_show_device_list()
    # HamamatsuCamera.dcam_show_properties()
