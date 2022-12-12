from aslm.model.features.common_features import ZStackAcquisition

def test_z_stack(dummy_model_to_test_features):
    model = dummy_model_to_test_features
    feature_list = [[{'name': ZStackAcquisition}]]
    
    config = model.configuration['experiment']['MicroscopeState']
    # 1 channel
    config['channels']['channel_1']['is_selected'] = True
    config['channels']['channel_2']['is_selected'] = False
    config['channels']['channel_3']['is_selected'] = False
    
    
    config['start_position'] = 0
    config['end_position'] = 200
    config['number_z_steps'] = 10
    config['step_size'] = (config['end_position'] - config['start_position']) / config['number_z_steps']
    model.start(feature_list)

    print(model.signal_records)

