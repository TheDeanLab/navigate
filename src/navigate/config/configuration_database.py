camera_device_types = {
    "Daheng MER2-1220-32U3C": ("Daheng", "daheng"),
    "Hamamatsu ORCA Lightning": ("HamamatsuOrcaLightning", "hamamatsu"),
    "Hamamatsu ORCA Fire": ("HamamatsuOrcaFire", "hamamatsu"),
    "Hamamatsu ORCA Fusion": ("HamamatsuOrcaFusion", "hamamatsu"),
    "Hamamatsu Flash 4.0": ("HamamatsuOrca", "hamamatsu"),
    "Photometrics Iris 15B": ("Photometrics", "photometrics"),
    "Ximea MU196MR-ON": ("MU196XR", "ximea"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

camera_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", camera_device_types, None],
    "hardware/serial_number": [
        "Serial Number",
        "Input",
        "string",
        None,
        'Example: "302352"',
    ],
    "hardware/camera_connection": [
        "Camera Connection",
        "Input",
        "string",
        None,
        "*Photometrics Iris 15B only",
    ],
    "defect_correct_mode": [
        "Defect Correct Mode",
        "Combobox",
        "string",
        {"On": 2.0, "Off": 1.0},
        None,
    ],
    "delay": [
        "Delay (ms)",
        "Spinbox",
        "float",
        {"from": 0, "to": 100, "step": 0.1},
        None,
    ],
    "settle_down": [
        "Settle Down (ms)",
        "Spinbox",
        "float",
        {"from": 0, "to": 100, "step": 0.1},
        None,
    ],
    "flip_x": ["Flip X", "Checkbutton", "bool", None, None],
    "flip_y": ["Flip Y", "Checkbutton", "bool", None, None],
    "supported_channel_count": [
        "Microscope Channel Count",
        "Spinbox",
        "int",
        {"from": 5, "to": 10, "step": 1},
        None,
    ],
}

filter_wheel_device_types = {
    "Sutter Instruments": ("Sutter", "sutter"),
    "ASI Filter Wheel": ("ASI", "asi"),
    "ASI Dichroic Slider": ("ASICubeSlider", "asi"),
    "Ludl Electronic Products": ("LUDL", "ludl"),
    "Analog/Digital Device": ("NI", "ni"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

filter_wheel_widgets = {
    "filter_name": ["Filter Name", "Input", "string", None, "Example: Empty-Alignment"],
    "filter_value": ["Filter Value", "Input", "string", None, "Example: 0"],
    "button_1": ["Delete", "Button", {"delete": True}],
    "frame_config": {
        "ref": "available_filters",
        "format": "item(filter_name,filter_value),",
        "direction": "horizon",
    },
}

filter_wheel_hardware_widgets = {
    "hardware/type": [
        "Device Type",
        "Combobox",
        "string",
        filter_wheel_device_types,
        None,
    ],
    "hardware/wheel_number": ["Number of Wheels", "Spinbox", "int", None, "Example: 1"],
    "hardware/port": ["Serial Port", "Input", "string", None, "Example: COM1"],
    "hardware/baudrate": ["Baudrate", "Input", "int", None, "Example: 9600"],
    "hardware/name": ["GUI Label", "Input", "string", None, "Example: Filter Wheel 1"],
    "filter_wheel_delay": [
        "Filter Wheel Delay (s)",
        "Input",
        "float",
        None,
        "Example: 0.03",
    ],
    "button_1": [
        "Add Available Filters",
        "Button",
        {
            "widgets": filter_wheel_widgets,
            "ref": "available_filters",
            "direction": "horizon",
            "parent": "constants",
        },
    ],
}

daq_device_types = {
    "National Instruments": "NI",
    "Applied Scientific Instrumentation": ("ASI", "asi"),
    "Virtual Device": "Synthetic",
}

daq_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", daq_device_types, None],
    "sample_rate": ["Sample Rate", "Input", "int", None, "Example: 100000"],
    "trigger_reset_count": [
        "Trigger Reset Count",
        "Input",
        "int",
        None,
        "Default: 0 (disabled). Use a positive value only for unstable systems.",
    ],
    "master_trigger_out_line": [
        "Master Trigger Out",
        "Input",
        "string",
        None,
        "Example: PXI6259/port0/line1",
    ],
    "camera_trigger_out_line": [
        "Camera Trigger Out",
        "Input",
        "string",
        None,
        "Example: /PXI6259/ctr0",
    ],
    "trigger_source": [
        "Trigger Source",
        "Input",
        "string",
        None,
        "Example: /PXI6259/PFI0",
    ],
    "laser_port_switcher": [
        "Laser Switcher Port",
        "Input",
        "string",
        None,
        "Example: PXI6733/port0/line0",
    ],
    "laser_switch_state": [
        "Laser Switch On State",
        "Combobox",
        "bool",
        [True, False],
        None,
    ],
}

shutter_device_types = {
    "ASI Shutter": ("ASI", "asi"),
    "Analog/Digital Device": ("NI", "ni"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

shutter_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", shutter_device_types, None],
    "channel": ["NI Channel", "Input", "string", None, "Example: PXI6259/port0/line0"],
    "port": ["COM Port", "Input", "string", None, "Example: COM3"],
    "axis": ["Shutter Axis", "Input", "string", None, "Example: 1"],
    "min": ["Minimum Voltage", "Spinbox", "float", None, "Example: 0"],
    "max": ["Maximum Voltage", "Spinbox", "float", None, "Example: 5"],
    "frame_config": {"ref": "hardware"},
}

stage_device_types = {
    "Applied Scientific Instrumentation": ("ASI", "asi"),
    "ASI MFC2000": ("MFC2000", "asi"),
    "ASI MS2000": ("MS2000", "asi"),
    "NI Analog/Digital Device": ("NI", "ni"),
    "Newport Conex Controller": ("Conex", "conex"),
    "Mad City Labs": ("MCL", "mcl"),
    "Newport ESP302 Motion Controller": ("Newport", "newport"),
    "Physik Instrumente": ("PI", "pi"),
    "Sutter Instruments": ("MP285", "sutter"),
    "ThorLabs KCube Inertial Device KIM001": ("KIM001", "thorlabs"),
    "ThorLabs KCube Inertial Device KST101": ("KST101", "thorlabs"),
    "ThorLabs Kinesis Stepper Motor (Serial)": ("KINESIS", "thorlabs"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

stage_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", stage_device_types, None],
    "serial_number": ["Serial Number", "Input", "string", None, None],
    "axes": [
        "Axes",
        "Input",
        "string",
        None,
        "Example: [x, y, z, theta, f]",
        "[x, y, z]",
    ],
    "axes_mapping": [
        "Axes Mapping",
        "Input",
        "string",
        None,
        "Example: [X, M, Y, D, E]",
        "[X, M, Y]",
    ],
    "feedback_alignment": [
        "Feedback Alighment",
        "Input",
        "string",
        None,
        "*ASI stage only. Example: [90, 90, 90, 0, 90]",
        "[90, 90, 90]",
    ],
    "device_units_per_mm": [
        "Device Units Per Micron",
        "Input",
        "float",
        None,
        "*KST101 only. Example: 2000.0",
        1000.25,
    ],
    "volts_per_micron": [
        "Volts Per Micron",
        "Input",
        "string",
        None,
        "*Analog/Digital Device only. Example: '0.1*x+0.05'",
        "0.1*x+0.05",
    ],
    "min": [
        "Minimum Volts",
        "Spinbox",
        "float",
        {"from": 0, "to": 5, "step": 0.1},
        "*Analog/Digital Device only",
        0,
    ],
    "max": [
        "Maximum Volts",
        "Spinbox",
        "float",
        {"from": 1, "to": 100, "step": 0.1},
        "*Analog/Digital Device only",
        5,
    ],
    "distance_threshold": [
        "Distance Threshold",
        "Spinbox",
        "float",
        {"from": 0, "to": 100, "step": 1},
        "*Analog-Controlled Galvo/Peizo only",
        5,
    ],
    "settle_duration_ms": [
        "Settle Duration (ms)",
        "Spinbox",
        "float",
        {"from": 0, "to": 100, "step": 1},
        "*Analog-Controlled Galvo/Peizo only",
        20,
    ],
    "controllername": [
        "Controller Name",
        "Input",
        "string",
        None,
        "*Physik Instrumente only. Example: 'C-884'",
    ],
    "stages": [
        "PI Stages",
        "Input",
        "string",
        None,
        "*Physik Instrumente only. Example: L-509.20DG10 L-509.40DG10",
    ],
    "refmode": [
        "REF Modes",
        "Input",
        "string",
        None,
        "*Physik Instrumente only. Example: FRF FRF",
    ],
    "port": ["Serial Port", "Input", "string", None, "Example: COM1"],
    "baudrate": ["Baudrate", "Input", "int", None, "Example: 9600"],
    "timeout": ["Serial Timeout", "Input", "float", None, "Example: 0.25", 0.25],
    "button_2": ["Delete", "Button", {"delete": True}],
    "frame_config": {
        "collapsible": True,
        "title": "Stage",
        "ref": "hardware",
        "format": "list-dict",
    },
}

stage_top_widgets = {
    "button_1": [
        "Add New Stage Device",
        "Button",
        {"widgets": stage_hardware_widgets, "ref": "hardware", "parent": "hardware"},
    ],
}

stage_constants_widgets = {
    "joystick_axes": [
        "Joystick Axes",
        "Input",
        "string",
        None,
        "Example: [x, y, z]",
        "[x, y, z]",
    ],
    "x_min": [
        "Min X",
        "Spinbox",
        "float",
        {"from": -100000, "to": 100000, "step": 1000},
        None,
        -10000,
    ],
    "x_max": [
        "Max X",
        "Spinbox",
        "float",
        {"from": 0, "to": 100000, "step": 1000},
        None,
        10000,
    ],
    "y_min": [
        "Min Y",
        "Spinbox",
        "float",
        {"from": -100000, "to": 100000, "step": 1000},
        None,
        -10000,
    ],
    "y_max": [
        "Max Y",
        "Spinbox",
        "float",
        {"from": 0, "to": 100000, "step": 1000},
        None,
        10000,
    ],
    "z_min": [
        "Min Z",
        "Spinbox",
        "float",
        {"from": -100000, "to": 10000, "step": 1000},
        None,
        -10000,
    ],
    "z_max": [
        "Max Z",
        "Spinbox",
        "float",
        {"from": 0, "to": 100000, "step": 1000},
        None,
        10000,
    ],
    "theta_min": [
        "Min Theta",
        "Spinbox",
        "float",
        {"from": 0, "to": 360, "step": 1},
        None,
        0,
    ],
    "theta_max": [
        "Max Theta",
        "Spinbox",
        "float",
        {"from": 0, "to": 360, "step": 1},
        None,
        360,
    ],
    "f_min": [
        "Min Focus",
        "Spinbox",
        "float",
        {"from": -100000, "to": 100000, "step": 1000},
        None,
        -10000,
    ],
    "f_max": [
        "Max Focus",
        "Spinbox",
        "float",
        {"from": 0, "to": 100000, "step": 1000},
        None,
        10000,
    ],
    "x_offset": [
        "Offset of X",
        "Spinbox",
        "float",
        {"from": -10000, "to": 10000, "step": 1000},
        None,
        0,
    ],
    "y_offset": [
        "Offset of Y",
        "Spinbox",
        "float",
        {"from": -10000, "to": 10000, "step": 100},
        None,
        0,
    ],
    "z_offset": [
        "Offset of Z",
        "Spinbox",
        "float",
        {"from": -10000, "to": 10000, "step": 10},
        None,
        0,
    ],
    "theta_offset": [
        "Offset of Theta",
        "Spinbox",
        "float",
        {"from": 0, "to": 360, "step": 1},
        None,
        0,
    ],
    "f_offset": [
        "Offset of Focus",
        "Spinbox",
        "float",
        {"from": -10000, "to": 10000, "step": 10},
        None,
        0,
    ],
    "flip_x": ["Flip X", "Checkbutton", "bool", None, None],
    "flip_y": ["Flip Y", "Checkbutton", "bool", None, None],
    "flip_z": ["Flip Z", "Checkbutton", "bool", None, None],
    "flip_f": ["Flip F", "Checkbutton", "bool", None, None],
    "frame_config": {"collapsible": True, "title": "Stage Constants"},
}

remote_focus_device_types = {
    "Equipment Solutions": ("EquipmentSolutions", "equipment_solutions"),
    "Equipment Solutions ASI": ("EquipmentSolutionsASI", "equipment_solutions"),
    "Analog Device": ("NI", "ni"),
    "ASI Device": ("ASI", "asi"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

remote_focus_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", remote_focus_device_types, None],
    "channel": ["DAQ Channel", "Input", "string", None, "Example: PXI6259/ao3"],
    "axis": ["Device Type", "Input", "string", None, "Example: A"],
    "min": [
        "Minimum Voltage",
        "Spinbox",
        "float",
        {"from": -10, "to": 10, "step": 1},
        None,
    ],
    "max": [
        "Maximum Voltage",
        "Spinbox",
        "float",
        {"from": 0, "to": 10, "step": 1},
        None,
    ],
    "port": ["Serial Port", "Input", "string", None, "*Equipment Solutions only"],
    "baudrate": [
        "Baudrate",
        "Input",
        "int",
        None,
        "*Equipment Solutions only. Example: 9600",
    ],
    "frame_config": {"ref": "hardware"},
}

galvo_device_types = {
    "Analog Device": ("NI", "ni"),
    "ASI Device": ("ASI", "asi"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

waveform_types = {
    "Sine": "sine",
    "Sawtooth": "sawtooth",
    "Square": "square",
    "Pulse": "pulse",
}

galvo_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", galvo_device_types, None],
    "hardware/channel": [
        "DAQ Channel",
        "Input",
        "string",
        None,
        "*Analog Device only. Example: PXI6259/ao1",
    ],
    "hardware/axis": ["Axis", "Input", "string", None, "Example: A"],
    "hardware/min": [
        "Minimum Voltage",
        "Spinbox",
        "float",
        {"from": -10, "to": 10, "step": 0.1},
        None,
    ],
    "hardware/max": [
        "Maximum Voltage",
        "Spinbox",
        "float",
        {"from": 0, "to": 10, "step": 0.1},
        None,
    ],
    "waveform": ["Waveform", "Combobox", "string", waveform_types, None],
    "phase": [
        "Phase",
        "Spinbox",
        "float",
        {"from": 0, "to": 10, "step": 0.1},
        "Example: 1.57",
        0,
    ],
    "button_1": ["Delete", "Button", {"delete": True}],
    "frame_config": {
        "collapsible": True,
        "title": "Galvo Device",
        "ref": "None",
        "format": "list-dict",
    },
}

galvo_top_widgets = {
    "button_1": [
        "Add New Device",
        "Button",
        {"widgets": galvo_hardware_widgets, "parent": "hardware"},
    ],
}

zoom_device_types = {
    "Dynamixel": ("Dynamixel", "dynamixel"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

zoom_position_widgets = {
    "zoom_value": ["Zoom Value", "Input", "string", None, "Example: 16x"],
    "position": ["Position", "Input", "float", None, "Example: 1000"],
    "pixel_size": ["Pixel Size (um)", "Input", "float", None, "Example: 0.5"],
    "button_1": ["Delete", "Button", {"delete": True}],
    "frame_config": {
        "ref": "position;pixel_size",
        "format": "item(zoom_value, position);item(zoom_value, pixel_size)",
        "direction": "horizon",
    },
}

zoom_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", zoom_device_types, None],
    "servo_id": ["Servo ID", "Input", "string", None, "Example: 1"],
    "port": ["Serial Port", "Input", "string", None, "Example: COM1"],
    "baudrate": ["Baudrate", "Input", "int", None, "Example: 9600"],
    "button_1": [
        "Add Zoom Value",
        "Button",
        {
            "widgets": zoom_position_widgets,
            "ref": "position;pixel_size",
            "direction": "horizon",
            "parent": "constants",
        },
    ],
    "frame_config": {"ref": "hardware"},
}

mirror_device_types = {
    "Imagine Optics": ("ImagineOptics", "imop"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

mirror_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", mirror_device_types, None],
    "hardware/flat_path": [
        "Flat Mirror Path",
        "Input",
        "string",
        None,
        r"Example: D:\WaveKitX64\MirrorFiles\Beads.wcs",
    ],
    "n_modes": ["Number of Modes", "Input", "int", None, "Example: 32", 32],
}

laser_device_types = {
    "Analog Device": ("NI", "ni"),
    "ASI Laser": ("ASI", "asi"),
    "Virtual Device": ("Synthetic", "synthetic"),
}

laser_hardware_widgets = {
    "wavelength": ["Wavelength", "Input", "int", None, "Example: 488", 488],
    "onoff": ["On/Off Setting", "Label", None, None, None],
    "onoff/hardware/type": ["Type", "Combobox", "string", laser_device_types, None],
    "onoff/hardware/axis": ["Digital Axis", "Input", "string", None, "Example: 2"],
    "onoff/hardware/channel": [
        "DAQ Channel",
        "Input",
        "string",
        None,
        "Example: PXI6733/port0/line2",
    ],
    "onoff/hardware/min": [
        "Minimum Voltage",
        "Spinbox",
        "float",
        {"from": 0, "to": 100, "step": 1},
        None,
    ],
    "onoff/hardware/max": [
        "Maximum Voltage",
        "Spinbox",
        "float",
        {"from": 0, "to": 100, "step": 1},
        None,
    ],
    "power": ["Power Setting", "Label", None, None, None],
    "power/hardware/type": ["Type", "Combobox", "string", laser_device_types, None],
    "power/hardware/axis": ["Analog Axis", "Input", "string", None, "Example: B"],
    "power/hardware/channel": [
        "DAQ Channel",
        "Input",
        "string",
        None,
        "Example: PXI6733/ao0",
    ],
    "power/hardware/min": [
        "Minimum Voltage",
        "Spinbox",
        "float",
        {"from": 0, "to": 1000, "step": 1},
        None,
    ],
    "power/hardware/max": [
        "Maximum Voltage",
        "Spinbox",
        "float",
        {"from": 0, "to": 1000, "step": 1},
        None,
    ],
    "button_1": ["Delete", "Button", {"delete": True}],
    "frame_config": {
        "collapsible": True,
        "title": "Wavelength",
        "format": "list-dict",
        "ref": "None",
    },
}

laser_top_widgets = {
    "button_1": [
        "Add Wavelength",
        "Button",
        {"widgets": laser_hardware_widgets, "parent": "hardware"},
    ],
}

hardwares_dict = {
    "Camera": camera_hardware_widgets,
    "Data Acquisition Card": daq_hardware_widgets,
    "Filter Wheel": (None, filter_wheel_hardware_widgets, filter_wheel_widgets),
    "Galvo": (galvo_top_widgets, galvo_hardware_widgets, None),
    "Lasers": (laser_top_widgets, laser_hardware_widgets, None),
    "Remote Focus Devices": remote_focus_hardware_widgets,
    "Adaptive Optics": mirror_hardware_widgets,
    "Shutters": shutter_hardware_widgets,
    "Stages": (stage_top_widgets, stage_hardware_widgets, stage_constants_widgets),
    "Zoom Device": (None, zoom_hardware_widgets, zoom_position_widgets),
}

hardwares_config_name_dict = {
    "Camera": "camera",
    "Data Acquisition Card": "daq",
    "Filter Wheel": "filter_wheel",
    "Galvo": "galvo",
    "Lasers": "laser",
    "Remote Focus Devices": "remote_focus",
    "Adaptive Optics": "mirror",
    "Shutters": "shutter",
    "Stages": "stage",
    "Zoom Device": "zoom",
}

hardware_wizard_metadata = {
    "Camera": {
        "device_field": "hardware/type",
        "steps": [
            "Device Type",
            "Connection",
            "Timing",
            "Orientation",
            "Review",
        ],
        "fields": {
            "hardware/type": {
                "step": "Device Type",
                "importance": "required",
                "hint": "Choose the camera driver used by this microscope.",
                "help": "This selects the device adapter Navigate uses to connect to the camera.",
            },
            "hardware/serial_number": {
                "step": "Connection",
                "importance": "recommended",
                "hint": "Enter the camera serial number when the driver needs one.",
                "help": "Serial numbers help identify the intended camera on systems with more than one device.",
            },
            "hardware/camera_connection": {
                "step": "Connection",
                "importance": "advanced",
                "applies_to": ["Photometrics Iris 15B"],
                "hint": "Set the Photometrics Iris connection string.",
                "help": "Only Photometrics Iris 15B cameras use this connection value.",
            },
            "defect_correct_mode": {
                "step": "Timing",
                "importance": "recommended",
                "hint": "Choose whether camera defect correction is enabled.",
                "help": "Use the mode supported by the camera and acquisition workflow.",
            },
            "delay": {
                "step": "Timing",
                "importance": "recommended",
                "hint": "Set the camera trigger delay in milliseconds.",
                "help": "This delay offsets acquisition timing after the camera receives a trigger.",
            },
            "settle_down": {
                "step": "Timing",
                "importance": "advanced",
                "hint": "Add settling time after camera activity.",
                "help": "Use this when the camera or synchronization hardware needs extra time before the next action.",
            },
            "flip_x": {
                "step": "Orientation",
                "importance": "recommended",
                "hint": "Flip camera images along the X axis.",
                "help": "Enable this when the camera image is mirrored horizontally in Navigate.",
            },
            "flip_y": {
                "step": "Orientation",
                "importance": "recommended",
                "hint": "Flip camera images along the Y axis.",
                "help": "Enable this when the camera image is mirrored vertically in Navigate.",
            },
            "supported_channel_count": {
                "step": "Review",
                "importance": "recommended",
                "hint": "Set the number of microscope channels this camera supports.",
                "help": "Use the configured microscope channel count so channel setup matches the camera.",
            },
        },
    },
    "Data Acquisition Card": {
        "device_field": "hardware/type",
        "steps": [
            "Device Type",
            "Timing",
            "Triggering",
            "Laser Switching",
            "Review",
        ],
        "fields": {
            "hardware/type": {
                "step": "Device Type",
                "importance": "required",
                "hint": "Choose the DAQ hardware family.",
                "help": "This selects the adapter Navigate uses for acquisition timing and triggers.",
            },
            "sample_rate": {
                "step": "Timing",
                "importance": "required",
                "hint": "Set the DAQ sample rate in samples per second.",
                "help": "The sample rate controls waveform timing for synchronized acquisition.",
            },
            "trigger_reset_count": {
                "step": "Timing",
                "importance": "advanced",
                "hint": "Set the trigger reset interval, or leave 0 to disable it.",
                "help": "Use a positive value only for systems that need periodic trigger reset handling.",
            },
            "master_trigger_out_line": {
                "step": "Triggering",
                "importance": "recommended",
                "applies_to": ["National Instruments"],
                "hint": "Enter the NI line used for the master trigger output.",
                "help": "This route distributes the master trigger to synchronized devices.",
            },
            "camera_trigger_out_line": {
                "step": "Triggering",
                "importance": "recommended",
                "applies_to": ["National Instruments"],
                "hint": "Enter the NI counter or line used to trigger the camera.",
                "help": "This output line sends acquisition triggers from the DAQ to the camera.",
            },
            "trigger_source": {
                "step": "Triggering",
                "importance": "recommended",
                "applies_to": ["National Instruments"],
                "hint": "Enter the NI input source used for external triggers.",
                "help": "Use this when acquisition timing starts from an external trigger source.",
            },
            "laser_port_switcher": {
                "step": "Laser Switching",
                "importance": "advanced",
                "applies_to": ["National Instruments"],
                "hint": "Enter the NI digital port used for laser switching.",
                "help": "This port controls digital laser state switching during acquisition.",
            },
            "laser_switch_state": {
                "step": "Laser Switching",
                "importance": "advanced",
                "applies_to": ["National Instruments"],
                "hint": "Choose the digital state that turns the laser switch on.",
                "help": "Match this value to the active-high or active-low wiring of the laser switch.",
            },
        },
    },
    "Filter Wheel": {"steps": ["Details"], "fields": {}},
    "Galvo": {"steps": ["Details"], "fields": {}},
    "Lasers": {"steps": ["Details"], "fields": {}},
    "Remote Focus Devices": {"steps": ["Details"], "fields": {}},
    "Adaptive Optics": {"steps": ["Details"], "fields": {}},
    "Shutters": {"steps": ["Details"], "fields": {}},
    "Stages": {
        "device_field": "type",
        "steps": [
            "Device Type",
            "Axes",
            "Motion Limits",
            "Controller Settings",
            "Advanced",
            "Review",
        ],
        "fields": {
            "type": {
                "step": "Device Type",
                "importance": "required",
                "hint": "Choose the stage controller or device family.",
                "help": "This selects the stage adapter Navigate uses for motion control.",
            },
            "serial_number": {
                "step": "Controller Settings",
                "importance": "recommended",
                "hint": "Enter the stage serial number when required by the controller.",
                "help": "Serial numbers help identify the correct controller on multi-device systems.",
            },
            "axes": {
                "step": "Axes",
                "importance": "required",
                "hint": "List the logical axes provided by this stage.",
                "help": "Use the axis names Navigate should expose, such as x, y, z, theta, or f.",
            },
            "axes_mapping": {
                "step": "Axes",
                "importance": "recommended",
                "hint": "Map Navigate axes to controller-specific axis names.",
                "help": "Use this when controller axis labels differ from Navigate's logical axes.",
            },
            "feedback_alignment": {
                "step": "Axes",
                "importance": "advanced",
                "applies_to": [
                    "Applied Scientific Instrumentation",
                    "ASI MFC2000",
                    "ASI MS2000",
                ],
                "hint": "Set ASI feedback alignment values for each axis.",
                "help": "These values align ASI controller feedback with Navigate's axis definitions.",
            },
            "device_units_per_mm": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["ThorLabs KCube Inertial Device KST101"],
                "hint": "Set the KST101 conversion from millimeters to device units.",
                "help": "Use the controller calibration value so commanded motion matches physical travel.",
            },
            "volts_per_micron": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Enter the NI analog voltage expression per micron.",
                "help": "This expression converts requested stage position into analog output voltage.",
            },
            "min": {
                "step": "Motion Limits",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Set the minimum analog output voltage.",
                "help": "This lower limit protects NI-controlled stages from invalid voltage commands.",
            },
            "max": {
                "step": "Motion Limits",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Set the maximum analog output voltage.",
                "help": "This upper limit protects NI-controlled stages from invalid voltage commands.",
            },
            "distance_threshold": {
                "step": "Motion Limits",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Set the motion distance threshold for analog-controlled stages.",
                "help": "Navigate uses this threshold when deciding how to handle analog stage moves.",
            },
            "settle_duration_ms": {
                "step": "Motion Limits",
                "importance": "advanced",
                "applies_to": ["NI Analog/Digital Device"],
                "hint": "Set the analog stage settling duration in milliseconds.",
                "help": "Use this to wait for the stage signal to settle after movement.",
            },
            "controllername": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["Physik Instrumente"],
                "hint": "Enter the Physik Instrumente controller model name.",
                "help": "This identifies the PI controller used for stage communication.",
            },
            "stages": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["Physik Instrumente"],
                "hint": "List the Physik Instrumente stage model names.",
                "help": "Use the PI stage names connected to the configured controller axes.",
            },
            "refmode": {
                "step": "Controller Settings",
                "importance": "advanced",
                "applies_to": ["Physik Instrumente"],
                "hint": "List the PI reference modes for the configured stages.",
                "help": "Reference modes tell the PI controller how each stage should home or reference.",
            },
            "port": {
                "step": "Controller Settings",
                "importance": "recommended",
                "hint": "Enter the serial port used by the stage controller.",
                "help": "Use the COM or device path assigned to the controller by the operating system.",
            },
            "baudrate": {
                "step": "Controller Settings",
                "importance": "recommended",
                "hint": "Enter the serial baudrate for the stage controller.",
                "help": "Match this value to the controller's configured serial communication speed.",
            },
            "timeout": {
                "step": "Controller Settings",
                "importance": "recommended",
                "hint": "Set the serial timeout in seconds.",
                "help": "Use a timeout long enough for the controller to respond without slowing failures.",
            },
        },
    },
    "Zoom Device": {"steps": ["Details"], "fields": {}},
}

deceased_device_type_names = {
    "ASIMS2000": "MS2000",
    "ASIMFC2000": "MFC2000",
    "GalvoNIStage": "NI",
    "Thorlabs": "KIM001",
}
