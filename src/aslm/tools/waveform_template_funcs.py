def get_waveform_template_parameters(waveform_template_name, waveform_template_dict, microscope_state_dict):
    waveform_template = waveform_template_dict[waveform_template_name]
    try:
        if type(waveform_template["repeat"]) is int:
            repeat_num = waveform_template["repeat"]
        else:
            repeat_num = int(microscope_state_dict[waveform_template["repeat"]])
    except:
        repeat_num = 1

    try:
        if type(waveform_template["expand"]) is int:
            expand_num = waveform_template["expand"]
        else:
            expand_num = int(microscope_state_dict[waveform_template["expand"]])
    except:
        expand_num = 1

    return repeat_num, expand_num