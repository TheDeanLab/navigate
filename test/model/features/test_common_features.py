from aslm.model.features.common_features import ZStackAcquisition

def test_z_stack(dummy_model_to_test_features):
    model = dummy_model_to_test_features
    config = model.configuration['experiment']['MicroscopeState']
    idx, record_num = 0, len(model.signal_records)

    def get_next_record(record_prefix, idx):
        global record_num
        while model.signal_records[idx][0] != record_prefix:
            idx += 1
            if idx >= record_num:
                assert False, 'Some device movements are missed!'
        return idx

    def z_stack_verification():
        mode = config['stack_cycling_mode'] # per_z/pre_stack
        is_multiposition = config['is_multiposition']
        if is_multiposition:
            positions = model.configuration['experiment']['MultiPositions']['stage_positions']
        else:
            positions = [model.configuration['StageParameters']]

        z_step = config['step_size']
        f_step = (config['end_focus'] - config['start_focus']) / config['number_z_steps']

        for i, pos in enumerate(positions):
            
            idx = get_next_record('move_stage', idx)
            
            # x, y, theta
            pos_moved = model.signal_records[idx][1][0]
            for axis in ['x', 'y', 'theta']:
                assert pos[axis] == pos_moved[axis], f"should move to x: {pos[axis]}, but moved to {pos_moved[axis]}"

            z_pos = pos['z'] + config['start_position']
            f_pos = pos['f'] + config['start_focus']

            if mode == 'per_z':
                for j in config['number_z_steps']:
                    idx = get_next_record('move_stage', idx+1)

                    pos_moved = model.signal_records[idx][1][0]
                    for axis in ['z', 'f']:
                        assert pos_moved[axis] == z_pos + j * z_step, f"should move to z: {z_pos + j * z_step}, but moved to {pos_moved[axis]}"

                        # channel
            else: # per_stack
                pass


            
                
                


    feature_list = [[{'name': ZStackAcquisition}]]
    
    # 1 channel
    config['channels']['channel_1']['is_selected'] = True
    config['channels']['channel_2']['is_selected'] = True
    config['channels']['channel_3']['is_selected'] = False
    model.target_channel = 1
        
    config['start_position'] = 0
    config['end_position'] = 200
    config['number_z_steps'] = 10
    config['step_size'] = (config['end_position'] - config['start_position']) / config['number_z_steps']
    
    model.start(feature_list)

    print(model.signal_records)

