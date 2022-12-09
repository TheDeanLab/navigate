import logging

import numpy.typing as npt

from multiprocessing.managers import DictProxy

class DataSource:
    def __init__(self, file_name: str = '', mode: str = 'w') -> None:
        """
        Base class for data sources, which can be of arbitrary file type.
        This implements read and write methods for accessing each data source.

        We expect to open the file for read or write during initialization.

        file_name  stores the name of the file to read/write from
        data       stores a pointer to the actual data in the data source and
        metdata    stores a pointer to the metadata.

        Concept and some of the code borrowed from python-microscopy
        (https://github.com/python-microscopy/python-microscopy/).
        """
        self.logger = logging.getLogger(__name__.split(".")[1])
        self.file_name = file_name
        self.metadata = None  # Expect a metadata object
        self._mode = None

        self.dx, self.dy, self.dz = 1, 1, 1  # pixel sizes (um)
        self.dt = 1                          # time displacement (s)
        self.dc = 1                          # step size between channels, should always be 1
        # shape
        self.shape_x, self.shape_y, self.shape_z, self.shape_t, self.shape_c = 1, 1, 1, 1, 1
        self.positions = 1

        self.mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    @mode.setter
    def mode(self, mode_str) -> None:
        if mode_str == self._mode:
            return
        if mode_str in ['r', 'w']:
            self._mode = mode_str
        else:
            self.logger.warning(f"Unknown mode {mode_str}. Setting to 'r'.")
            self._mode = 'r'
        self._mode_checks()

    @property
    def data(self) -> npt.ArrayLike:
        """Return array representation of data stored in data source."""
        raise NotImplementedError('Implemented in a derived class.')

    @property
    def voxel_size(self) -> tuple:
        """Return voxel size"""
        return (self.dx, self.dy, self.dz)

    @property
    def shape(self) -> tuple:
        """Return shape as XYCZT."""
        return (self.shape_x, self.shape_y, self.shape_c, self.shape_z, self.shape_t)

    def set_metadata_from_configuration_experiment(self, configuration: DictProxy) -> None:
        self.metadata.configuration = configuration

        # pull new values from the metadata
        self.dx, self.dy, self.dz = self.metadata.voxel_size
        self.shape_x, self.shape_y, self.shape_c, self.shape_z, self.shape_t = self.metadata.shape
        self.positions = self.metadata.positions

    def _cztp_indices(self, frame_id: int, per_stack: bool = True) -> tuple:
        """Figure out where we are in the stack from the frame number.

        per_stack indicates if we move through z (per_stack=True) or c fastest.
        we move through positions slower than z or c. we move through time slower than z, c or p.
        
        Parameters
        ----------
        frame_id : int 
            Frame number in the stack.
        per_stack : bool
            Are we acquiring images along z before c? See experiment.yml.

        Returns
        -------
        c : int
            Index of channel
        z : int
            Index of z position
        t : int
            Index of time position
        p : int
            Index of multiposition position.
        """
        # If z-stacking, if multi-position
        if self.shape_z > 1:
            # We're z-stacking, make z, c vary faster than t
            if per_stack:
                c = (frame_id // self.shape_z) % self.shape_c
                z = frame_id % self.shape_z
            else:
                c = frame_id % self.shape_c
                z = (frame_id // self.shape_c) % self.shape_z
            
            t = frame_id // (self.shape_c*self.shape_z*self.positions)
            p = (frame_id // (self.shape_c*self.shape_z)) % self.positions
        else:
            # Timepoint acqusition, only c varies faster than t
            c = frame_id % self.shape_c
            t = (frame_id // self.shape_c) % self.shape_t
            z = (frame_id // (self.shape_c*self.shape_t)) % self.shape_z
            p = (frame_id // (self.shape_c*self.shape_t)) % self.positions

        return c, z, t, p

    def _mode_checks(self) -> None:
        """Run additional checks after setting the mode."""
        pass
    
    def write(self, data: npt.ArrayLike, **kw) -> None:
        """Write data to file."""
        raise NotImplementedError('Implemented in a derived class.')
    
    def read(self) -> None:
        """Read data from file."""
        raise NotImplementedError('Implemented in a derived class.')

    def close(self) -> None:
        """Clean up any leftover file pointers, etc."""
        pass

    def __del__(self):
        self.close()
