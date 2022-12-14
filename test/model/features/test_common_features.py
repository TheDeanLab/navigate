from aslm.model.features.common_features import ZStackAcquisition

def test_z_stack(dummy_model_to_test_features):
    model = dummy_model_to_test_features
    record_num = len(model.signal_records)
    config = model.configuration['experiment']['MicroscopeState']

    def get_next_record(record_prefix, idx):
        global record_num
        idx += 1
        while model.signal_records[idx][0] != record_prefix:
            idx += 1
            if idx >= record_num:
                assert False, 'Some device movements are missed!'
        return idx

    def z_stack_verification():
        global record_num
        record_num = len(model.signal_records)
        # save all the selected channels
        selected_channels = []
        for channel_key in config['channels'].keys():
            if config['channels'][channel_key]['is_selected']:
                selected_channels.append(dict(config['channels'][channel_key]))
                selected_channels[-1]['id'] = int(channel_key[len('channel_'):])

        mode = config['stack_cycling_mode'] # per_z/pre_stack
        is_multiposition = config['is_multiposition']
        if is_multiposition:
            positions = model.configuration['experiment']['MultiPositions']['stage_positions']
        else:
            pos_dict = model.configuration['experiment']['StageParameters']
            positions = [{'x': pos_dict['x'],
                          'y': pos_dict['y'],
                          'z': config.get('stack_z_origin', pos_dict['z']),
                          'theta': pos_dict['theta'],
                          'f': config.get('stack_focus_origin', pos_dict['f'])
                        }]

        z_step = config['step_size']
        f_step = (config['end_focus'] - config['start_focus']) / config['number_z_steps']

        frame_id = 0
        idx = -1

        for i, pos in enumerate(positions):
            
            idx = get_next_record('move_stage', idx)
            
            # x, y, theta
            pos_moved = model.signal_records[idx][1][0]
            for axis in ['x', 'y', 'theta']:
                assert pos[axis] == pos_moved[axis+'_abs'], f"should move to {axis}: {pos[axis]}, but moved to {pos_moved[axis+'_abs']}"

            z_pos = pos['z'] + config['start_position']
            f_pos = pos['f'] + config['start_focus']

            if mode == 'per_z':
                for j in range(config['number_z_steps']):
                    idx = get_next_record('move_stage', idx)

                    pos_moved = model.signal_records[idx][1][0]
                    # z, f
                    assert pos_moved['z_abs'] == z_pos + j * z_step, f"should move to z: {z_pos + j * z_step}, but moved to {pos_moved['z_abs']}"
                    assert pos_moved['f_abs'] == f_pos + j * f_step, f"should move to z: {f_pos + j * f_step}, but moved to {pos_moved['f_abs']}"

                    # channel
                    for k in range(len(selected_channels)):
                        idx = get_next_record('change_channel', idx)
                        c = selected_channels[(k+1) % len(selected_channels)]['id']
                        assert model.signal_records[idx][1][0] == c, f"{frame_id} should change to channel {c}, but it's {model.signal_records[idx][1][0]}"
                        assert model.signal_records[idx][2]['frame_id'] == frame_id
                        frame_id += 1

            else: # per_stack
                for k in range(len(selected_channels)):
                    # z
                    for j in range(config['number_z_steps']):
                        idx = get_next_record('move_stage', idx)

                        pos_moved = model.signal_records[idx][1][0]
                        # z, f
                        assert pos_moved['z_abs'] == z_pos + j * z_step, f"should move to z: {z_pos + j * z_step}, but moved to {pos_moved['z_abs']}"
                        assert pos_moved['f_abs'] == f_pos + j * f_step, f"should move to z: {f_pos + j * f_step}, but moved to {pos_moved['f_abs']}"
                        frame_id += 1

                    idx = get_next_record('change_channel', idx)
                    c = selected_channels[(k+1) % len(selected_channels)]['id']
                    assert model.signal_records[idx][1][0] == c, f"{frame_id} should change to channel {c}, but it's {model.signal_records[idx][1][0]}"
                    assert model.signal_records[idx][2]['frame_id'] == frame_id-1
                        


    feature_list = [[{'name': ZStackAcquisition}]]
        
    config['start_position'] = 0
    config['end_position'] = 200
    config['number_z_steps'] = 10
    config['step_size'] = (config['end_position'] - config['start_position']) / config['number_z_steps']
    
    config['is_multiposition'] = False
    
    # 1 channel per_stack
    config['stack_cycling_mode'] = 'per_stack'
    config['channels']['channel_1']['is_selected'] = True
    config['channels']['channel_2']['is_selected'] = False
    config['channels']['channel_3']['is_selected'] = False
    model.start(feature_list)
    print(model.signal_records)
    z_stack_verification()

    # 1 channel per_z
    config['stack_cycling_mode'] = 'per_z'
    model.start(feature_list)
    z_stack_verification()

    # 2 channels per_stack
    config['stack_cycling_mode'] = 'per_stack'
    for i in range(3):
        for j in range(3):
            config['channels']['channel_'+str(j+1)]['is_selected'] = True
        config['channels']['channel_'+str(i+1)]['is_selected'] = False
        model.start(feature_list)
        z_stack_verification()

    # 2 channels per_z
    config['stack_cycling_mode'] = 'per_z'
    for i in range(3):
        for j in range(3):
            config['channels']['channel_'+str(j+1)]['is_selected'] = True
        config['channels']['channel_'+str(i+1)]['is_selected'] = False
        model.start(feature_list)
        z_stack_verification()

    config['is_multiposition'] = True
    model.configuration['experiment']['MultiPositions']['stage_positions']