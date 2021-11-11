class AcquisitionHardware:
    hardware_type = 'NI'

    # triggers
    master_trigger_out_line = 'PXI6259/port0/line1'
    camera_trigger_out_line = '/PXI6259/ctr0'
    camera_trigger_source = '/PXI6259/PFI0'
    laser_task_trigger_source = '/PXI6259/PFI0'
    galvo_etl_task_trigger_source = '/PXI6259/PFI0'

    # galvos
    galvo_etl_task_line = 'PXI6259/ao0:3'
    galvo_left = 'ao0'
    galvo_right = 'ao1'

    # ETL
    etl_left = 'ao2'
    etl_right = 'ao3'

    # lasers
    laser_488 = 'PXI6733/port0/line2'
    laser_561 = 'PXI6733/port0/line3'
    laser_647 = 'PXI6733/port0/line4'

    # shutters
    shutter_left = 'PXI6259/port0/line0'
    shutter_right = 'PXI6259/port2/line0'

class ASLMParameters:
    ASLM_acquisition_time = 0.3
    ASLM_from_volt = 0  # first voltage applied at remote mirror
    ASLM_to_volt = 1  # voltage applied at remote mirror at the end of sawtooth
    ASLM_current_volt = 0  # current voltage applied to remote mirror
    ASLM_static_low_res_volt = 0  # default ASLM low res voltage
    ASLM_static_high_res_volt = 0  # default ASLM high res voltage
    ASLM_alignment_on = 0  # param=1 if ASLM alignment mode is on, otherwise zero
    ASLM_delay_before_voltage_return = 0.001  # 1ms
    ASLM_additional_return_time = 0.001  # 1ms
    #ASLM_scan_width = ASLM_parameters.simultaneous_lines

class StageParameters:
    stage_type = 'PI'
    controllername = 'C-884'
    stages = ('L-509.20DG10', 'L-509.40DG10', 'L-509.20DG10', 'M-060.DG', 'M-406.4PD', 'NOSTAGE')
    refmode = ('FRF', 'FRF', 'FRF', 'FRF', 'FRF', 'FRF',)
    serialnum = '119060508'
    y_unload_position = 10000
    y_load_position = 90000
    startfocus = 70700
    x_max = 50000
    x_min = 2000
    y_max = 100000
    y_min = 2000
    z_max = 50000
    z_min = 2000
    f_max = 100000
    f_min = 2000
    theta_max = 360
    theta_min = 0
    x_rot_position = 2000
    y_rot_position = 2000
    z_rot_position = 2000

class ZoomParameters:
    zoom_type = 'Dynamixel'
    servo_id = 1
    COM_port = 'COM21'
    baudrate = 1000000
    zoom_position = {'0.63x': 0,
                '1x': 627,
                '2x': 1711,
                '3x': 2301,
                '4x': 2710,
                '5x': 3079,
                '6x': 3383}

    low_res_zoom_pixel_size = {'0.63x': 9.7,
             '1x': 6.38,
             '2x': 3.14,
             '3x': 2.12,
             '4x': 1.609,
             '5x': 1.255,
             '6x': 1.044}

    high_res_zoom_pixel_size = 0.167

class FilterWheelParameters:
    avail_filters = {'Empty-Alignment': 0,
                  'GFP - FF01-515/30-32': 1,
                  'RFP - FF01-595/31-32': 2,
                  'Far-Red - BLP01-647R/31-32': 3,
                  'Blocked1': 4,
                  'Blocked2': 5,
                  'Blocked3': 6,
                  'Blocked4': 7,
                  'Blocked5': 8,
                  'Blocked6': 9}

    filterwheel_parameters = {'filterwheel_type': 'Sutter', 'COMport': 'COM9'}
    number_of_filter_wheels = 2

class CameraParameters:
    type = 'HamamatsuOrca'
    number_of_cameras = 2
    camera_parameters = {'x_pixels': 2048,
                         'y_pixels': 2048,
                         'x_pixel_size_in_microns': 6.5,
                         'y_pixel_size_in_microns': 6.5,
                         'subsampling': [1, 2, 4],
                         'sensor_mode': 12,  # 12 for progressive
                         'defect_correct_mode': 2,
                         'binning': '1x1',
                         'readout_speed': 1,
                         'trigger_active': 1,
                         'trigger_mode': 1, # it is unclear if this is the external lightsheeet mode - how to check this?
                         'trigger_polarity': 2,  # positive pulse
                         'trigger_source': 2,  # external
                         'camera_line_interval': 0.000075,
                         'camera_exposure_time': 0.01,
                         }
    exposure_time = 200

class SavingParameters:
    saving_dict = {
    'auto_save' : False,
    'auto_save_waterfall' : True,
    'directory' : 'E:\',
    'filename_video' : 'Video',  # Can be the same filename for video and photo
    'filename_photo' : 'Snap',
    'filename_waterfall' : 'Waterfall',
    'filename_trajectory' : 'Trajectory',
    'filename_log' : 'Log',
    'max_memory' : 800  # In megabytes
    }


class FileSaveParameters:
    # HDF5 can have subsampling of ((1, 1, 1), (2, 2, 2), ...) for (z, y, x)
    # Compression can be None, 'gzip', 'lzf'
    # flip_xy can be True or False, to match BigStitcher coordinates
    hdf5 = {'subsampling': ((1, 1, 1),),
             'compression': None,
             'flip_xyz': (True, True, False)
             }

    parentdir = "E:/"


'''
class NI_board_parameters:
    # "ao0/highrescamera", "ao1/lowrescamera", "ao3/stage", "ao5/laser488TTL",
    # "ao6/laser552_TTL", "ao8/laser594_TTL", "ao11/laser640_TTL", "ao12/voicecoil"
    line_selection = "Dev1/ao0, Dev1/ao1, Dev1/ao3, Dev1/ao5, Dev1/ao6, Dev1/ao8, Dev1/ao11, Dev1/ao12"
    ao_type = '6738'
    ao_nchannels = 8
    rate = 2e4
    highres_camera = 0
    lowres_camera = 1
    stage = 2
    laser488 = 3
    laser552 = 4
    laser594 = 5
    laser640 = 6
    voicecoil = 7


    #constant values for laser power etc...
    ao_type_constant = '6738_constant'
    power_488_line = "Dev1/ao17"
    power_552_line = "Dev1/ao18"
    power_594_line = "Dev1/ao22"
    power_640_line = "Dev1/ao25"
    flip_mirror_line = "Dev1/ao26"
    mSPIM_mirror_line = "Dev1/ao29"
    mSPIM_mirror_voltage = 0.1
    minVol_constant = 0
    maxVol_constant = 5
    max_mSPIM_constant = 2


# class SharedMemory_allocation:
#     # Acquisition:
#     vol_per_buffer = 1
#     num_data_buffers = 2  # increase for multiprocessing
#     num_snap = 1  # interbuffer time limited by ao play
#     images_per_buffer = 1
#     bytes_per_data_buffer = images_per_buffer * 6000 * 4000 * 2
#     bytes_per_preview_buffer = bytes_per_data_buffer * 3

'''