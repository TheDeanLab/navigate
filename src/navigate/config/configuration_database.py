camera_device_types = {
    "Hamamatsu ORCA Lightning": "HamamatsuOrcaLightning",
    "Hamamatsu ORCA Fire": "HamamatsuOrcaFire",
    "Hamamatsu Flash 4.0": "HamamatsuOrca",
    "Photometrics Iris 15B": "Photometrics",
    "Virtual Device": "synthetic"
}

camera_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", camera_device_types],
    "hardware/serial_number": ["Serial Number", "Input", "string", None],
    "defect_correct_mode": ["Defect Correct Mode", "Combobox", "string", {"On": 2.0, "Off": 1.0}],
    "delay": ["Delay (ms)", "Spinbox", "float", None],
    "flip_x": ["Flip X", "Checkbutton", "bool", None],
    "flip_y": ["Flip Y", "Checkbutton", "bool", None],
}

filter_wheel_device_types = {
    "Sutter Instruments": "SutterFilterWheel",
    "Applied Scientific Instrumentation": "ASI",
    "Virtual Device": "synthetic",
}

filter_wheel_widgets = {
    "filter_name": ["Filter Name", "Input", "string", None],
    "filter_value": ["Filter Value", "Input", "string", None],
    "button_1": ["Delete", "Button", {"delete": True}],
    "frame_config": {"format": "item(filter_name,filter_value)"}
}

filter_wheel_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", filter_wheel_device_types,],
    "hardware/wheel_number": ["Number of Wheels", "Spinbox", "int", None],
    "hardware/port": ["Serial Port", "Input", "string", None],
    "hardware/baudrate": ["Baudrate", "Input", "int", None],
    "filter_wheel_delay": ["Filter Wheel Delay (s)", "Input", "float", None],
    "button_1": ["Add Available Filters", "Button", {"widgets":filter_wheel_widgets, "ref": "available_filters", "direction": "horizon"}]
}

daq_device_types = {
    "National Instruments": "NI",
}

daq_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", daq_device_types,],
    "sample_rate": ["Sample Rate", "Input", "int", None],
    "master_trigger_out_line": ["Master Trigger Out", "Input", "string", None],
    "camera_trigger_out_line": ["Camera Trigger Out", "Input", "string", None],
    "trigger_source": ["Trigger Source", "Input", "string", None],
    "laser_port_switcher": ["Laser Switcher Port", "Input", "string", None],
    "laser_switch_state": ["Laser Switch On State", "Combobox", "bool", [True, False]],
}

shutter_device_types = {
    "Analog/Digital Device": "NI",
    "Virtual Device": "synthetic",
}

shutter_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", shutter_device_types,],
    "channel": ["NI Channel", "Input", "string", None],
    "min": ["Minimum Voltage", "Spinbox", "float", None],
    "max": ["Maximum Voltage", "Spinbox", "float", None],
    "frame_config": {"ref": "hardware"}
}

stage_device_types = {
    "Applied Scientific Instrumentation": "ASI",
    "Analog/Digital Device": "GalvoNIStage",
    "Mad City Labs": "MCL",
    "Physik Instrumente": "PI",
    "Sutter Instruments": "MP285",
    "ThorLabs KCube Inertial Device": "Thorlabs",
    "Virtual Device": "synthetic",
}

stage_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", stage_device_types,],
    "serial_number": ["Serial Number", "Input", "string", None],
    "axes": ["Axes", "Input", "string", None,],
    "axes_mapping": ["Axes Mapping", "Input", "string", None],
    "volts_per_micron": ["Volts Per Micron", "Spinbox", "float", {"from": 0, "to": 100, "step":0.1}, ("type", "GalvoNIStage")],
    "min": ["Minimum Volts", "Spinbox", "float", {"from": 0, "to": 5, "step": 0.1}, ("type", "GalvoNIStage")],
    "max": ["Maximum Volts", "Spinbox", "float", {"from": 1, "to": 100, "step": 0.1}, ("type", "GalvoNIStage")],
    "controllername": ["Controller Name", "Input", "string", None, ("type", "PI")],
    "stages": ["PI Stages", "Input", "string", None, ("type", "PI")],
    "refmode": ["REF Modes", "Input", "string", None, ("type", "PI")],
    "port": ["Serial Port", "Input", "string", None],
    "baudrate": ["Baudrate", "Input", "int", None],
    "button_2": ["Delete", "Button", {"delete": True}],
    "frame_config": {"collapsible": True, "title": "Stage", "ref": "hardware", "format": "list-dict"}
}

stage_top_widgets = {
    "button_1": ["Add New Stage Device", "Button", {"widgets": stage_hardware_widgets, "ref": "hardware", "parent": "hardware"}],
}

stage_constants_widgets = {
    "x_min": ["Min X", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "x_max": ["Max X", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "y_min": ["Min Y", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "y_max": ["Max Y", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "z_min": ["Min Z", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "z_max": ["Max Z", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "theta_min": ["Min Theta", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "theta_max": ["Max Theta", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "f_min": ["Min Focus", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "f_max": ["Max Focus", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "x_offset": ["Offset of X", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "y_offset": ["Offset of Y", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "z_offset": ["Offset of Z", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "theta_offset": ["Offset of Theta", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "f_offset": ["Offset of Focus", "Spinbox", "float", {"from": -100000, "to": 10000, "step": 1000}],
    "frame_config": {"collapsible": True, "title": "Stage Constants"}
}

remote_focus_device_types = {
    "Equipment Solutions": "EquipmentSolutions",
    "Analog Device": "NI",
    "Virtual Device": "synthetic"
}

remote_focus_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", remote_focus_device_types],
    "channel": ["DAQ Channel", "Input", "string", None],
    "min": ["Minimum Voltage", "Spinbox", "float", {"from": 0, "to": 10, "step": 0.1}],
    "max": ["Maximum Voltage", "Spinbox", "float", {"from": 0, "to": 10, "step": 0.1}],
    "comport": ["Serial Port", "Input", "string", None],
    "baudrate": ["Baudrate", "Input", "int", None],
    "frame_config": {"ref": "hardware"}
}

galvo_device_types = {
    "Analog Device": "NI",
    "Virtual Device": "synthetic"
}

waveform_types = {
    "Sine": "sine",
    "Sawtooth": "sawtooth",
    "Square": "square",
}

galvo_hardware_widgets = {
    "hardware/type": ["Device Type", "Combobox", "string", galvo_device_types],
    "hardware/channel": ["DAQ Channel", "Input", "string", None],
    "hardware/min": ["Minimum Voltage", "Spinbox", "float", {"from": 0, "to": 10, "step": 0.1}],
    "hardware/max": ["Maximum Voltage", "Spinbox", "float", {"from": 0, "to": 10, "step": 0.1}],
    "waveform": ["Waveform", "Combobox", "string", waveform_types],
    "phase": ["Phase", "Input", "string", None],
    "button_1": ["Delete", "Button", {"delete": True}],
    "frame_config": {"collapsible": True, "title": "Galvo Device", "ref": "None", "format": "list-dict"}
}

galvo_top_widgets = {
    "button_1": ["Add New Device", "Button", {"widgets": galvo_hardware_widgets, "parent": "hardware"}],
}

zoom_device_types = {
    "Dynamixel": "DynamixelZoom",
    "Virtual Device": "synthetic"
}

zoom_position_widgets = {
    "zoom_value": ["Zoom Value", "Input", "string", None],
    "position": ["Position", "Input", "float", None],
    "pixel_size": ["Pixel Size (um)", "Input", "float", None],
    "button_1": ["Delete", "Button", {"delete": True}],
    "frame_config": {"ref": "position;pixel_size", "format": "item(zoom_value, position);item(zoom_value, pixel_size)"}
}

zoom_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", zoom_device_types,],
    "servo_id": ["Servo ID", "Input", "string", None],
    "button_1": ["Add Zoom Value", "Button", {"widgets":zoom_position_widgets, "ref": "position;pixel_size", "direction": "horizon"}]
}

mirror_device_types = {
    "Imagine Optics": "ImagineOpticsMirror",
    "Virtual Device": "SyntheticMirror"
}

mirror_hardware_widgets = {
    "type": ["Device Type", "Combobox", "string", mirror_device_types,],
    "frame_config": {"ref": "hardware"}
}

laser_device_types = {
    "Analog Device": "NI",
    "Virtual Device": "synthetic"
}

laser_hardware_widgets = {
    "wavelength": ["Wavelength", "Input", "int", None],
    "onoff": ["On/Off Setting", "Label", None, None],
    "onoff/hardware/type": ["Type", "Combobox", "string", laser_device_types],
    "onoff/hardware/channel": ["DAQ Channel", "Input", "string", None],
    "onoff/hardware/min": ["Minimum Voltage", "Spinbox", "float", {"from": 0, "to": 100, "step": 1}],
    "onoff/hardware/max": ["Maximum Voltage", "Spinbox", "float", {"from": 0, "to": 100, "step": 1}],
    "power": ["Power Setting", "Label", None, None],
    "power/hardware/type": ["Type", "Combobox", "string", laser_device_types],
    "power/hardware/channel": ["DAQ Channel", "Input", "string", None],
    "power/hardware/min": ["Minimum Voltage", "Spinbox", "float", {"from": 0, "to": 100, "step": 1}],
    "power/hardware/max": ["Maximum Voltage", "Spinbox", "float", {"from": 0, "to": 100, "step": 1}],
    "button_1": ["Delete", "Button", {"delete": True}],
    "frame_config": {"collapsible": True, "title": "Wavelength"}
}

laser_top_widgets = {
    "button_1": ["Add Wavelength", "Button", {"widgets": laser_hardware_widgets, "ref": "", "parent": "hardware"}],
}

hardwares_dict = {
    "Camera": camera_hardware_widgets,
    "Data Acquisition Card": daq_hardware_widgets,
    "Filter Wheel": filter_wheel_hardware_widgets,
    "Galvo": (galvo_top_widgets, galvo_hardware_widgets, None),
    "Lasers": (laser_top_widgets, laser_hardware_widgets, None),
    "Remote Focus Devices": remote_focus_hardware_widgets,
    "Adaptive Optics": mirror_hardware_widgets,
    "Shutters": shutter_hardware_widgets,
    "Stages": (stage_top_widgets, stage_hardware_widgets, stage_constants_widgets),
    "Zoom Device": zoom_hardware_widgets
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