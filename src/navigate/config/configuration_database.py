camera_device_types = {
    "Hamamatsu ORCA Lightning": "HamamatsuOrcaLightning",
    "Hamamatsu ORCA Fire": "HamamatsuOrcaFire",
    "Hamamatsu ORCA Fusion": "HamamatsuOrcaFusion",
    "Hamamatsu Flash 4.0": "HamamatsuOrca",
    "Photometrics Iris 15B": "Photometrics",
    "Virtual Device": "synthetic",
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
    "delay": ["Delay (ms)", "Spinbox", "float", None, None],
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
    "Sutter Instruments": "SutterFilterWheel",
    "Applied Scientific Instrumentation": "ASI",
    "Virtual Device": "synthetic",
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
        },
    ],
}

daq_device_types = {
    "National Instruments": "NI",
    "Virtual Device": "synthetic",
}

daq_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", daq_device_types, None],
    "sample_rate": ["Sample Rate", "Input", "int", None, "Example: 100000"],
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
    "Analog/Digital Device": "NI",
    "Virtual Device": "synthetic",
}

shutter_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", shutter_device_types, None],
    "channel": ["NI Channel", "Input", "string", None, "Example: PXI6259/port0/line0"],
    "min": ["Minimum Voltage", "Spinbox", "float", None, "Example: 0"],
    "max": ["Maximum Voltage", "Spinbox", "float", None, "Example: 5"],
    "frame_config": {"ref": "hardware"},
}

stage_device_types = {
    "Applied Scientific Instrumentation": "ASI",
    "ASI MFC2000": "MFC2000",
    "ASI MS2000": "MS2000",
    "Analog/Digital Device": "GalvoNIStage",
    "Mad City Labs": "MCL",
    "Physik Instrumente": "PI",
    "Sutter Instruments": "MP285",
    "ThorLabs KCube Inertial Device KIM001": "Thorlabs",
    "ThorLabs KCube Inertial Device KST101": "KST101",
    "Virtual Device": "synthetic",
}

stage_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", stage_device_types, None],
    "serial_number": ["Serial Number", "Input", "string", None, None],
    "axes": ["Axes", "Input", "string", None,"Example: [x, y, z, theta, f]", "[x, y, z]"],
    "axes_mapping": ["Axes Mapping", "Input", "string", None, "Example: [X, M, Y, D, E]", "[X, M, Y]"],
    "feedback_alignment": ["Feedback Alighment", "Input", "string", None, "*ASI stage only. Example: [90, 90, 90, 0, 90]", "[90, 90, 90]"],
    "device_units_per_mm": ["Device Units Per Micron", "Input", "float", None, "*KST101 only. Example: 2000.0", 1000.25],
    "volts_per_micron": [
        "Volts Per Micron",
        "Input",
        "string",
        None,
        "*Analog/Digital Device only. Example: '0.1*x+0.05'",
        "0.1*x+0.05"
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
        5
    ],
    "settle_duration_ms": [
        "Settle Duration (ms)",
        "Spinbox",
        "float",
        {"from": 0, "to": 100, "step": 1},
        "*Analog-Controlled Galvo/Peizo only",
        20
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
    "joystick_axes": ["Joystick Axes", "Input", "string", None, "Example: [x, y, z]", "[x, y, z]"],
    "x_min": [
        "Min X",
        "Spinbox",
        "float",
        {"from": -100000, "to": 100000, "step": 1000},
        None,
        -10000
    ],
    "x_max": [
        "Max X",
        "Spinbox",
        "float",
        {"from": 0, "to": 100000, "step": 1000},
        None,
        10000
    ],
    "y_min": [
        "Min Y",
        "Spinbox",
        "float",
        {"from": -100000, "to": 100000, "step": 1000},
        None,
        -10000
    ],
    "y_max": [
        "Max Y",
        "Spinbox",
        "float",
        {"from": 0, "to": 100000, "step": 1000},
        None,
        10000
    ],
    "z_min": [
        "Min Z",
        "Spinbox",
        "float",
        {"from": -100000, "to": 10000, "step": 1000},
        None,
        -10000
    ],
    "z_max": [
        "Max Z",
        "Spinbox",
        "float",
        {"from": 0, "to": 100000, "step": 1000},
        None,
        10000
    ],
    "theta_min": [
        "Min Theta",
        "Spinbox",
        "float",
        {"from": 0, "to": 360, "step": 1},
        None,
        0
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
    "Equipment Solutions": "EquipmentSolutions",
    "Analog Device": "NI",
    "Virtual Device": "synthetic",
}

remote_focus_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", remote_focus_device_types, None],
    "channel": ["DAQ Channel", "Input", "string", None, "Example: PXI6259/ao3"],
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
    "comport": ["Serial Port", "Input", "string", None, "*Equipment Solutions only"],
    "baudrate": [
        "Baudrate",
        "Input",
        "int",
        None,
        "*Equipment Solutions only. Example: 9600",
    ],
    "frame_config": {"ref": "hardware"},
}

galvo_device_types = {"Analog Device": "NI", "Virtual Device": "synthetic"}

waveform_types = {
    "Sine": "sine",
    "Sawtooth": "sawtooth",
    "Square": "square",
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
        0
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

zoom_device_types = {"Dynamixel": "DynamixelZoom", "Virtual Device": "synthetic"}

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
        },
    ],
    "frame_config": {"ref": "hardware"},
}

mirror_device_types = {
    "Imagine Optics": "ImagineOpticsMirror",
    "Virtual Device": "SyntheticMirror",
}

mirror_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", mirror_device_types, None],
    "flat_path": [
        "Flat Mirror Path",
        "Input",
        "string",
        None,
        "Example: D:\WaveKitX64\MirrorFiles\Beads.wcs",
    ],
    "n_modes": ["Number of Modes", "Input", "int", None, None, "Example: 32"],
    "frame_config": {"ref": "hardware"},
}

laser_device_types = {"Analog Device": "NI", "Virtual Device": "synthetic"}

laser_hardware_widgets = {
    "wavelength": ["Wavelength", "Input", "int", None, None, "Example: 488"],
    "onoff": ["On/Off Setting", "Label", None, None, None],
    "onoff/hardware/type": ["Type", "Combobox", "string", laser_device_types, None],
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
        {"from": 0, "to": 100, "step": 1},
        None,
    ],
    "power/hardware/max": [
        "Maximum Voltage",
        "Spinbox",
        "float",
        {"from": 0, "to": 100, "step": 1},
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
    "Lasers": "lasers",
    "Remote Focus Devices": "remote_focus_device",
    "Adaptive Optics": "mirror",
    "Shutters": "shutter",
    "Stages": "stage",
    "Zoom Device": "zoom",
}
