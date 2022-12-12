from aslm.model.features.common_features import ZStackAcquisition

def test_z_stack(dummy_model_to_test_features):
    model = dummy_model_to_test_features
    feature_list = [[{'name': ZStackAcquisition}]]
    
    model.start(feature_list)

