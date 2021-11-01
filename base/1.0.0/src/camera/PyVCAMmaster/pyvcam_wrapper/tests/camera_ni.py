import ctypes as C
import numpy as np
import matplotlib.pyplot as plt

"""
TODO: One way or another, make it harder to forget the daq.close()
method, which can cause crazy voltages to persist. _del_? _enter_ and
_exit_? Try to do it better than we are.
Requires nicaiu.dll to be in the same directory, or located in the
os.environ['PATH'] search path.
If you get an error, google for NIDAQmx.h to decypher it.
"""
api = C.cdll.LoadLibrary("nicaiu")


#todo- rewrite this so that you can specify in constants
#digital/analog, channel number, minVol, maxVol, name of channel, constant voltage or play

#todo - include a tool to make a single voltage output and not only the play voltage functionality

class Analog_Out:
    def __init__(
        self,
        num_channels='all',
        rate=1e4,
        verbose=True,
        daq_type='6733',
        line='Dev1/ao0',
        clock_name=None,
        minVol=0,
        maxVol=10,
        ):
        """Play analog voltages via a National Instruments analog-out DAQ board.
        """

        self.daq_type = daq_type

        if self.daq_type == '6738':
            self.max_channels = 32
            self.max_rate = 1e6 #This is for 8 channels, otherwise 350 kS/s
            self.channel_type = 'analog'
            self.has_clock = True
        elif self.daq_type == '6738_digital':
            # WARNING: See note about 6733_digital lines. Also note that there
            # are 8 digital lines on `port1`, but these are not "buffered". We
            # have not yet included any functionality for these lines.
            self.max_channels = 2
            self.max_rate = 10e6 #TODO is this the correct max rate?
            self.channel_type = 'digital'
            self.has_clock = False
        elif self.daq_type == '6738_constant':
            self.max_channels = 32
            self.max_rate = 1e6  # This is for 8 channels, otherwise 350 kS/s
            self.channel_type = 'constant'
            self.has_clock = True

        if num_channels == 'all':
            num_channels = self.max_channels
        assert 1 <= num_channels <= self.max_channels
        self.num_channels = num_channels
        if clock_name is not None:
            assert isinstance(clock_name, str)
            clock_name = bytes(clock_name, 'ascii')
        self.verbose = verbose

        if self.verbose: print("Opening %s-out board..."%self.channel_type)
        self.task_handle = C.c_void_p(0)
        api.create_task(bytes(), self.task_handle)
        # If I were a real man, I would automatically detect the proper
        # board name somehow
    # (http://digital.ni.com/public.nsf/allkb/86256F0E001DA9FF492572A5006FD7D3)
    # instead of demanding user input via the 'init' argument. If
        # this next api call crashes for you, check the name of your
        # analog-out card using NI Measurement and Automation Explorer
        # (NI MAX):

        if self.channel_type == 'analog':
            device_name2 = bytes(line, 'ascii')
            api.create_ao_voltage_channel(
                self.task_handle,
                device_name2,
                b"",
                -10, #Minimum voltage
                +10.0, #Maximum voltage
                10348, #DAQmx_Val_Volts; don't question it!
                None) #NULL
        elif self.channel_type == 'digital':
            device_name2 = bytes(line, 'ascii')
            api.create_do_channel(
                self.task_handle,
                device_name2,
                b"",
                1) #DAQmx_Val_ChanForAllLines; don't question it!
        elif self.channel_type == 'constant':
            device_name2 = bytes(line, 'ascii')
            api.create_ao_voltage_channel(
                self.task_handle,
                device_name2,
                b"",
                minVol,  # Minimum voltage
                maxVol,  # Maximum voltage
                10348,  # DAQmx_Val_Volts; don't question it!
                None)  # NULL
            return None

        if self.verbose: print(" Board open.")
        dtype = {'digital': np.uint8, 'analog': np.float64}[self.channel_type]
        self.voltages = np.zeros((2, self.num_channels), dtype=dtype)
        # Play initial voltages with the internal clock
        if self.has_clock:
            self.clock_name = None
        else:
            self.clock_name = clock_name
        self.set_rate(rate)
        self._write_voltages(self.voltages)
        if self.has_clock:
            self.play_voltages(force_final_zeros=False, block=True)
        else:
            self.play_voltages(force_final_zeros=False, block=False)
        if clock_name is not None and self.has_clock: # Switch to external clock
            self.clock_name = clock_name
            self.set_rate(rate)
        return None

    def set_rate(self, rate):
        self._ensure_task_is_stopped()
        assert 0 < rate <= self.max_rate
        self.rate = float(rate)
        api.clock_timing(
            self.task_handle,
            self.clock_name, #NULL, to specify onboard clock for timing
            self.rate,
            10280, #DAQmx_Val_Rising (doesn't matter)
            10178, #DAQmx_Val_FiniteSamps (run once / Acquire or generate a finite number of samples.)
            self.voltages.shape[0])
        return None

    def play_voltages(
        self,
        voltages=None,
        force_final_zeros=True,
        block=True,
        ):
        """
        If voltage is None, play the previously set voltage.
        If 'force_final_zeros', the last entry of each channel of
        'voltages' is set to zero.
        If 'block', this function will not return until the voltages are
        finished playing. Not performant, but easier to reason about.
        NB: by default, play_voltages() blocks until the voltages finish
        playing. This makes it harder to accidentally code yourself into
        ugly race conditions, but it obviously makes it hard to do
        anything else while the board is playing voltages. Since
        we're just issuing a DLL call, it's easy for play_voltages() to
        return as soon as the voltage task has started playing. This is
        probably what you want! But easier to write bugs with.
        Regardless, if a previous voltage task is still playing, we have
        to wait for it to finish before we can start the next one.
        """
        self._ensure_task_is_stopped()
        if voltages is not None:
            self._write_voltages(voltages, force_final_zeros)
        if self.verbose: print("Playing voltages...")
        api.start_task(self.task_handle)
        self._task_running = True
        if block:
            self._ensure_task_is_stopped()
        return None

    def close(self):
        if self.daq_type == '6738_constant':
            if self.verbose: print("Setting voltages to zero")
            api.write_scalarvoltages(self.task_handle, 1, 10, 0, None)
            api.clear_task(self.task_handle)
            return None
        else:
            self._ensure_task_is_stopped()
            if self.verbose: print("Closing %s board..."%self.daq_type)
            api.clear_task(self.task_handle)
            if self.verbose: print(" %s board is closed."%self.daq_type)
            return None

    def setconstantvoltage(self, voltage):
        # Writes a floating-point sample to a task that contains a single analog output channel.
        api.write_scalarvoltages(self.task_handle, 1, 10, voltage, None)

    def s2p(self, seconds):
        '''Convert a duration in seconds to a number of AO "pixels."
        Frequently I know how many seconds I want to play a voltage for,
        and I do simple math to convert this to how many "pixels" of
        voltage I should use on the analog out card to get this many
        seconds. Frequently I get this math wrong. That's why I wrote
        this function.
        '''
        num_pixels = int(round(self.rate * seconds))
        return num_pixels

    def p2s(self, num_pixels):
        '''Convert a  number of AO "pixels to a duration in seconds."
        Frequently I know how many "pixels" of voltage I'm playing on
        the analog out card, and I do simple math to convert this to how
        many seconds I'm playing that voltage for. Frequently I get this
        math wrong. That's why I wrote this function.
        '''
        seconds = num_pixels / self.rate
        return seconds

    def s2s(self, seconds):
        '''Calculate nearest duration the AO card can exactly deliver.
        This function rounds a time (in seconds) to the nearest time
        that the AO card can exactly deliver via an integer number of
        "pixels". For example, maybe you'd like to play a 10 millisecond
        pulse of voltage, but the AO rate is set to 300; how many
        "pixels" should we expect the AO card play for?
        '''
        seconds = self.p2s(self.s2p(seconds))
        return seconds

    def _ensure_task_is_stopped(self):
        if not hasattr(self, '_task_running'):
            self._task_running = False
        if self._task_running:
            if self.verbose: print("Waiting for board to finish playing...")
            api.finish_task(self.task_handle, -1) #A value of -1 (DAQmx_Val_WaitInfinitely) means to wait indefinitely.
            if self.verbose: print(" NI%s is finished playing."%self.daq_type)
            api.stop_task(self.task_handle)
            self._task_running = False
        return None

    def _write_voltages(self, voltages, force_final_zeros=True):
        assert len(voltages.shape) == 2
        assert voltages.dtype == self.voltages.dtype
        assert voltages.shape[0] >= 2
        assert voltages.shape[1] == self.num_channels
        if force_final_zeros:
            if self.verbose:
                print("***Coercing voltages to end in zero!***")
            voltages[-1, :] = 0
        old_voltages_shape = self.voltages.shape
        self.voltages = voltages
        if self.voltages.shape[0] != old_voltages_shape[0]:
            self.set_rate(self.rate)
        if not hasattr(self, 'num_points_written'):
            self.num_points_written = C.c_int32(0)
        write = {'analog': api.write_voltages,
                 'digital': api.write_digits}[self.channel_type]
        self._ensure_task_is_stopped()
        write(
            self.task_handle,
            self.voltages.shape[0], #Samples per channel
            0, #Set autostart to False
            10.0, #Timeout for writing, in seconds. We could be smarter...
            1, #DAQmx_Val_GroupByScanNumber (interleaved)
            self.voltages,
            self.num_points_written,
            None)
        if self.verbose:
            print(self.num_points_written.value,
                  "points written to each %s channel."%self.daq_type)
        return None

    def plot_voltages(self, volts, names):
        # Reverse lookup table; channel numbers to names:
        for c in range(volts.shape[1]):
            plt.plot(volts[:, c], label=names[c])
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        xlocs, xlabels = plt.xticks()
        plt.xticks(xlocs, [self.p2s(l) for l in xlocs])
        plt.ylabel('Volts')
        plt.xlabel('Seconds')
        plt.tight_layout()
        plt.show()

# DLL api management----------------------------------------------------------------------------------------------------

#int32 DAQmxGetExtendedErrorInfo (char errorString[], uInt32 bufferSize);
#Returns dynamic, specific error information. This function is valid only for the last function that failed;
# additional NI-DAQmx calls may invalidate this information.
api.get_error_info = api.DAQmxGetExtendedErrorInfo
api.get_error_info.argtypes = [C.c_char_p, C.c_uint32]

def check_error(error_code):
    if error_code != 0:
        num_bytes = api.get_error_info(None, 0) #if passed in 0 in buffersize, the value returned is the number of bytes
        print("Error message from NI DAQ: (", num_bytes, "bytes )")
        error_buffer = (C.c_char * num_bytes)()
        api.get_error_info(error_buffer, num_bytes)
        print(error_buffer.value.decode('ascii'))
        raise UserWarning(
            "NI DAQ error code: %i; see above for details."%(error_code))
    return error_code

#int32 DAQmxCreateTask (const char taskName[], TaskHandle *taskHandle);
#Creates a task . If you use this function to create a task, you must use DAQmxClearTask to destroy it.
api.create_task = api.DAQmxCreateTask
api.create_task.argtypes = [C.c_char_p, C.POINTER(C.c_void_p)]
api.create_task.restype = check_error

#int32 DAQmxCreateAOVoltageChan (TaskHandle taskHandle, const char physicalChannel[], const char nameToAssignToChannel[],
# float64 minVal, float64 maxVal, int32 units, const char customScaleName[]);
# Creates channel(s) to generate voltage and adds the channel(s) to the task you specify with taskHandle.
api.create_ao_voltage_channel = api.DAQmxCreateAOVoltageChan
api.create_ao_voltage_channel.argtypes = [
    C.c_void_p,
    C.c_char_p,
    C.c_char_p,
    C.c_double,
    C.c_double,
    C.c_int32,
    C.c_char_p]
api.create_ao_voltage_channel.restype = check_error

#int32 DAQmxCreateDOChan (TaskHandle taskHandle, const char lines[], const char nameToAssignToLines[], int32 lineGrouping);
#Creates channel(s) to generate digital signals and adds the channel(s) to the task you specify with taskHandle. You can group
# digital lines into one digital channel or separate them into multiple digital channels. If you specify one or more entire ports
# in lines by using port physical channel names, you cannot separate the ports into multiple channels. To separate ports into multiple
# channels, use this function multiple times with a different port each time.
api.create_do_channel = api.DAQmxCreateDOChan
api.create_do_channel.argtypes = [
    C.c_void_p,
    C.c_char_p,
    C.c_char_p,
    C.c_int32]
api.create_do_channel.restype = check_error

#int32 DAQmxCfgSampClkTiming (TaskHandle taskHandle, const char source[], float64 rate, int32 activeEdge, int32 sampleMode, uInt64 sampsPerChanToAcquire);
#Sets the source of the Sample Clock, the rate of the Sample Clock, and the number of samples to acquire or generate.
api.clock_timing = api.DAQmxCfgSampClkTiming
api.clock_timing.argtypes = [
    C.c_void_p,
    C.c_char_p,
    C.c_double,
    C.c_int32,
    C.c_int32,
    C.c_uint64]
api.clock_timing.restype = check_error

#int32 DAQmxWriteAnalogF64 (TaskHandle taskHandle, int32 numSampsPerChan,
# bool32 autoStart, float64 timeout, bool32 dataLayout, float64 writeArray[],
# int32 *sampsPerChanWritten, bool32 *reserved);
#Writes multiple floating-point samples to a task that contains one or more analog output channels.
api.write_voltages = api.DAQmxWriteAnalogF64
api.write_voltages.argtypes = [
    C.c_void_p,
    C.c_int32,
    C.c_uint32, #NI calls this a 'bool32' haha awesome
    C.c_double,
    C.c_uint32,
    np.ctypeslib.ndpointer(dtype=np.float64, ndim=2), #Numpy is awesome.
    C.POINTER(C.c_int32),
    C.POINTER(C.c_uint32)]
api.write_voltages.restype = check_error

#int32 DAQmxWriteAnalogScalarF64 (TaskHandle taskHandle, bool32 autoStart, float64 timeout, float64 value, bool32 *reserved);
#Writes a floating-point sample to a task that contains a single analog output channel.
api.write_scalarvoltages = api.DAQmxWriteAnalogScalarF64
api.write_scalarvoltages.argtypes = [
    C.c_void_p,
    C.c_uint32,
    C.c_double,
    C.c_double,
    C.POINTER(C.c_uint32)]
api.write_scalarvoltages.restype = check_error

#int32 DAQmxWriteDigitalLines (TaskHandle taskHandle, int32 numSampsPerChan, bool32 autoStart, float64 timeout,
# bool32 dataLayout, uInt8 writeArray[], int32 *sampsPerChanWritten, bool32 *reserved);
#Writes multiple samples to each digital line in a task. When you create your write array, each sample per channel
# must contain the number of bytes returned by the DAQmx_Write_DigitalLines_BytesPerChan property.
api.write_digits = api.DAQmxWriteDigitalLines
api.write_digits.argtypes = [
    C.c_void_p,
    C.c_int32,
    C.c_uint32, #NI calls this a 'bool32' haha awesome
    C.c_double,
    C.c_uint32,
    np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2), #Numpy is awesome.
    C.POINTER(C.c_int32),
    C.POINTER(C.c_uint32)]
api.write_digits.restype = check_error


#Transitions the task from the committed state to the running state, which begins measurement or generation. Using this
# function is required for some applications and optional for others. If you do not use this function, a measurement task starts
# automatically when a read operation begins. The autoStart parameter of the NI-DAQmx Write functions determines if a generation
# task starts automatically when you use an NI-DAQmx Write function. If you do not call DAQmxStartTask and DAQmxStopTask when you
# call NI-DAQmx Read functions or NI-DAQmx Write functions multiple times, such as in a loop, the task starts and stops repeatedly.
# Starting and stopping a task repeatedly reduces the performance of the application.
api.start_task = api.DAQmxStartTask
api.start_task.argtypes = [C.c_void_p]
api.start_task.restype = check_error

#int32 DAQmxWaitUntilTaskDone (TaskHandle taskHandle, float64 timeToWait);
#Waits for the measurement or generation to complete. Use this function to ensure that the specified operation is complete before you stop the task.
api.finish_task = api.DAQmxWaitUntilTaskDone
api.finish_task.argtypes = [C.c_void_p, C.c_double]
api.finish_task.restype = check_error

#int32 DAQmxStopTask (TaskHandle taskHandle);
#Stops the task and returns it to the state it was in before you called DAQmxStartTask or called an NI-DAQmx Write function with autoStart set to TRUE.
api.stop_task = api.DAQmxStopTask
api.stop_task.argtypes = [C.c_void_p]
api.stop_task.restype = check_error

#int32 DAQmxClearTask (TaskHandle taskHandle);
#Clears the task. Before clearing, this function aborts the task, if necessary, and releases any resources reserved by the task.
# You cannot use a task once you clear the task without recreating or reloading the task.
api.clear_task = api.DAQmxClearTask
api.clear_task.argtypes = [C.c_void_p]
api.clear_task.restype = check_error


if __name__ == '__main__':
##    6738 test block
    rate = 2e4
    do_type = '6738_digital'
    do_name = 'Dev1'
    do_nchannels = 2
    do_clock = '/Dev1/ao/SampleClock'
    do = Analog_Out(
        num_channels=do_nchannels,
        rate=rate,
        daq_type=do_type,
        line= 'Dev1/port0/line0',
        clock_name=do_clock,
        verbose=True)

    ao_type = '6738'
    ao_nchannels = 7
    line_selection = "Dev1/ao0, Dev1/ao5, Dev1/ao6, Dev1/ao8, Dev1/ao11, Dev1/ao14, , Dev1/ao18"
    ao = Analog_Out(
        num_channels=ao_nchannels,
        rate=rate,
        daq_type=ao_type,
        line= line_selection,
        verbose=True)
    digits = np.zeros((do.s2p(10), do_nchannels), np.dtype(np.uint8))
    volts = np.zeros((ao.s2p(10), ao_nchannels), np.dtype(np.float64))
    digits[do.s2p(.25):do.s2p(.75), :] = 1
    volts[ao.s2p(.25):ao.s2p(1), :] = 5
    volts[ao.s2p(2.5):ao.s2p(4), :] = 5
    volts[ao.s2p(8):ao.s2p(10), :] = 5


    #channels: stage trigger, remote mirror, TTL laser (4), camera trigger
    exposure_time = 0.2 # 40 ms
    remote_low_vol = -2
    remote_high_vol =+2
    stage_triggertime = 0.002
    delay_camera_trigger = 0.002 #how long does stage needs to move
    camera_triggertime = 0.002
    returnpoint = ao.s2p(stage_triggertime + delay_camera_trigger)
    endpoint = ao.s2p(stage_triggertime + delay_camera_trigger + camera_triggertime + exposure_time)

    #np.linspace(remote_low_vol, remote_low_vol, num = ao.s2p(exposure_time + 0.004)-ao.s2p(0.000))
    basic_unit = np.zeros((endpoint, 7), np.dtype(np.float64))
    basic_unit[0:ao.s2p(stage_triggertime), 0] = 4 #stage trigger
    basic_unit[ao.s2p(stage_triggertime + delay_camera_trigger): ao.s2p(stage_triggertime + delay_camera_trigger + camera_triggertime),1] =4 # camera trigger
    basic_unit[ao.s2p(stage_triggertime + delay_camera_trigger + camera_triggertime): ao.s2p(stage_triggertime + delay_camera_trigger + camera_triggertime + exposure_time),2] =4 # laser trigger
    print(ao.s2p(exposure_time + 0.004)-ao.s2p(0.000))

    basic_unit[0 : returnpoint,3] = np.linspace(remote_high_vol, remote_low_vol, num = returnpoint-ao.s2p(0.000))
    basic_unit[returnpoint: endpoint,3] = np.linspace(remote_low_vol, remote_high_vol, num = endpoint-returnpoint)

    nb_frames = 5
    control_array = np.tile(basic_unit, (nb_frames, 1))
    print(control_array)
    ao.plot_voltages(control_array, ("ao0/stage", "ao5/camera", "ao6/laser", "ao8/remote mirror", "ao11", "ao14", "ao18"))

    #volts[ao.s2p(0.001):ao.s2p]
    #do.play_voltages(digits, force_final_zeros=True, block=False)
    #ao.play_voltages(volts, force_final_zeros=True, block=True)

    ao.play_voltages(control_array, force_final_zeros=True, block=True)

    ao_constant = Analog_Out(
        daq_type='6738_constant',
        line="Dev1/ao22",
        minVol=0,
        maxVol=5,
        verbose=True)

    ao_constant.setconstantvoltage(2)

    import time
    #time.sleep(4)
    print("closing")
    do.close()
    ao.close()
    ao_constant.close()
