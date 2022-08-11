#  Standard Imports
import logging
from typing import Optional, Tuple

# Local Imports
from aslm.tools import xml_tools
from aslm.model.aslm_model_config import Configurator

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)

class Metadata:
    def __init__(self) -> None:
        """
        Store and convert internal representation of metadata (configuration, experiment, etc.)
        to alternative file types.

        Concept and some of the code borrowed from python-microscopy
        (https://github.com/python-microscopy/python-microscopy/).
        """
        self._configuration = None
        self._experiment = None
        self.dx, self.dy, self.dz = 1, 1, 1  # pixel sizes (um)
        self.dt = 1                          # time displacement (s)
        self.dc = 1                          # step size between channels, should always be 1
        self._order = 'XYCZT'
        self._per_stack = True

        # shape
        self.shape_x, self.shape_y, self.shape_z, self.shape_t, self.shape_c = 1, 1, 1, 1, 1

    @property
    def configuration(self) -> Optional[Configurator]:
        return self._configuration

    @configuration.setter
    def configuration(self, configuration: Configurator) -> None:
        self._configuration = configuration
        self.set_from_configuration_experiment()

    @property
    def experiment(self) -> Optional[Configurator]:
        return self._experiment

    @experiment.setter
    def experiment(self, experiment: Configurator) -> None:
        self._experiment = experiment
        self.set_from_configuration_experiment()

    @property
    def per_stack(self) -> bool:
        return self._per_stack

    def set_from_configuration_experiment(self) -> None:
        if self.experiment is not None and self.configuration is not None:
            self.set_shape_from_configuration_experiment()
            self.set_stack_order_from_configuration_experiment()

    def set_shape_from_configuration_experiment(self) -> None:
        zoom = self.experiment.MicroscopeState['zoom']
        if self.experiment.MicroscopeState['resolution_mode'] == 'low':
            pixel_size = float(self.configuration.ZoomParameters['low_res_zoom_pixel_size'][zoom])
        else:
            pixel_size = float(self.configuration.ZoomParameters['high_res_zoom_pixel_size'])
        self.dx, self.dy = pixel_size, pixel_size
        self.dz = float(self.experiment.MicroscopeState['step_size'])
        self.dt = float(self.experiment.MicroscopeState['timepoint_interval'])

        self.shape_x = int(self.experiment.CameraParameters['x_pixels'])
        self.shape_y = int(self.experiment.CameraParameters['y_pixels'])
        self.shape_z = int(self.experiment.MicroscopeState['number_z_steps'])
        self.shape_t = int(self.experiment.MicroscopeState['timepoints'])
        self.shape_c = sum([v['is_selected'] == True for k, v in self.experiment.MicroscopeState['channels'].items()])

    def set_stack_order_from_configuration_experiment(self) -> None:
        self._per_stack = self.experiment.MicroscopeState['stack_cycling_mode'] == 'per_stack'

    @property
    def voxel_size(self) -> tuple:
        """Return voxel size"""
        return (self.dx, self.dy, self.dz)

    @property
    def shape(self) -> tuple:
        """Return shape as XYCZT."""
        return (self.shape_x, self.shape_y, self.shape_c, self.shape_z, self.shape_t)

class XMLMetadata(Metadata):

    def write_xml(self, file_name: str, file_type: str) -> None:
        xml = self.to_xml(file_type)
        file_name = '.'.join(file_name.split('.')[:-1])+'.xml'
        with open(file_name, 'r') as fp:
            fp.write(xml)

    def to_xml(self, file_type: str, root: Optional[str] = None, **kw) -> str:
        """
        Convert stored metadata to XML
        """
        try:
            d = getattr(self, f"{file_type.lower().replace(' ','_').replace('-','_')}_xml_dict")(**kw)
            xml = xml_tools.dict_to_xml(d, root)
        except AttributeError:
            logging.debug(f"Metadata Writer - I do not know how to export {self.file_type} metadata to XML.")
        return xml
