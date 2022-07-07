import numpy as np
import PIL 
import glob 

class LazyTiff:
    def __init__(self, fp):
        """
        Lazy-loads a folder containing a sequence of TIFF files using PIL.
        Assumes all TIFF files are single slices, with the same x and y dims.
        """
            
        # How many images in this sequence?
        self._files = sorted(glob.glob(fp+'/*.tif'))
        self._n_files = len(self._files)
        self._image_index = 0
        try:
            # Open the first image to get the sizing
            with PIL.Image.open(self._files[0]) as im:
                self._image = im
                self._width, self._height = im.width, im.height
        except FileNotFoundError:
            raise FileNotFoundError("Is there a TIFF (.tif) in this folder?")

    @property
    def shape(self):
        return (self._width, self._height, self._n_files)
    
    def __getitem__(self, keys):
        """Numpy slicing access."""
        
        if not isinstance(keys, tuple):
            keys = (keys,)
        if len(keys) > 3:
            raise IndexError(f"Cannot access this index. Shape is {self.shape}.")
            
        print(keys, self._image_index)
        
        image_index = self._image_index
        if len(keys) == 0:
            return self._image.squeeze()
        elif len(keys) < 2:
            # Need to grab all of the files
            new_files = self._files
            self._image_index = ()
        elif keys[2] != self._image_index:
            # load a new image
            new_files = self._files[keys[2]]
            if not isinstance(new_files, list):
                new_files = [new_files]
            self._image_index = keys[2]
        
        if image_index != self._image_index:
            self._image = np.zeros((self._width, self._height, len(new_files)), dtype=np.uint16)
            for i, file in enumerate(new_files):
                with PIL.Image.open(file) as im:
                    self._image[...,i] = im
                    
        if len(keys) == 1:
            return self._image[keys[0],...].squeeze()
        
        return self._image[keys[0],keys[1],:].squeeze()
