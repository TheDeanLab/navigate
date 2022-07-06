import numpy as np
import PIL 
import glob 

class LazyTiff:
    def __init__(self, fp):
        """
        Lazy-loads a folder containing a sequence of TIFF files as a 3D image stack.
        Assumes all TIFF files are single slices, with the same x and y dims. Image is
        slicable as if a numpy array, it may just take a minute to load all of the images
        depending on how big a slice you want.

        Usage is, e.g.:
            low_res_fp = '/endosome/archive/MIL/marin/Zach/Lung/Alignment/AntiRFP/2022-07-02/Cell_001'
            low_res_data = LazyTiff(low_res_fp)
            imshow(low_res_data[50, 500:1500, 500:1500])

        Parameters
        ----------
        fp : str
            Path to folder containing sequence of TIFF files.
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
        return (self.n_files, self._width, self._height)
    
    def __getitem__(self, keys):
        """Numpy slicing access."""
        
        if not isinstance(keys, tuple):
            keys = (keys,)
        if len(keys) > 3:
            raise IndexError(f"Cannot access this index. Shape is {self.shape}.")
        
        if len(keys) == 0:
            return self._image

        if keys[0] != self._image_index:
            # load a new image
            new_files = self._files[keys[0]]
            if not isinstance(new_files, list):
                new_files = [new_files]
            self._image_index = keys[0]  # TODO: This flips between integer and slice
            self._image = np.zeros((len(new_files), self._width, self._height), dtype=np.uint16)
            for i, file in enumerate(new_files):
                with PIL.Image.open(file) as im:
                    self._image[i,...] = im
                    
        self._image = self._image.squeeze()
        if len(keys) == 1:
            return self._image
        if len(keys) == 2:
            return self._image[keys[1]]
        
        return self._image[keys[1],keys[2]]
