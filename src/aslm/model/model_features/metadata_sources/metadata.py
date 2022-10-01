#  Standard Imports
import os
import logging
from typing import Optional

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
        self.dx, self.dy, self.dz = 1, 1, 1  # pixel sizes (um)
        self.dt = 1                          # time displacement (s)
        self.dc = 1                          # step size between channels, should always be 1
        self._order = 'XYCZT'
        self._per_stack = True

        # shape
        self.shape_x, self.shape_y, self.shape_z, self.shape_t, self.shape_c = 1, 1, 1, 1, 1
        self.positions = 1

        self.active_microscope = None

    @property
    def configuration(self) -> Optional[Configurator]:
        return self._configuration

    @configuration.setter
    def configuration(self, configuration: Configurator) -> None:
        self._configuration = configuration
        self.set_from_configuration_experiment()

    @property
    def per_stack(self) -> bool:
        return self._per_stack

    def set_from_configuration_experiment(self) -> None:
        if self.configuration.get('experiment') is not None and self.configuration.get('configuration') is not None:
            self.active_microscope = self.configuration['experiment']['MicroscopeState']['resolution_mode']
            self.set_shape_from_configuration_experiment()
            self.set_stack_order_from_configuration_experiment()

    def set_shape_from_configuration_experiment(self) -> None:
        zoom = self.configuration['experiment']['MicroscopeState']['zoom']
        pixel_size = float(self.configuration['configuration']['microscopes'][self.active_microscope]['zoom']['pixel_size'][zoom])
        self.dx, self.dy = pixel_size, pixel_size
        self.dz = float(self.configuration['experiment']['MicroscopeState']['step_size'])
        self.dt = float(self.configuration['experiment']['MicroscopeState']['timepoint_interval'])

        self.shape_x = int(self.configuration['experiment']['CameraParameters']['x_pixels'])
        self.shape_y = int(self.configuration['experiment']['CameraParameters']['y_pixels'])
        self.shape_z = int(self.configuration['experiment']['MicroscopeState']['number_z_steps'])
        self.shape_t = int(self.configuration['experiment']['MicroscopeState']['timepoints'])
        self.shape_c = sum([v['is_selected'] == True for k, v in self.configuration['experiment']['MicroscopeState']['channels'].items()])

        if bool(self.configuration['experiment']['MicroscopeState']['is_multiposition']):
            self.positions = len(self.configuration['experiment']['MicroscopeState']['stage_positions'])
        else:
            self.positions = 1

    def set_stack_order_from_configuration_experiment(self) -> None:
        self._per_stack = self.configuration['experiment']['MicroscopeState']['stack_cycling_mode'] == 'per_stack'

    @property
    def voxel_size(self) -> tuple:
        """Return voxel size"""
        return (self.dx, self.dy, self.dz)

    @property
    def shape(self) -> tuple:
        """Return shape as XYCZT."""
        return (self.shape_x, self.shape_y, self.shape_c, self.shape_z, self.shape_t)


class XMLMetadata(Metadata):
    """
    This is a base class for dealing with metadata that is stored as an XML, e.g. in OME-TIFF or BigDataViewer.
    There are multiple methods for storing XML. In OME-TIFF, the XML is stored in the header of the first OME-TIFF
    file in a directory. In BigDataViewer, it is stored in a separate XML. Both have proprietary XML formats. To
    address this, we store their metadata in a nested dictionary, defined by file_type_xml_dict()
    (e.g. ome_tiff_xml_dict()) (see to_xml()). We then parse this nested dictionary into an XML file. Similarly,
    we can parse from an XML file to a nested dictionary and map these values back to our internal representation
    of metadata values (TODO: Not implemented. Will use xml_tools.parse_xml() for the first bit.)
    """

    def write_xml(self, file_name: str, file_type: str, root: Optional[str] = None, **kw) -> None:
        """Write to XML file. Assumes we do not include the XML header in our nested metadata dictionary."""
        xml = '<?xml version="1.0" encoding="UTF-8"?>'  # XML file header
        # TODO: should os.path.basename be the default? Added this for BigDataViewer's relative path.
        xml += self.to_xml(file_type, root, file_name=os.path.basename(file_name), **kw)
        file_name = '.'.join(file_name.split('.')[:-1])+'.xml'
        with open(file_name, 'w') as fp:
            fp.write(xml)

    def to_xml(self, file_type: str, root: Optional[str] = None, **kw) -> str:
        """
        Convert stored metadata to XML
        """
        xml = ""
        try:
            d = getattr(self, f"{file_type.lower().replace(' ','_').replace('-','_')}_xml_dict")(**kw)
            xml = xml_tools.dict_to_xml(d, root)
        except AttributeError:
            logging.debug(f"Metadata Writer - I do not know how to export {file_type} metadata to XML.")
        return xml
