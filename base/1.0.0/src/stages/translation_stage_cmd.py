'''
translation_stage_cmd.py
========================================
Script containing all functions to initialize and operate the translation stages from Smaract
'''

import sys
from threading import Event, Thread
import numpy as np

try:
    from .smaract import ctl as ctl
except ImportError:
    import smaract.ctl as ctl



class SLC_translationstage:

    def __init__(self, locator):
        '''
        Initialize translation stage parameters, and print out some parameters for debugging
        Input: locator address of the translation stage, e.g. usb:sn:MCS2-00001795
        Output: an initialized and connected stage.
        '''
        self.locator = locator
        self.d_handle = 0
        self.no_of_channels = 0

        # Read the version of the library
        # Note: this is the only function that does not require the library to be initialized.
        version = ctl.GetFullVersionString()
        print("SmarActCTL library version: '{}'.".format(version))
        self.assert_lib_compatibility()

        try:
            # Open the MCS2 device
            self.d_handle = ctl.Open(self.locator)
            print("MCS2 opened {}.".format(self.locator))

            serial = ctl.GetProperty_s(self.d_handle, 0, ctl.Property.DEVICE_SERIAL_NUMBER)
            print("Device Serial Number: {}".format(serial))

        except ctl.Error as e:
            # Passing an error code to "GetResultInfo" returns a human readable string
            # specifying the error.
            print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}."
              .format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code,
                      (sys.exc_info()[-1].tb_lineno)))

        except Exception as ex:
            print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))
            raise

        self.no_of_channels = ctl.GetProperty_i32(self.d_handle, 0, ctl.Property.NUMBER_OF_CHANNELS)
        print("MCS2 number of channels: {}.".format(self.no_of_channels))

        #initialize stream events
        self.stream_done = Event()
        self.stream_abort = Event()



    def assert_lib_compatibility(self):
        """
        Checks that the major version numbers of the Python API and the
        loaded shared SmarAct library are the same to avoid errors due to
        incompatibilities.
        Raises a RuntimeError if the major version numbers are different.
        """
        vapi = ctl.api_version
        vlib = [int(i) for i in ctl.GetFullVersionString().split('.')]
        if vapi[0] != vlib[0]:
            raise RuntimeError("Incompatible SmarActCTL python api and library version.")

    def findReference(self):
        # Set find reference options.
        # The reference options specify the behavior of the find reference sequence.
        # The reference flags can be ORed to build the reference options.
        # By default (options = 0) the positioner returns to the position of the reference mark.
        # Note: In contrast to previous controller systems this is not mandatory.
        # The MCS2 controller is able to find the reference position "on-the-fly".
        # See the MCS2 Programmer Guide for a description of the different modes.

        for channel in range(self.no_of_channels):
            print("MCS2 find reference on channel: {}.".format(channel))

            ctl.SetProperty_i32(self.d_handle, channel, ctl.Property.REFERENCING_OPTIONS, 0)
            # Set velocity to 1mm/s
            ctl.SetProperty_i64(self.d_handle, channel, ctl.Property.MOVE_VELOCITY, 2000000000)
            # Set acceleration to 10mm/s2.
            ctl.SetProperty_i64(self.d_handle, channel, ctl.Property.MOVE_ACCELERATION, 10000000000)
            # Start referencing sequence
            ctl.Reference(self.d_handle, channel)
            # Note that the function call returns immediately, without waiting for the movement to complete.
            # The "ChannelState.REFERENCING" flag in the channel state can be monitored to determine
            # the end of the referencing sequence.
            self.waitForEvent_referencing()

        #Set all positions to 0 pm
        for channel in range(self.no_of_channels):
            state = ctl.GetProperty_i32(self.d_handle, channel, ctl.Property.CHANNEL_STATE)
            # The returned channel state holds a bit field of several state flags.
            # See the MCS2 Programmers Guide for the meaning of all state flags.
            # We pick the "sensorPresent" flag to check if there is a positioner connected
            # which has an integrated sensor.
            # Note that in contrast to previous controller systems the controller supports
            # hotplugging of the sensor module and the actuators.
            position = ctl.GetProperty_i64(self.d_handle, channel, ctl.Property.POSITION)
            base_unit = ctl.GetProperty_i32(self.d_handle, channel, ctl.Property.POS_BASE_UNIT)

            #print("MCS2 position of channel {}: {}".format(channel, position), end='')
            #print("pm.") if base_unit == ctl.BaseUnit.METER else print("ndeg.")

            position = 0  # in pm | ndeg
            print("MCS2 setting position of channel {} to {}".format(channel, position), end='')
            base_unit = ctl.GetProperty_i32(self.d_handle, channel, ctl.Property.POS_BASE_UNIT)
            print("pm.") if base_unit == ctl.BaseUnit.METER else print("ndeg.")
            ctl.SetProperty_i64(self.d_handle, channel, ctl.Property.POSITION, position)


    def close(self):
        if self.d_handle != None:
            ctl.Close(self.d_handle)
            print("MCS2 close.")


    def waitForEvent_referencing(self):
        """ Wait for events generated by the connected device """
        # The wait for event function blocks until an event was received or the timeout elapsed.
        # In case of timeout, a "ctl.Error" exception is raised containing the "TIMEOUT" error.
        # If the "timeout" parameter is set to "ctl.INFINITE" the call blocks until an event is received.
        # This can be useful in case the WaitForEvent function runs in a separate thread.
        # For simplicity, this is not shown here thus we set a timeout of 3 seconds.
        timeout = 60000  # in ms
        try:
            event = ctl.WaitForEvent(self.d_handle, timeout)
            # The "type" field specifies the event. The "idx" field holds the device index for this event
            # The "i32" data field gives additional information about the event.
            if event.type == ctl.EventType.REFERENCE_FOUND:
                if (event.i32 == ctl.ErrorCode.NONE):
                    # Movement finished.
                    print("MCS2 reference found, channel: ", event.idx)
                    self.waitForEvent_MovementComplete()
                else:
                    # The movement failed for some reason. E.g. an endstop was detected.
                    print("MCS2 reference found, channel: {}, error: 0x{:04X} ({}) ".format(event.idx, event.i32,
                                                                                              ctl.GetResultInfo(
                                                                                                  event.i32)))
            else:
                # The code should be prepared to handle unexpected events beside the expected ones.
                print("MCS2 received event: {}".format(ctl.GetEventInfo(event)))
                self.waitForEvent_referencing()

        except ctl.Error as e:
            if e.code == ctl.ErrorCode.TIMEOUT:
                print("MCS2 wait for event timed out after {} ms".format(timeout))
            else:
                print("MCS2 {}".format(ctl.GetResultInfo(e.code)))
            return

    def waitForEvent_MovementComplete_Channels(self, nb_channels):
        """ Wait for movement complete events generated by the connected device """
        iter =0
        timeout = 30000  # in ms
        done = False
        while (not done):
            try:
                event = ctl.WaitForEvent(self.d_handle, timeout)

                if event.type == ctl.EventType.MOVEMENT_FINISHED:
                    if (event.i32 == ctl.ErrorCode.NONE):
                        print("MCS2 movement finished, channel: ", event.idx)
                        iter = iter+1
                        if(nb_channels == iter):
                            done=True

                    else:
                        print("MCS2 movement finished, channel: {}, error: 0x{:04X} ({}) ".format(event.idx, event.i32, ctl.GetResultInfo(event.i32)))
                else:
                    print("MCS2 received event: {}".format(ctl.GetEventInfo(event)))

            except ctl.Error as e:
                if e.code == ctl.ErrorCode.TIMEOUT:
                    print("MCS2 wait for event timed out after {} ms".format(timeout))
                else:
                    print("MCS2 {}".format(ctl.GetResultInfo(e.code)))
                return

    def waitForEvent_MovementComplete(self):
        """ Wait for movement complete events generated by the connected device """

        timeout = 30000  # in ms
        try:
            event = ctl.WaitForEvent(self.d_handle, timeout)

            if event.type == ctl.EventType.MOVEMENT_FINISHED:
                if (event.i32 == ctl.ErrorCode.NONE):
                    print("MCS2 movement finished, channel: ", event.idx)
                else:
                    print("MCS2 movement finished, channel: {}, error: 0x{:04X} ({}) ".format(event.idx, event.i32, ctl.GetResultInfo(event.i32)))
            else:
                print("MCS2 received event: {}".format(ctl.GetEventInfo(event)))

        except ctl.Error as e:
            if e.code == ctl.ErrorCode.TIMEOUT:
                print("MCS2 wait for event timed out after {} ms".format(timeout))
            else:
                print("MCS2 {}".format(ctl.GetResultInfo(e.code)))
            return

    def waitForEvent_stream(self):
        """Wait for events generated by the connected device"""
        while True:
            try:
                event = ctl.WaitForEvent(self.d_handle, ctl.INFINITE)

                if event.type == ctl.EventType.STREAM_FINISHED:
                    print("MCS2 {}".format(ctl.GetEventInfo(event)))
                    if ctl.EventParameter.PARAM_RESULT(event.i32) == ctl.ErrorCode.NONE:
                        print("MCS2 stream ended")
                        # All streaming frames were processed, stream finished.
                        self.stream_done.set()
                    elif ctl.EventParameter.PARAM_RESULT(event.i32) == ctl.ErrorCode.ABORTED:
                        # Stream was canceled by the user.
                        print("MCS2 stream aborted by user")
                        self.stream_done.set()
                        self.stream_abort.set()
                    else:
                        # Stream was canceled by device.
                        # Note: The event parameter now holds the error code as well as the channel index responsible for the failure
                        print("MCS2 stream aborted by device: {}".format(ctl.ErrorCode(ctl.EventParameter.PARAM_RESULT(event.i32)).name))
                        self.stream_done.set()
                        self.stream_abort.set()
                elif event.type == ctl.EventType.STREAM_READY or event.type == ctl.EventType.STREAM_TRIGGERED:
                    # These events are mainly useful when the STREAM_TRIGGER_MODE_EXTERNAL_ONCE trigger mode is used.
                    # A STREAM_READY event is generated to indicate that the stream is ready to be triggered
                    # by the external trigger. In this armed state the device waits for the trigger to occur and then generates a
                    # STREAM_TRIGGERED event.
                    print("MCS2 stream ready to trigger or triggered")
                else:
                    # The code should be prepared to handle unexpected events beside the expected ones.
                    print("MCS2 received event: {}".format(ctl.GetEventInfo(event)))

            except ctl.Error as e:
                if e.code == ctl.ErrorCode.CANCELED:
                    # we use "INFINITE" timeout, so the function call will return only when canceled by the "Cancel" function
                    print("MCS2 canceled wait for event")
                else:
                    print("MCS2 {}".format(ctl.GetResultInfo(e.code)))
                return

    def waitForEvent_CommandGroupTriggered(self):
        """ Wait for events generated by the connected device """

        timeout = 100000  # in ms
        done = False
        while (not done):
            try:
                event = ctl.WaitForEvent(self.d_handle, timeout)

                if event.type == ctl.EventType.CMD_GROUP_TRIGGERED:
                    # A command group has been executed.
                    # The event parameter holds:
                    # - the result code of the group (Bit 0-15)
                    # - the corresponding transmit handle of the group (Bit 31-24)
                    t_handle = ctl.EventParameter.PARAM_HANDLE(event.i32)
                    result_code = ctl.EventParameter.PARAM_RESULT(event.i32)
                    if result_code == ctl.ErrorCode.NONE:
                        print("MCS2 command group triggered, handle: {}".format(t_handle))
                    else:
                        # The command group failed -> the reason may be found in the result code.
                        # To determine which command caused the error, read the individual results of the command
                        # with "WaitForWrite" / "ReadProperty_x".
                        print(
                            "MCS2 command group failed, handle: {}, error: 0x{:04X} ({})".format(t_handle, result_code,
                                                                                                 ctl.GetResultInfo(
                                                                                                     result_code)))
                    done = True
                else:
                    # ignore other events and wait for the next one
                    pass
            except ctl.Error as e:
                if e.code == ctl.ErrorCode.TIMEOUT:
                    print("MCS2 wait for event timed out after {} ms".format(timeout))
                else:
                    print("MCS2 {}".format(ctl.GetResultInfo(e.code)))
                return

    def stream_csvFile(self):

        NUMBER_OF_STREAMING_CHANNELS = 2
        MAX_NUMBER_OF_FRAMES = 1024
        STREAM_FILE_NAME = "streamPoses.csv"

        self.stream_done.clear()
        self.stream_abort.clear()

        try:
            with open(STREAM_FILE_NAME) as file:
                # Consume the head line
                next(file)
                no_of_frames = 0
                valid = True
                stream_buffer = []
                for line in file:
                    line = line.strip()
                    # Ignore blank lines
                    if not line:
                        continue
                    ch_A, pos_A, ch_B, pos_B = line.split(",")
                    # Basic valid checks
                    if (int(ch_A) < 0) or (int(ch_B) < 0) or (int(ch_A) > int(ch_B)):
                        # Channels must be in ascending order
                        valid = False
                        break
                    if no_of_frames >= MAX_NUMBER_OF_FRAMES:
                        break
                    # Write frames to buffer
                    frame = [int(ch_A), int(pos_A), int(ch_B), int(pos_B)]
                    stream_buffer.append(frame)
                    no_of_frames += 1
        except Exception as e:
            print("Failed to open pose file {}: {}, abort.".format(STREAM_FILE_NAME, e))
            input()
            sys.exit(1)

        if (not valid):
            print("File format invalid.")
            input()
            sys.exit(1)
        else:
            print("Read {} stream frames from file {}".format(no_of_frames, STREAM_FILE_NAME))

        try:

            # Spawn a thread to receive events from the controller.
            event_handle_thread = Thread(target=self.waitForEvent_stream)
            event_handle_thread.start()

            # Set position zero, enable amplifier
            # Sensor power mode: enabled (disable power save, which is not allowed with position streaming)
            for channel in range(NUMBER_OF_STREAMING_CHANNELS):
                ctl.SetProperty_i64(self.d_handle, channel, ctl.Property.POSITION, 0)
                ctl.SetProperty_i32(self.d_handle, channel, ctl.Property.SENSOR_POWER_MODE, ctl.SensorPowerMode.ENABLED)
                ctl.SetProperty_i32(self.d_handle, channel, ctl.Property.AMPLIFIER_ENABLED, ctl.TRUE)

            # Configure stream (optional)
            # Note: the stream rate must be a whole-number multiplier of the external sync rate.
            # Set external sync rate to 100Hz (only active when using trigger mode STREAM_TRIGGER_MODE_EXTERNAL_SYNC)
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.STREAM_EXT_SYNC_RATE, 100)
            # Set stream base rate to 1kHz
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.STREAM_BASE_RATE, 1000)
            # Prepare for streaming, select desired trigger mode
            # (using STREAM_TRIGGER_MODE_DIRECT starts the stream as soon as enough frames were sent to the device)
            s_handle = ctl.OpenStream(self.d_handle, ctl.StreamTriggerMode.DIRECT)
            # Send all frames in a loop
            # Note: the "AbortStream" function could be used to abort a running stream programmatically.
            for frame_idx in range(no_of_frames):
                # The "waitForEvent" thread received an "abort" event.
                if self.stream_abort.isSet():
                    break
                # Make list from stream data, each frame contains all
                # target positions for all channels that participate in the trajectory.
                # The frame data list must have the structure:
                # <chA>,<posA,<chB>,<posB>
                frame = stream_buffer[frame_idx]
                ctl.StreamFrame(self.d_handle, s_handle, frame)

            # All frames sent, close stream
            ctl.CloseStream(self.d_handle, s_handle)
            # Wait for the "stream done" event.
            self.stream_done.wait()
            # Cancel waiting for events.
            ctl.Cancel(self.d_handle)
            # Wait for the "waitForEvent" thread to terminate.
            event_handle_thread.join()

        except ctl.Error as e:
            # Passing an error code to "GetResultInfo" returns a human readable string
            # specifying the error.
            print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}."
                  .format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code,
                          (sys.exc_info()[-1].tb_lineno)))

        except Exception as ex:
            print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))
            raise

    def moveToPosition(self, position_list):
        r_id = [0] * 9
        print(r_id)
        t_handle = ctl.OpenCommandGroup(self.d_handle, ctl.CmdGroupTriggerMode.DIRECT)

        r_id[0] = ctl.RequestWriteProperty_i32(self.d_handle, 0, ctl.Property.AMPLIFIER_ENABLED,
                                               ctl.TRUE, tHandle=t_handle)

        r_id[1] = ctl.RequestWriteProperty_i32(self.d_handle, 1, ctl.Property.AMPLIFIER_ENABLED,
                                               ctl.TRUE, tHandle=t_handle)

        r_id[2] = ctl.RequestWriteProperty_i32(self.d_handle, 2, ctl.Property.AMPLIFIER_ENABLED,
                                               ctl.TRUE, tHandle=t_handle)

        ctl.CloseCommandGroup(self.d_handle, t_handle)

        # Wait for the "triggered" event before reading the results
        self.waitForEvent_CommandGroupTriggered()
        # One important thing to notice is that the WaitForWrite function calls must be issued
        # after the command group was closed. Otherwise the function calls will block.
        # Note that synchronous property accesses cannot be put into a command group.
        ctl.WaitForWrite(self.d_handle, r_id[0])
        ctl.WaitForWrite(self.d_handle, r_id[1])
        ctl.WaitForWrite(self.d_handle, r_id[2])


        ##start movement
        t_handle = ctl.OpenCommandGroup(self.d_handle, ctl.CmdGroupTriggerMode.DIRECT)

        r_id[0] = ctl.RequestWriteProperty_i32(self.d_handle, 0, ctl.Property.MOVE_MODE,
                                               ctl.MoveMode.CL_ABSOLUTE, tHandle=t_handle)
        r_id[1] = ctl.RequestWriteProperty_i32(self.d_handle, 1, ctl.Property.MOVE_MODE,
                                               ctl.MoveMode.CL_ABSOLUTE, tHandle=t_handle)
        r_id[2] = ctl.RequestWriteProperty_i32(self.d_handle, 2, ctl.Property.MOVE_MODE,
                                               ctl.MoveMode.CL_ABSOLUTE, tHandle=t_handle)
        r_id[3] = ctl.RequestWriteProperty_i64(self.d_handle, 0, ctl.Property.MOVE_VELOCITY,
                                               10000000000, tHandle=t_handle)
        r_id[4] = ctl.RequestWriteProperty_i64(self.d_handle, 1, ctl.Property.MOVE_VELOCITY,
                                               10000000000, tHandle=t_handle)
        r_id[5] = ctl.RequestWriteProperty_i64(self.d_handle, 2, ctl.Property.MOVE_VELOCITY,
                                               10000000000, tHandle=t_handle)
        r_id[6] = ctl.RequestWriteProperty_i64(self.d_handle, 0, ctl.Property.MOVE_ACCELERATION,
                                               100000000000, tHandle=t_handle)
        r_id[7] = ctl.RequestWriteProperty_i64(self.d_handle, 1, ctl.Property.MOVE_ACCELERATION,
                                               100000000000, tHandle=t_handle)
        r_id[8] = ctl.RequestWriteProperty_i64(self.d_handle, 2, ctl.Property.MOVE_ACCELERATION,
                                               100000000000, tHandle=t_handle)

        ctl.Move(self.d_handle, 0, position_list[0], t_handle)
        ctl.Move(self.d_handle, 1, position_list[1], t_handle)
        ctl.Move(self.d_handle, 2, position_list[2], t_handle)

        ctl.CloseCommandGroup(self.d_handle, t_handle)

        # Wait for the "triggered" event before reading the results
        self.waitForEvent_CommandGroupTriggered()


        for id in r_id:
            ctl.WaitForWrite(self.d_handle, id)

        self.waitForEvent_MovementComplete_Channels(3)

        # Next we create a command group to read some properties: the current position of both channels.
        t_handle = ctl.OpenCommandGroup(self.d_handle, ctl.CmdGroupTriggerMode.DIRECT)

        r_id[0] = ctl.RequestReadProperty(self.d_handle, 0, ctl.Property.POSITION, t_handle)
        r_id[1] = ctl.RequestReadProperty(self.d_handle, 1, ctl.Property.POSITION, t_handle)
        r_id[2] = ctl.RequestReadProperty(self.d_handle, 2, ctl.Property.POSITION, t_handle)
        ctl.CloseCommandGroup(self.d_handle, t_handle)

        # Wait for the "triggered" event before reading the results
        self.waitForEvent_CommandGroupTriggered()
        # The same rule applies as for write properties:
        # Put the RequestReadProperty calls into the command group,
        # but issue e.g. ReadProperty_i64 calls after the group close.
        position_0 = ctl.ReadProperty_i64(self.d_handle, r_id[0])
        position_1 = ctl.ReadProperty_i64(self.d_handle, r_id[1])
        position_2 = ctl.ReadProperty_i64(self.d_handle, r_id[2])

        print("Position channel 0: {} pm, channel 1: {} pm, channel 2: {} pm.".format(position_0, position_1, position_2))

    # def streamStackAcquisition(self, no_of_frames, increment):
    #
    #     self.stream_done.clear()
    #     self.stream_abort.clear()
    #
    #     startPosition = ctl.GetProperty_i64(self.d_handle, 0, ctl.Property.POSITION)
    #     print(startPosition)
    #
    #     stream_buffer = []
    #     for frame_idx in range(no_of_frames):
    #         frame = [int(0), int(startPosition + frame_idx * increment)]
    #         stream_buffer.append(frame)
    #
    #     stream_buffer.append([int(0), startPosition])
    #
    #     try:
    #
    #         # Spawn a thread to receive events from the controller.
    #         event_handle_thread = Thread(target=self.waitForEvent_stream)
    #         event_handle_thread.start()
    #
    #         # Set position zero, enable amplifier
    #         # Sensor power mode: enabled (disable power save, which is not allowed with position streaming)
    #
    #         #ctl.SetProperty_i64(self.d_handle, 0, ctl.Property.POSITION, 0)
    #         ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.SENSOR_POWER_MODE, ctl.SensorPowerMode.ENABLED)
    #         ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.AMPLIFIER_ENABLED, ctl.TRUE)
    #         #ctl.SetProperty_i32(self.d_handle,0, ctl.Property.MOVE_VELOCITY, 100000000000)
    #         ctl.SetProperty_i32(self.d_handle,0, ctl.Property.MOVE_VELOCITY, 0)
    #
    #         ctl.SetProperty_i32(self.d_handle,0, ctl.Property.MOVE_ACCELERATION, 100000000000)
    #
    #         # Configure stream (optional)
    #         # Note: the stream rate must be a whole-number multiplier of the external sync rate.
    #         # Set external sync rate to 100Hz (only active when using trigger mode STREAM_TRIGGER_MODE_EXTERNAL_SYNC)
    #         ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.STREAM_EXT_SYNC_RATE, 100)
    #         # Set stream base rate to 1kHz
    #         ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.STREAM_BASE_RATE, 1000)
    #         # Prepare for streaming, select desired trigger mode
    #         # (using STREAM_TRIGGER_MODE_DIRECT starts the stream as soon as enough frames were sent to the device)
    #         s_handle = ctl.OpenStream(self.d_handle, ctl.StreamTriggerMode.DIRECT)
    #         # Send all frames in a loop
    #         # Note: the "AbortStream" function could be used to abort a running stream programmatically.
    #         for frame_idx in range(no_of_frames+1):
    #             # The "waitForEvent" thread received an "abort" event.
    #             if self.stream_abort.isSet():
    #                 break
    #             # Make list from stream data, each frame contains all
    #             # target positions for all channels that participate in the trajectory.
    #             # The frame data list must have the structure:
    #             # <chA>,<posA,<chB>,<posB>
    #             frame = stream_buffer[frame_idx]
    #             ctl.StreamFrame(self.d_handle, s_handle, frame)
    #
    #         # All frames sent, close stream
    #         ctl.CloseStream(self.d_handle, s_handle)
    #         # Wait for the "stream done" event.
    #         self.stream_done.wait()
    #         # Cancel waiting for events.
    #         ctl.Cancel(self.d_handle)
    #         # Wait for the "waitForEvent" thread to terminate.
    #         event_handle_thread.join()
    #
    #     except ctl.Error as e:
    #         # Passing an error code to "GetResultInfo" returns a human readable string
    #         # specifying the error.
    #         print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}."
    #               .format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code,
    #                       (sys.exc_info()[-1].tb_lineno)))
    #
    #     except Exception as ex:
    #         print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))
    #         raise

    def streamStackAcquisition_externalTrigger_setup(self, no_of_frames, increment, slow_velocity, slow_acceleration):
        """

        :param no_of_frames: how many frames the stream will be
        :param increment: how many um the stream will go up
        :param slow_velocity: the factor for velocity of 10 mm/s
        :param slow_acceleration: the factor for acceleration 100 mm/s2
        :return: a waiting stream to receive voltage inputs
        """
        self.stream_done.clear()
        self.stream_abort.clear()

        #check velocity not too high
        if slow_velocity >= 1:
            slow_velocity =1
        if slow_acceleration >= 1:
            slow_acceleration =1

        #get starting position for stream
        startPosition = ctl.GetProperty_i64(self.d_handle, 0, ctl.Property.POSITION)
        print(startPosition)

        #generate array with relative positions to starting value based on the chosen increment
        stream_buffer = []
        for frame_idx in range(no_of_frames):
            frame = [int(0), int(startPosition + frame_idx * increment)]
            stream_buffer.append(frame)

        stream_buffer.append([int(0), startPosition])

        #set stage speed
        velocityvalue = np.ulonglong(slow_velocity * 10000000000)
        accelerationvalue = np.ulonglong(slow_acceleration * 100000000000)
        ctl.SetProperty_i64(self.d_handle, 0, ctl.Property.MOVE_VELOCITY, velocityvalue)
        ctl.SetProperty_i64(self.d_handle,0, ctl.Property.MOVE_ACCELERATION, accelerationvalue)

        try:
            # Spawn a thread to receive events from the controller.
            self.event_handle_thread_triggeredStream = Thread(target=self.waitForEvent_stream)
            self.event_handle_thread_triggeredStream.start()

            # Set enable amplifier
            # Sensor power mode: enabled (disable power save, which is not allowed with position streaming)
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.SENSOR_POWER_MODE, ctl.SensorPowerMode.ENABLED)
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.AMPLIFIER_ENABLED, ctl.TRUE)

            print("Set trigger condition to rising edge.")
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.DEV_INPUT_TRIG_CONDITION, ctl.TriggerCondition.RISING)
            print("Configure input trigger mode to stream mode.")
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.DEV_INPUT_TRIG_MODE,
                                ctl.DeviceInputTriggerMode.STREAM)

            # print("set output trigger to report when target reached")
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.IO_MODULE_VOLTAGE, ctl.IOModuleVoltage.VOLTAGE_3V3)
            # # Enable the digital output driver circuit of the I/O module.
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.IO_MODULE_OPTIONS, ctl.IOModuleOption.DIGITAL_OUTPUT_ENABLED)
            #

            #position compare
            result = ctl.SetProperty_i64(self.d_handle, 0, ctl.Property.CH_POS_COMP_START_THRESHOLD, startPosition)
            if (result):
                print("get result 1")
            result = ctl.SetProperty_i64(self.d_handle, 0, ctl.Property.CH_POS_COMP_INCREMENT, increment)
            result = ctl.SetProperty_i32(self.d_handle,0, ctl.Property.CH_POS_COMP_DIRECTION, ctl.EITHER_DIRECTION)
            # disable limits
            ctl.SetProperty_i64(self.d_handle, 0, ctl.Property.CH_POS_COMP_LIMIT_MIN, 0)
            ctl.SetProperty_i64(self.d_handle, 0, ctl.Property.CH_POS_COMP_LIMIT_MAX, 0)
            if (result):
                print("get result 2")
            result = ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.CH_OUTPUT_TRIG_POLARITY, ctl.TriggerPolarity.ACTIVE_HIGH)
            if (result):
                print("get result 4")
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.CH_OUTPUT_TRIG_PULSE_WIDTH, 5000000)
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.CH_OUTPUT_TRIG_MODE, ctl.ChannelOutputTriggerMode.POSITION_COMPARE)



            # ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.CH_OUTPUT_TRIG_POLARITY, ctl.TriggerPolarity.ACTIVE_HIGH)
            # ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.CH_OUTPUT_TRIG_PULSE_WIDTH, 1000000)
            # ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.CH_OUTPUT_TRIG_MODE, ctl.ChannelOutputTriggerMode.TARGET_REACHED)
            #ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.CH_OUTPUT_TRIG_MODE, ctl.ChannelOutputTriggerMode.ACTIVELY_MOVING)




            # Configure stream (optional)
            # Note: the stream rate must be a whole-number multiplier of the external sync rate.
            # Set external sync rate to 100Hz (only active when using trigger mode STREAM_TRIGGER_MODE_EXTERNAL_SYNC)
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.STREAM_EXT_SYNC_RATE, 100)
            # Set stream base rate to 1kHz
            ctl.SetProperty_i32(self.d_handle, 0, ctl.Property.STREAM_BASE_RATE, 1000)
            # Prepare for streaming, select desired trigger mode
            s_handle = ctl.OpenStream(self.d_handle, ctl.StreamTriggerMode.EXTERNAL)
            # Send all frames in a loop
            # Note: the "AbortStream" function could be used to abort a running stream programmatically.
            for frame_idx in stream_buffer:
                # The "waitForEvent" thread received an "abort" event.
                if self.stream_abort.isSet():
                    break
                # Make list from stream data, each frame contains all
                # target positions for all channels that participate in the trajectory.
                # The frame data list must have the structure:
                # <chA>,<posA,<chB>,<posB>
                frame = frame_idx
                ctl.StreamFrame(self.d_handle, s_handle, frame)

            # All frames sent, close stream
            ctl.CloseStream(self.d_handle, s_handle)

        except ctl.Error as e:
            # Passing an error code to "GetResultInfo" returns a human readable string
            # specifying the error.
            print("MCS2 {}: {}, error: {} (0x{:04X}) in line: {}."
                  .format(e.func, ctl.GetResultInfo(e.code), ctl.ErrorCode(e.code).name, e.code,
                          (sys.exc_info()[-1].tb_lineno)))

        except Exception as ex:
            print("Unexpected error: {}, {} in line: {}".format(ex, type(ex), (sys.exc_info()[-1].tb_lineno)))
            raise

    def streamStackAcquisition_externalTrigger_waitEnd(self):
        # Wait for the "stream done" event.
        self.stream_done.wait()
        # Cancel waiting for events.
        ctl.Cancel(self.d_handle)
        # Wait for the "waitForEvent" thread to terminate.
        self.event_handle_thread_triggeredStream.join()

if __name__ == '__main__':
    ##test here code of this class

    stage_id = 'network:sn:MCS2-00000382'

    translationstage = SLC_translationstage(stage_id)
    translationstage.findReference()
    #3000000 = 3 um
    #translationstage.streamPosition(100, 3000000)
    position_list = [1000000000, 2000000000, 8000000000]
    translationstage.moveToPosition(position_list)

    import time
    time.sleep(5)
    translationstage.streamStackAcquisition(1000, 5000000)
    time.sleep(3)

    position_list = [3000000000, -2000000000, -8000000000]
    translationstage.moveToPosition(position_list)

    import time

    time.sleep(5)
    translationstage.streamStackAcquisition(1000, 5000000)
    time.sleep(3)

    position_list = [0, 0, 0]
    translationstage.moveToPosition(position_list)
    #translationstage.stream_csvFile()
    #translationstage.streamStackAcquisition(1000, 5000000)
    #translationstage.stream_csvFile()

    translationstage.close()