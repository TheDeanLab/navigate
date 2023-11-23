import os
import ctypes as ct
import numpy as np
import pandas as pd
import time

from .enums import *

basepath = 'D:\\WaveKitX64'
# wfc_config_file_path = os.path.join(basepath, 'MirrorFiles', 'WaveFrontCorrector_Mirao52-e_0259.dat')
# haso_config_file_path = os.path.join(basepath, 'MirrorFiles', 'HASO4_first_7458.dat')

imop_lib = ct.windll.LoadLibrary(os.path.join(basepath, 'C', 'Lib', 'c_interface_vc100_x64.dll'))
# mode_names = ['x-tilt','y-tilt','defocus','obliq. asm.','vert. asm.','vert. coma','horiz. coma','vert. tre.','obliq. tre.','spherical','vert. 2nd asm.','horiz. 2nd asm.','vert. quad.','obliq. quad.']
# mode_names = ['piston', 'x-tilt','y-tilt','defocus','obliq. asm.','vert. asm.','vert. coma','horiz. coma','spherical','vert. tre.','obliq. tre.','vert. 2nd asm.','horiz. 2nd asm.','vert. quad.','obliq. quad.']

mode_names = [
    "Vert. Tilt",
    "Horz. Tilt",
    "Defocus",
    "Vert. Asm.",
    "Oblq. Asm.",
    "Vert. Coma",
    "Horz. Coma",
    "3rd Spherical",
    "Vert. Tre.",
    "Horz. Tre.",
    "Vert. 5th Asm.",
    "Oblq. 5th Asm.",
    "Vert. 5th Coma",
    "Horz. 5th Coma",
    "5th Spherical",
    "Vert. Tetra.",
    "Oblq. Tetra.",
    "Vert. 7th Tre.",
    "Horz. 7th Tre.",
    "Vert. 7th Asm.",
    "Oblq. 7th Asm.",
    "Vert. 7th Coma",
    "Horz. 7th Coma",
    "7th Spherical",
    "Vert. Penta.",
    "Horz. Penta.",
    "Vert. 9th Tetra.",
    "Oblq. 9th Tetra.",
    "Vert. 9th Tre.",
    "Horz. 9th Tre.",
    "Vert. 9th Asm.",
    "Oblq. 9th Asm."
    ]

"""
    MODE NAMES:
    1   Vert. Tilt
    2   Horz. Tilt
    3   Defocus
    4   Vert. Asm.
    5   Oblq. Asm.
    6   Vert. Coma
    7   Horz. Coma
    8   3rd Spherical
    9   Vert. Tre.
    10  Horz. Tre.
    11  Vert. 5th Asm.
    12  Oblq. 5th Asm.
    13  Vert. 5th Coma
    14  Horz. 5th Coma
    15  5th Spherical
    16  Vert. Tetra.
    17  Oblq. Tetra.
    18  Vert. 7th Tre.
    19  Horz. 7th Tre.
    20  Vert. 7th Asm.
    21  Oblq. 7th Asm.
    22  Vert. 7th Coma
    23  Horz. 7th Coma
    24  7th Spherical
    25  Vert. Penta.
    26  Horz. Penta.
    27  Vert. 9th Tetra.
    28  Oblq. 9th Tetra.
    29  Vert. 9th Tre.
    30  Horz. 9th Tre.
    31  Vert. 9th Asm.
    32  Oblq. 9th Asm.
"""

# ctypes utility functions:
def char_p(s):    
    # return a C character pointer from python String
    return ct.c_char_p(s.encode('utf-8'))

def arr_p(ndarr):
    # convert numpy.ndarray to C pointer array
    return ct.c_void_p(ndarr.ctypes.data)

def call_errmsg(func, *args):
    message = ct.create_string_buffer(256)
    
    flag = func(message, *args)
        
    err_msg = f"{func.__name__}: {message.value.decode('utf-8')}"
    del message
    
    if flag:
        raise Exception(err_msg)
    
    return err_msg, flag

# CTypes Structures:

class uint2D(ct.Structure):

    _fields_ = [
        ('X', ct.c_uint),
        ('Y', ct.c_uint)
        ]    
        
class int2D(ct.Structure):

    _fields_ = [
        ('X', ct.c_int),
        ('Y', ct.c_int)
        ]
        
class float2D(ct.Structure):

    _fields_ = [
        ('X', ct.c_float),
        ('Y', ct.c_float)
        ]

# Generic class which contains a pointer to object address
# (used in C Imop functions)
class Pointer:
    
    def __init__(self):    
        self.pointer = ct.c_void_p()
    
    def __call__(self):
        return self.pointer

'''
Imop_Pupil_SetData

Imop_PupilCompute_FitZernikePupil

Imop_HasoSlopes_NewFromModalCoef
Imop_HasoSlopes_Delete
'''
class IMOP_Mirror:
    
    def __init__(self,
                 wfc_config_file_path=os.path.join(basepath, 'MirrorFiles', 'WaveFrontCorrector_Mirao52-e_0259.dat'),
                 haso_config_file_path=os.path.join(basepath, 'MirrorFiles', 'HASO4_first_7458.dat'),
                 #positions_file_path=os.path.join(basepath, 'Matlab', 'FlouresceinJuly19th22_3iter.wcs'),
                 #positions_file_path=os.path.join(basepath, 'MirrorFiles', 'FEP-tube-2022-11-10.wcs'),
                 #positions_file_path=os.path.join(basepath, 'MirrorFiles', 'Louis-2022-11-03.wcs'),
                 #positions_file_path=os.path.join(basepath, 'MirrorFiles', 'Fluorescein-2022-11-15.wcs'),
                 positions_file_path=os.path.join(basepath, 'MirrorFiles', 'OPMv3_SysCorr_517nm_20230324.wcs'),
                 #positions_file_path=os.path.join(basepath, 'MirrorFiles', 'best.wcs'),
                 #interaction_matrix_file_path=os.path.join(basepath, 'MirrorFiles', 'OlympusJuly5.aoc'),
                 interaction_matrix_file_path=os.path.join(basepath, 'MirrorFiles', 'VAST_Sept_2023_b.aoc'),
                 n_modes=32
                 ):
        
        mirror_set = WavefrontCorrectorSet()
        mirror_set.new_from_config_file(wfc_config_file_path)
        
        mirror = WavefrontCorrector(
            wfc_config_file_path=wfc_config_file_path,
            haso_config_file_path=haso_config_file_path,
            positions_file_path=positions_file_path,
            interaction_matrix_file_path=interaction_matrix_file_path,
            n_actuators=mirror_set.get_actuators_count()
            )
        
        corrdata_manager = CorrDataManager()
        corrdata_manager.new_from_backup_file(haso_config_file_path, interaction_matrix_file_path)

        corrdata_manager.set_command_matrix_prefs(nb_kept_modes=32)
        corrdata_manager.compute_command_matrix()

        mirror.set_temporization(20)
        
        config = CoreEngine().get_config(haso_config_file_path)

        pupil = Pupil()
        pupil.new_from_dimensions(config.nb_subpupils, config.ulens_step, 0)

        pupil_zeros = np.zeros((config.nb_subpupils.Y, config.nb_subpupils.X))
        pupil_buffer = corrdata_manager.get_greatest_common_pupil(pupil_zeros)

        pupil.set_data(pupil_buffer)
        
        self.pupil_center, self.pupil_radius = PupilCompute().fit_zernike_pupil(
            pupil, 
            E_PUPIL_DETECTION_T.E_PUPIL_AUTOMATIC, 
            E_PUPIL_COVERING_T.E_PUPIL_CIRCUMSCRIBED, 
            0
            )
        
        self.position_flat = mirror.get_positions_from_file(positions_file_path)

        modal_coef = ModalCoef()
        modal_coef.new() # default is Zernike
        modal_coef.set_zernike_prefs(
            n_modes, 
            0, 
            np.empty(0), 
            self.pupil_center, 
            self.pupil_radius 
            # normalization=E_ZERNIKE_NORM_T.E_ZERNIKE_NORM_RMS
            )
        
        self.n_modes = n_modes
        self.mirror = mirror
        self.mirror_set = mirror_set
        self.corrdata_manager = corrdata_manager
        self.pupil = pupil
        self.modal_coef = modal_coef
        self.haso_slopes = HasoSlopes()
        self.last_delta_commands = np.zeros(self.mirror.n_actuators, dtype=np.float32)

    def flat(self):
        # self.mirror.move_absolute(self.position_flat)

        self.display_modes(np.zeros(self.n_modes, dtype=np.float32))

    def zero_flatness(self):
        self.set_flat(np.zeros(self.mirror.n_actuators, dtype=np.float32))
        self.flat()

    def set_flat(self, pos=None, pos_path=None):
        if pos_path:
            pos = self.mirror.get_positions_from_file(pos_path)
        self.position_flat = pos

    def move_absolute_zero(self):
        self.mirror.move_absolute(np.zeros(self.mirror.n_actuators, dtype=np.float32))

    def display_modes(self, coefs, wait=False):
        # make sure coefs is np.float32 array
        if type(coefs) is not np.ndarray:
            coefs = np.array(coefs)
        if coefs.dtype is not np.float32:
            coefs = coefs.astype(np.float32)

        try:
            self.modal_coef.set_data(coefs, np.arange(1,self.n_modes+1).astype(np.uint32), self.n_modes, self.pupil)
        except Exception as modal_coef_exception:
            print("modal_coef.set_data failed...\n", modal_coef_exception)

        try:
            self.haso_slopes.new_from_modal_coef(self.modal_coef, self.mirror.haso_config_file_path)
        except Exception as haso_exception:
            print("haso_slopes.new_from_modal_coef failed...\n", haso_exception)        
        
        try:
            delta_commands = self.corrdata_manager.compute_delta_command_from_delta_slopes(self.haso_slopes, np.zeros(self.mirror.n_actuators).astype(np.float32))
        except Exception as delta_commands_exception:
            print("corrdata_manager.compute_delta_command_from_delta_slopes failed...\n", delta_commands_exception) 

        self.last_delta_commands = delta_commands
        
        new_positions = self.position_flat + delta_commands

        try:
            self.mirror.move_absolute(new_positions)
        except Exception as move_exception:
            print("mirror.move_absolute failed...\n", move_exception)

        if wait:
            # while True:
            #     pos_check = self.mirror.check_absolute_positions(new_positions)
            #     if pos_check == 0:
            #         break
            #     print(f'Positions not yet satisfied! >> flag: {pos_check}')
            timeout = 1000
            t = 0
            while (self.get_modal_coefs()[0] != coefs).any():
                t += 1
                if t == timeout:
                    print("Ran out of time...")
                    break
                time.sleep(0.001)

    def update_delta_commands(self):
        self.last_delta_commands = self.mirror.get_current_positions() - self.position_flat

    def get_modal_coefs(self):
        return self.modal_coef.get_data(n_modes=self.n_modes, pupil=self.pupil)

    def load_wcs(self, path=None, name=None, mode_file=False):
        if path:
            wcs_load_path = path
        elif name:
            wcs_load_path = os.path.join(basepath, 'MirrorFiles', name+'.wcs')
        else:
            print("IMOP_Mirror:: Need to provide either name or path!")
            return

        new_positions = self.mirror.get_positions_from_file(wcs_load_path)
        self.mirror.move_absolute(new_positions)
        self.update_delta_commands()

        if mode_file:
            mode_load_path = wcs_load_path.split('.')[0] + '.json'
            
            try:
                import json
                with open(mode_load_path, 'r') as f:
                    coefs = json.load(f)
            except FileNotFoundError as err:
                    print(f'{err.strerror}::{mode_load_path} -> Modal coef will not be updated...')
                    return []
                    
            coefs = [float(c) for c in coefs.values()]

            return coefs

    def save_wcs(self, path=None, name=None, mode_file=False):
        if path:
            wcs_save_path = path
        elif name:    
            wcs_save_path = os.path.join(basepath, 'MirrorFiles', name+'.wcs')
        else:
            print("IMOP_Mirror:: Need to provide either name or path!")
            return
        
        self.mirror.save_positions_to_file(file_path=wcs_save_path)
    
        if mode_file:
            mode_save_path = wcs_save_path.split('.')[0] + '.json'
            coefs, coef_inds = self.get_modal_coefs()
            mode_dict = {}
            # for i, c_idx in enumerate(coef_inds):
            for c in coef_inds:
                mode_dict[mode_names[c-1]] = f'{coefs[c-1]:.4f}'
 
            import json
            with open(mode_save_path, 'w') as f:
                json.dump(mode_dict, f)
            f.close()

    def get_wavefront_pix(self):
        radius = 4
        x, y = np.meshgrid(range(2*radius), range(2*radius))

        x = x - x.mean()
        y = y - y.mean()

        pupil = x**2 + y**2 <= radius**2
        wavefront = np.zeros(pupil.shape)

        wavefront[pupil[:]] = self.last_delta_commands   

        return wavefront

# CoreEngine class (cHasoConfig.h)
class CoreEngine:
    
    def get_config(self, haso_config_file_path):
        _, _, config = self.__Imop_CoreEngine_GetConfig(haso_config_file_path)
        
        return pd.Series(config)
    
    def __Imop_CoreEngine_GetConfig(self, haso_config_file_path):
        serial_number               = ct.create_string_buffer(256)
        revision                    = ct.c_uint()
        model                       = ct.create_string_buffer(256)
        nb_subpupils                = uint2D()
        ulens_step                  = float2D()
        alignment_position_pixels   = float2D()
        tolerance_radius            = ct.c_ushort()
        default_start_subpupil      = uint2D()
        lower_calibration_wavelen   = ct.c_double()
        upper_calibration_wavelen   = ct.c_double()
        black_subpupil_position     = uint2D()
        tilt_limit_mrad             = ct.c_double()
        radius                      = ct.c_double()
        microlens_focal             = ct.c_double()
        smearing_limit_wavelen      = ct.c_double()
        smearing_limit_exp_duration = ct.c_double()
        internal_options_list       = ct.create_string_buffer(256)
        software_info_list          = ct.create_string_buffer(256)
        SdkInfoList                 = ct.create_string_buffer(256)
        
        msg, result = call_errmsg(
            imop_lib.Imop_CoreEngine_GetConfig,
            char_p(haso_config_file_path),
            serial_number,
            ct.byref(revision),
            model,
            ct.byref(nb_subpupils),
            ct.byref(ulens_step),
            ct.byref(alignment_position_pixels),
            ct.byref(tolerance_radius),
            ct.byref(default_start_subpupil),
            ct.byref(lower_calibration_wavelen),
            ct.byref(upper_calibration_wavelen),
            ct.byref(black_subpupil_position),
            ct.byref(tilt_limit_mrad),
            ct.byref(radius),
            ct.byref(microlens_focal),
            ct.byref(smearing_limit_wavelen),
            ct.byref(smearing_limit_exp_duration),
            internal_options_list,
            software_info_list,
            SdkInfoList
            )

        config = {
            'serial_number'               : serial_number.value.decode('utf-8'),
            'revision'                    : revision.value,
            'model'                       : model.value.decode('utf-8'),
            'nb_subpupils'                : nb_subpupils,
            'ulens_step'                  : ulens_step,
            'alignment_position_pixels'   : alignment_position_pixels,
            'tolerance_radius'            : tolerance_radius.value,
            'default_start_subpupil'      : default_start_subpupil,
            'lower_calibration_wavelen'   : lower_calibration_wavelen.value,
            'upper_calibration_wavelen'   : upper_calibration_wavelen.value,
            'black_subpupil_position'     : black_subpupil_position,
            'tilt_limit_mrad'             : tilt_limit_mrad.value,
            'radius'                      : radius.value,
            'microlens_focal'             : microlens_focal.value,
            'smearing_limit_wavelen'      : smearing_limit_wavelen.value,
            'smearing_limit_exp_duration' : smearing_limit_exp_duration.value,
            'internal_options_list'       : internal_options_list.value.decode('utf-8').split(';'),
            'software_info_list'          : software_info_list.value.decode('utf-8').split(';'),
            'SdkInfoList'                 : SdkInfoList.value.decode('utf-8').split(';')
            }
        
        return msg, result, config          

# HasoSlopes class (cHasoSlopes.h)
class HasoSlopes(Pointer):

    def __init__(self):
        super().__init__()

    # Public functions:
        
    def new_from_modal_coef(self, modal_coef, haso_config_file_path):
        self.__Imop_HasoSlopes_NewFromModalCoef(modal_coef, haso_config_file_path)           

    # Private functions translated directly from Imop C API:      

    def __Imop_HasoSlopes_NewFromModalCoef(self, modal_coef, config_file_path):
        return call_errmsg(
            imop_lib.Imop_HasoSlopes_NewFromModalCoef,
            ct.byref(self.pointer),
            modal_coef.pointer,
            char_p(config_file_path)
            )

# PupilCompute class (cComputePupil.h)
class PupilCompute(Pointer):

    def __init__(self):
        super().__init__()

    # Public functions:
        
    def fit_zernike_pupil(
            self, 
            pupil, 
            detection_mode=E_PUPIL_DETECTION_T.E_PUPIL_AUTOMATIC, 
            covering=E_PUPIL_COVERING_T.E_PUPIL_INSCRIBED, 
            has_central_occultation=False):
        _, _, center, radius = self.__Imop_PupilCompute_FitZernikePupil(pupil, detection_mode, covering, has_central_occultation)

        return center, radius            

    # Private functions translated directly from Imop C API:      

    def __Imop_PupilCompute_FitZernikePupil(self, pupil, detection_mode, covering, has_central_occultation):
        center = float2D()
        radius = ct.c_float()
        
        msg, result = call_errmsg(
            imop_lib.Imop_PupilCompute_FitZernikePupil,
            pupil.pointer,
            detection_mode,
            covering,
            has_central_occultation,
            ct.byref(center),
            ct.byref(radius)
            )
        
        return msg, result, center, radius

# Pupil class (cPupil.h)
class Pupil(Pointer):
    
    def __init__(self):
        super().__init__()

    def __del__(self):
        # Destructor
        self.__Imop_Pupil_Delete()

    # Public functions:

    def new_from_dimensions(self, dimensions, steps, value):
        self.__Imop_Pupil_NewFromDimensions(dimensions, steps, value)

    def new_from_zernike_pupil(self, dimensions, steps, center, radius):
        self.__Imop_Pupil_NewFromZernikePupil(dimensions, steps, center, radius)

    def get_data(self, buffer):
        _, _, data = self.__Imop_Pupil_GetData(buffer)

        return data

    def set_data(self, data):
        self.__Imop_Pupil_SetData(data)

    # Private functions translated directly from Imop C API:      

    def __Imop_Pupil_NewFromDimensions(self, dimensions, steps, value):
        return call_errmsg(
            imop_lib.Imop_Pupil_NewFromDimensions,
            ct.byref(self.pointer),
            ct.byref(dimensions),
            ct.byref(steps),
            value
            )

    def __Imop_Pupil_NewFromZernikePupil(self, dimensions, steps, center, radius):
        return call_errmsg(
            imop_lib.Imop_Pupil_NewFromZernikePupil,
            ct.byref(self.pointer),
            ct.byref(steps),
            ct.byref(dimensions),
            ct.byref(center),
            ct.c_float(radius)
            )            

    def __Imop_Pupil_GetData(self, data):
        data = data.astype(bool)
        
        msg, result = call_errmsg(
            imop_lib.Imop_Pupil_GetData,
            self.pointer,
            arr_p(data)
            )
        
        return msg, result, data

    def __Imop_Pupil_SetData(self, data):
        return call_errmsg(
            imop_lib.Imop_Pupil_SetData,
            self.pointer,
            arr_p(data)
            )   

    def __Imop_Pupil_Delete(self):
        return call_errmsg(
            imop_lib.Imop_Pupil_Delete,
            self.pointer
            )            
        
# ModalCoef class (cModalCoef.h)
class ModalCoef(Pointer):
    
    def __init__(self):
        super().__init__()

    def __del__(self):
        # Destructor
        self.__Imop_ModalCoef_Delete()

    # Public functions:

    def new(self, e_modal_t=E_MODAL_T.E_MODALCOEF_ZERNIKE):
        self.__Imop_ModalCoef_New(e_modal_t)        

    def set_zernike_prefs(
            self, 
            nb_coefs_total, 
            nb_coefs_to_filter, 
            coefs_to_filter, 
            projection_pupil_center, 
            projection_pupil_radius,
            normalization=E_ZERNIKE_NORM_T.E_ZERNIKE_NORM_STD
            ):
        self.__Imop_ModalCoef_SetZernikePrefs(
            normalization, 
            nb_coefs_total, 
            nb_coefs_to_filter, 
            coefs_to_filter, 
            projection_pupil_center, 
            projection_pupil_radius
            )

    def set_data(self, coef, index, size, pupil):
        self.__Imop_ModalCoef_SetData(coef, index, size, pupil)

    def get_data(self, n_modes, pupil):
        _, _, coef, index = self.__Imop_ModalCoef_GetData(n_modes, pupil)

        return coef, index

    # Private functions translated directly from Imop C API:

    def __Imop_ModalCoef_New(self, e_modal_t):
        return call_errmsg(
            imop_lib.Imop_ModalCoef_New,
            ct.byref(self.pointer),
            e_modal_t
            )       

    def __Imop_ModalCoef_SetZernikePrefs(
            self, 
            normalization, 
            nb_coefs_total, 
            nb_coefs_to_filter, 
            coefs_to_filter, 
            projection_pupil_center, 
            projection_pupil_radius
            ):
        return call_errmsg(
            imop_lib.Imop_ModalCoef_SetZernikePrefs,
            self.pointer,
            normalization, 
            nb_coefs_total, 
            nb_coefs_to_filter, 
            arr_p(coefs_to_filter), 
            ct.byref(projection_pupil_center), 
            projection_pupil_radius
            )       

    def __Imop_ModalCoef_SetData(self, coef, index, size, pupil):
        return call_errmsg(
            imop_lib.Imop_ModalCoef_SetData,
            self.pointer,
            arr_p(coef),
            arr_p(index),
            size,
            pupil.pointer
            )   

    def __Imop_ModalCoef_GetData(self, n_modes, pupil):
        coef = np.zeros(n_modes, dtype=np.float32)
        index = np.zeros(n_modes, dtype=np.uint32)
        
        msg, result = call_errmsg(
            imop_lib.Imop_ModalCoef_GetData,
            self.pointer,
            arr_p(coef),
            arr_p(index),
            pupil.pointer
            )

        return msg, result, coef, index  

    def __Imop_ModalCoef_Delete(self):
        return call_errmsg(
            imop_lib.Imop_ModalCoef_Delete,
            self.pointer
            )

# CorrDataManager class (cCorrDataManager.h)
class CorrDataManager(Pointer):
    
    def __init__(self):
        super().__init__()
        
    def __del__(self):
        # Destructor      
        self.__Imop_CorrDataManager_Delete()

    # Public functions:
    
    def new_from_backup_file(self, haso_config_file_path, interaction_matrix_file_path):
        self.__Imop_CorrDataManager_NewFromBackupFile(haso_config_file_path, interaction_matrix_file_path)
    
    def set_command_matrix_prefs(self, nb_kept_modes, tilt_filtering=False):
        self.__Imop_CorrDataManager_SetCommandMatrixPrefs(nb_kept_modes, tilt_filtering)

    def compute_command_matrix(self):
        self.__Imop_CorrDataManager_ComputeCommandMatrix()

    def get_greatest_common_pupil(self, pupil):
        _, _, pupil = self.__Imop_CorrDataManager_GetGreatestCommonPupil(pupil)
        
        return pupil
    
    def compute_delta_command_from_delta_slopes(self, delta_slopes, delta_command):
        _, _, delta_command = self.__Imop_CorrDataManager_ComputeDeltaCommandFromDeltaSlopes(delta_slopes, delta_command)
        
        return delta_command
    
    # Private functions translated directly from Imop C API:
    
    def __Imop_CorrDataManager_NewFromBackupFile(self, haso_config_file_path, interaction_matrix_file_path):
        return call_errmsg(
            imop_lib.Imop_CorrDataManager_NewFromBackupFile,
            ct.byref(self.pointer), 
            char_p(haso_config_file_path),
            char_p(interaction_matrix_file_path)
            ) 
        
    def __Imop_CorrDataManager_Delete(self):
        return call_errmsg(
            imop_lib.Imop_CorrDataManager_Delete,
            self.pointer
            )

    def __Imop_CorrDataManager_SetCommandMatrixPrefs(self, nb_kept_modes, tilt_filtering):
        return call_errmsg(
            imop_lib.Imop_CorrDataManager_SetCommandMatrixPrefs,
            self.pointer, 
            nb_kept_modes,
            tilt_filtering
            )
    
    def __Imop_CorrDataManager_ComputeCommandMatrix(self):
        return call_errmsg(
            imop_lib.Imop_CorrDataManager_ComputeCommandMatrix,
            self.pointer
            )

    def __Imop_CorrDataManager_GetGreatestCommonPupil(self, pupil):      
        pupil = pupil.astype(bool)
        
        msg, result = call_errmsg(
            imop_lib.Imop_CorrDataManager_GetGreatestCommonPupil,
            self.pointer,
            arr_p(pupil)
            )
        
        return msg, result, pupil

    def __Imop_CorrDataManager_ComputeDeltaCommandFromDeltaSlopes(self, delta_slopes, delta_command):      
        delta_command = delta_command.astype(np.float32)
        
        msg, result = call_errmsg(
            imop_lib.Imop_CorrDataManager_ComputeDeltaCommandFromDeltaSlopes,
            self.pointer,
            delta_slopes.pointer, # HasoSlopes object
            arr_p(delta_command)
            )
        
        return msg, result, delta_command

# WavefrontCorrectorSet class (cWavefrontCorrectorSet.h)
class WavefrontCorrectorSet(Pointer):
    
    def __init__(self):
        super().__init__()
    
    def __del__(self):
        # Destructor      
        self.__Imop_WavefrontCorrectorSet_Delete()

    # Public functions:
    
    def new_from_config_file(self, wfc_config_file_path):
        self.__Imop_WavefrontCorrectorSet_NewFromConfigFile(wfc_config_file_path)
    
    def get_actuators_count(self):
        _, _, n_actuators = self.__Imop_WavefrontCorrectorSet_GetActuatorsCount()
    
        return n_actuators
    
    # Private functions translated directly from Imop C API:
    
    def __Imop_WavefrontCorrectorSet_NewFromConfigFile(self, wfc_config_file_path):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrectorSet_NewFromConfigFile,
            ct.byref(self.pointer), 
            char_p(wfc_config_file_path)
            ) 

    def __Imop_WavefrontCorrectorSet_GetActuatorsCount(self):
        n_actuators = ct.c_int()
        
        msg, result = call_errmsg(
            imop_lib.Imop_WavefrontCorrectorSet_GetActuatorsCount,
            self.pointer,
            ct.byref(n_actuators),
            )
        
        return msg, result, n_actuators.value       
    
    def __Imop_WavefrontCorrectorSet_Delete(self):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrectorSet_Delete,
            self.pointer
            )

# WavefrontCorrector class (cWavefrontCorrector.h)
class WavefrontCorrector(Pointer):

    def __init__(self,
                 wfc_config_file_path=os.path.join(basepath, 'MirrorFiles', 'WaveFrontCorrector_Mirao52-e_0259.dat'),
                 haso_config_file_path=os.path.join(basepath, 'MirrorFiles', 'HASO4_first_7458.dat'),
                 #positions_file_path=os.path.join(basepath, 'Matlab', 'FlouresceinJuly19th22_3iter.wcs'),
                 positions_file_path=os.path.join(basepath, 'MirrorFiles', 'FlouresceinOctober12.wcs'),
                 #interaction_matrix_file_path=os.path.join(basepath, 'MirrorFiles', 'OlympusJuly5.aoc'),
                 interaction_matrix_file_path=os.path.join(basepath, 'MirrorFiles', 'OlympusApril22.aoc'),
                 n_actuators=52
                 ):
        super().__init__()
        
        self.wfc_config_file_path = wfc_config_file_path
        self.haso_config_file_path = haso_config_file_path   
        self.positions_file_path = positions_file_path   
        self.interaction_matrix_file_path = interaction_matrix_file_path
        
        self.n_actuators = n_actuators
        
        self.__Imop_WavefrontCorrector_NewFromConfigFile()
        self.__Imop_WavefrontCorrector_Init()

        self.get_preferences()

    def __del__(self):
        # Destructor        
        self.__Imop_WavefrontCorrector_Delete()

    # Public functions:
        
    def get_preferences(self):
        _, _, (sleep_after_movement, cmd_min, cmd_max, validity, fixed_values) = self.__Imop_WavefrontCorrector_GetPreferences()        

        self.preferences = {
            'sleep_after_movement': sleep_after_movement, 
            'cmd_min': cmd_min, 
            'cmd_max': cmd_max, 
            'validity': validity, 
            'fixed_values': fixed_values
            }
        
        return self.preferences

    def set_preferences(self, **kwargs):
        for k in kwargs.keys():
            if k in self.preferences.keys():
                self.preferences[k] = kwargs[k]
            else:
                raise ValueError(k + ' is not a valid preference! Choose from: ' + str([k for k in self.preferences.keys()]))
                return
        
        self.__Imop_WavefrontCorrector_SetPreferences(
            self.preferences['sleep_after_movement'], 
            self.preferences['cmd_min'], 
            self.preferences['cmd_max'], 
            self.preferences['validity'], 
            self.preferences['fixed_values']
            )

    def get_temporization(self):
        _, _, sleep_after_movement = self.__Imop_WavefrontCorrector_GetTemporization()
        
        return sleep_after_movement

    def set_temporization(self, sleep_after_movement):
        self.preferences['sleep_after_movement'] = sleep_after_movement
        
        self.__Imop_WavefrontCorrector_SetTemporization(sleep_after_movement)

    def get_current_positions(self):
        _, _, positions = self.__Imop_WavefrontCorrector_GetCurrentPositions()
        
        return positions

    def get_positions_from_file(self, path):
        _, _, positions = self.__Imop_WavefrontCorrector_GetPositionsFromFile(path)
        
        return positions

    def save_positions_to_file(self, file_path):
        self.__Imop_WavefrontCorrector_SaveCurrentPositionsToFile(file_path)

    def move_relative(self, positions):
        self.__Imop_WavefrontCorrector_MoveToRelativePositions(positions.astype(np.float32))

    def move_absolute(self, positions):
        self.__Imop_WavefrontCorrector_MoveToAbsolutePositions(positions.astype(np.float32))

    # TODO: doesn't really work... always returns zero.
    def check_absolute_positions(self, positions):
        _, flag = self.__Imop_WavefrontCorrector_CheckAbsolutePositions(positions.astype(np.float32))
        return flag

    def clear(self):
        self.move_absolute(np.zeros(self.n_actuators))

    # Private functions translated directly from Imop C API:

    def __Imop_WavefrontCorrector_Delete(self):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_Delete,
            self.pointer
            )
        
    def __Imop_WavefrontCorrector_NewFromConfigFile(self):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_NewFromConfigFile,
            ct.byref(self.pointer), 
            char_p(self.wfc_config_file_path)
            )

    def __Imop_WavefrontCorrector_Init(self, set_init_state_from_config_file=True):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_Init,
            self.pointer,
            ct.c_bool(set_init_state_from_config_file)
            )

    def __Imop_WavefrontCorrector_CallSpecificFeature(self, feature_name):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_CallSpecificFeature,
            self.pointer,
            char_p(feature_name)
            )
    
    def __Imop_WavefrontCorrector_GetPreferences(self):
        sleep_after_movement = ct.c_int()
        cmd_min = np.zeros(self.n_actuators).astype(np.float32)
        cmd_max = np.zeros(self.n_actuators).astype(np.float32)
        validity = np.zeros(self.n_actuators).astype(np.int32)
        fixed_values = np.zeros(self.n_actuators).astype(np.float32)
        
        msg, result = call_errmsg(
            imop_lib.Imop_WavefrontCorrector_GetPreferences,
            self.pointer,
            ct.byref(sleep_after_movement),
            arr_p(cmd_min),
            arr_p(cmd_max),
            arr_p(validity),
            arr_p(fixed_values)
            )
        
        return msg, result, (sleep_after_movement.value, cmd_min, cmd_max, validity, fixed_values)
    
    # TODO: Imop_WavefrontCorrector_AssertEqualPreferences
    
    # TODO: Imop_WavefrontCorrector_CheckUserPreferences
    
    def __Imop_WavefrontCorrector_SetPreferences(self, sleep_after_movement, cmd_min, cmd_max, validity, fixed_values):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_SetPreferences,
            self.pointer,
            sleep_after_movement,
            arr_p(cmd_min),
            arr_p(cmd_max),
            arr_p(validity),
            arr_p(fixed_values)
            )

    def __Imop_WavefrontCorrector_GetTemporization(self):
        sleep_after_movement = ct.c_int()
        
        msg, result = call_errmsg(
            imop_lib.Imop_WavefrontCorrector_GetTemporization,
            self.pointer,
            ct.byref(sleep_after_movement),
            )
        
        return msg, result, sleep_after_movement.value

    def __Imop_WavefrontCorrector_SetTemporization(self, sleep_after_movement):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_SetTemporization,
            self.pointer,
            sleep_after_movement,
            )
    
    def __Imop_WavefrontCorrector_GetCurrentPositions(self):
        positions = np.zeros(self.n_actuators).astype(np.float32)
        
        msg, result = call_errmsg(
            imop_lib.Imop_WavefrontCorrector_GetCurrentPositions,
            self.pointer,
            arr_p(positions),
            )
        
        return msg, result, positions
    
    # TODO: Imop_WavefrontCorrector_CheckRelativePositions
    
    def __Imop_WavefrontCorrector_MoveToRelativePositions(self, positions):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_MoveToRelativePositions,
            self.pointer,
            arr_p(positions),
            )
    
    # TODO: Imop_WavefrontCorrector_CheckAbsolutePositions
    def __Imop_WavefrontCorrector_CheckAbsolutePositions(self, positions):
        msg, result = call_errmsg(
            imop_lib.Imop_WavefrontCorrector_CheckAbsolutePositions,
            self.pointer,
            arr_p(positions)
            )        

        return msg, result

    def __Imop_WavefrontCorrector_MoveToAbsolutePositions(self, positions):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_MoveToAbsolutePositions,
            self.pointer,
            arr_p(positions),
            )
    
    def __Imop_WavefrontCorrector_GetPositionsFromFile(self, pmc_file_path):
        positions = np.zeros(self.n_actuators).astype(np.float32)

        msg, result = call_errmsg(
            imop_lib.Imop_WavefrontCorrector_GetPositionsFromFile,
            char_p(pmc_file_path),
            arr_p(positions)
            )
    
        return msg, result, positions

    def __Imop_WavefrontCorrector_SaveCurrentPositionsToFile(self, pmc_file_path):
        return call_errmsg(
            imop_lib.Imop_WavefrontCorrector_SaveCurrentPositionsToFile,
            self.pointer,
            char_p(pmc_file_path)
            )
    
    # TODO: Rest of file... but maybe good enough for now.
    