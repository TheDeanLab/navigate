from enum import IntEnum

# Enumerated type defs (cEnum.h):

class E_MODAL_T(IntEnum):
    
    E_MODALCOEF_LEGENDRE = 0
    E_MODALCOEF_ZERNIKE  = 1    

class E_ZERNIKE_NORM_T(IntEnum):
    
    E_ZERNIKE_NORM_STD = 0
    E_ZERNIKE_NORM_RMS = 1  

class E_PUPIL_DETECTION_T(IntEnum):
    
    E_PUPIL_FIXED_RADIUS = 0
    E_PUPIL_FIXED_CENTER = 1
    E_PUPIL_AUTOMATIC    = 2

class E_PUPIL_COVERING_T(IntEnum):
    
    E_PUPIL_INSCRIBED     = 0
    E_PUPIL_CIRCUMSCRIBED = 1  