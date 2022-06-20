from numpy import sqrt

def compute_noise_sigma(Fn=1.0, qe=0.82, S=0.0, Ib=100.0, Nr=1.4, M=1.0):
    """
    start sloppy... using https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/sys/SCAS0134E_C13440-20CU_tec.pdf
    the noise sigma is given by

    Parameters
    ----------
    Fn : float
        Excess noise factor (unitless)
    qe : float
        Quantum efficiency (unitless)
    S : float or np.array
        Signal (photons/pixel/frame)
    Ib : float or np.array
        Background (photons/pixel/frame)
    Nr : float
        Readout noise (e- rms)
    M : float
        EM Gain

    Returns
    --------
    noise : float or np.array
        Estimated noise model
    """
    noise = sqrt(Fn*Fn*qe*(S+Ib)+(Nr/M)**2)
    return noise