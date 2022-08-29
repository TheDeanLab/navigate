def test_data_source_mode():
    from aslm.model.model_features.data_sources.data_source import DataSource

    ds = DataSource()

    # set read and write
    ds.mode = 'r'
    assert(ds.mode =='r')

    ds.mode = 'w'
    assert(ds.mode == 'w')

    # set unknown mode, default to read
    ds.mode = 'goblin'
    assert(ds.mode=='r')
