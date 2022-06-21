from aslm.model.model_features.aslm_image_writer import ImageWriter
from pathlib import Path
from aslm.model.aslm_model_config import Session as session


# Set up the model, experiment, ETL dictionaries
base_directory = Path(__file__).resolve().parent.parent.parent.parent
configuration_directory = Path.joinpath(base_directory, 'src', 'config')

config = session(Path.joinpath(configuration_directory, 'configuration.yml'))
experiment = session(Path.joinpath(configuration_directory, 'experiment.yml'))
etl_constants = session(Path.joinpath(configuration_directory, 'etl_constants.yml'))


class TestImageWriter:

    def test_zarr_byslice():
        from aslm.model.aslm_model import Model
        # model = Model()
        # slicetest = ImageWriter()

    
    def test_zarr_bymultislice():
        pass


    def test_zarr_bystack():
        pass

    def test_zarr_bymultistack():
        pass