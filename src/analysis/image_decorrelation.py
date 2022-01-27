import numpy as np
import numpy.matlib
from tifffile import imread, imsave
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pretty_errors

def getDcorrMax(d):
    '''
    # ---------------------------------------
    #
    # Return the local maxima of the decorrelation function d
    #
    # Inputs:
    #  d        	Decorrelation function
    #
    # Outputs:
    #  ind        	Position of the local maxima
    #  A			Amplitude of the local maxima
    #
    # ---------------------------------------
    '''

    ind = np.argmax(d)
    A = d[ind]
    t = d;
    # arbitrary peak significance parameter imposed by numerical noise
    # this becomes relevant especially when working with post-processed data
    dt = 0.001;

    while ind == np.shape(t)[0]:
        t[-1] = []
        if np.isempty(t):
            A = 0
            ind = 1
        else:
            ind = np.argmax(t)
            A = t[ind]
            # check if the peak is significantly larger than the former minimum
            if t[ind] - np.min(d[ind:-1]) > dt:
                break
            else:
                t[ind] = np.min(d[ind:-1])
                ind = np.shape(t)[0]

    return ind, A

def getDcorrLocalMax(d):
    '''
    # [ind,A] = getDcorrLocalMax(d)
    # ---------------------------------------
    #
    # Return the local maxima of the decorrelation function d
    #
    # Inputs:
    #  d        	Decorrelation function
    #
    # Outputs:
    #  ind        	Position of the local maxima
    #  A			Amplitude of the local maxima
    #
    # ---------------------------------------
    '''
    numel = np.shape(d)
    numel = numel[0]

    if numel < 1:
        ind = 0
        A = d[0]
    else:
        ind = np.argmax(d)
        A = d[ind]
        while numel > 1:
            # if the last indexed position
            if ind == numel:
                d[-1] = []
                ind = np.argmax(d)
                A = d[ind]

            # If the first indexed position
            elif ind == 0:
                break

            # If the minimum amplitude between ind and the last index is above a threshold
            elif (A - np.min(d[ind:-1])) >= 0.0005:
                break

            # If the threshold is not met.
            else:
                d[-1] = []
                ind = np.argmax(d)
                A = d[ind]

        if ind.size == 0:
            ind = 0
            A = d[0]

        else:
            A = d[ind]

    return ind, A

def linear_map(val, valMin, valMax):
    '''
    # rsc = linear_map(val,valMin,valMax,mapMin,mapMax)
    # ---------------------------------------
    #
    # Performs a linear mapping of val from the range [valMin,valMax] to the range [mapMin,mapMax]
    #
    # Inputs:
    #  val        	Input value
    #  valMin		Minimum value of the range of val
    #  valMax		Maximum value of the range of val
    #  mapMin		Minimum value of the new range of val
    #  mapMax		Maximum value of the new range of val
    #
    # Outputs:
    #  rsc        	Rescaled value
    #
    # Example : rsc = linear_map(val,0,255,0,1); # map the uint8 val to the range [0,1]
    #
    # ---------------------------------------
    '''

    mapMin = valMin
    mapMax = valMax
    valMin = np.min(val)
    valMax = np.max(val)

    # convert the input value between 0 and 1
    tempVal = (val-valMin)/(valMax-valMin)

    # clamp the value between 0 and 1
    map0 = tempVal < 0
    map1 = tempVal > 1
    tempVal[map0] = 0
    tempVal[map1] = 1

    # rescale and return
    rsc = np.multiply(tempVal, (mapMax-mapMin)) + mapMin
    return rsc

def apod_im_rect(image, N):
    '''
    # [out,mask] = apodImRect(in,N)
    # ---------------------------------------
    #
    # Apodize the edges of a 2D image
    #
    # Inputs:
    #  in        	Input image
    #  N            Number of pixels of the apodization
    #
    # Outputs:
    #  out        	Apodized image
    #  mask         Mask used to apodize the image
    #
    # ---------------------------------------
    '''

    number_x, number_y = np.shape(image)

    x = np.abs(np.linspace(-number_x/2, number_x/2, number_x))
    y = np.abs(np.linspace(-number_y/2, number_y/2, number_y))
    mapx = x > (number_x/2 - N)
    mapy = y > (number_y/2 - N)

    val = np.mean(image)

    d = np.multiply((-np.abs(x) - np.mean(-np.abs(x[mapx]))), mapx)
    d = linear_map(d, -np.pi/2, np.pi/2)
    d[mapx == False] = np.pi/2
    maskx = (np.sin(d)+1)/2

    d = np.multiply((-np.abs(y) - np.mean(-np.abs(y[mapy]))), mapy)
    d = linear_map(d, -np.pi/2, np.pi/2)
    d[mapy == False] = np.pi/2
    masky = (np.sin(d)+1)/2

    # Make it 2D
    # np.matlib.repmat(a, m, n). a: array/matrix. m,n: int - number of times a is repeated on first and second axes.
    mask_1 = np.matlib.repmat(masky, number_x, 1)
    mask_2 = np.matlib.repmat(maskx, number_y, 1)
    mask_2 = np.transpose(mask_2)
    mask = np.multiply(mask_1, mask_2)

    out = np.multiply((image-val), mask) + val

    return out

def getCorrcoef(I1, I2, c1=None, c2=None):
    '''
    # cc = getCorrcoef(I1,I2,c1,c2)
    # ---------------------------------------
    #
    # Return the normalized correlation coefficient expressed in Fourier space
    #
    # Inputs:
    #  I1        	Complex Fourier transfom of image 1
    #  I2           Complex Fourier transfom of image 2
    #
    # Outputs:
    #  cc        	Normalized cross-correlation coefficient
    '''

    if c1 == None:
        c1 = np.square(np.sqrt(np.sum(np.sum(np.abs(I1)))))

    if c2 == None:
        c2 = np.square(np.sqrt(np.sum(np.sum(np.abs(I2)))))
    import warnings
    warnings.simplefilter("ignore", np.ComplexWarning)
    a = np.sum(np.real(np.multiply(I1, np.conjugate(I2))))
    b = c1*c2
    np.seterr(invalid='ignore')
    cc = np.divide(a, b)
    cc = np.double(cc)
    cc = np.floor(1000*cc)/1000
    return cc

def getDCorr(im, r=None, Ng=10, figID=0):
    verbose = True
    if r is None:
        r = np.linspace(0, 1, 50)

    if np.shape(r)[0] < 30:
        r = np.linspace(np.min(r), np.max(r), 30)

        if Ng < 5:
            Ng = 5

    im = np.single(im)

    # Make size odd numbers only.
    number_x, number_y = np.shape(im)
    if np.mod(number_x, 2) == 0:
        im = np.delete(im, 0, 0)
    if np.mod(number_y, 2) == 0:
        im = np.delete(im, 0, 1)

    number_x, number_y = np.shape(im)

    x = np.linspace(-1, 1, number_x)
    y = np.linspace(-1, 1, number_y)
    x, y = np.meshgrid(x, y)
    R = np.sqrt(x**2 + y**2)
    Nr = np.shape(r)[0]

    # In = Fourier Normalized Image
    In = np.fft.fftshift(np.fft.fft2(np.fft.fftshift(im)))
    In = np.divide(In, np.abs(In))
    In[np.isinf(In)] = 0
    In[np.isnan(In)] = 0
    mask0 = R**2 < 1**2
    In = np.multiply(np.transpose(mask0), In)

    # Ik = Fourier Transform of Image
    Ik = np.multiply(np.transpose(mask0), np.fft.fftshift(np.fft.fft2(np.fft.fftshift(im))))
    c = np.sqrt(np.sum(np.multiply(Ik, np.conjugate(Ik))))
    r0 = np.linspace(r[0], r[-1], Nr)

    d0 = np.zeros(np.shape(r)[0])
    for k in range(np.shape(r)[0], 0, -1):
        cc = getCorrcoef(Ik, np.transpose(np.square(R)) < np.multiply(r0[k-1]**2, In), c)
        if np.isnan(cc):
            cc = 0
        d0[k-1] = cc

    ind0, snr0 = getDcorrLocalMax(d0)

    k0 = r[ind0]
    gMax = 2/r0[ind0]

    if np.isinf(gMax):
        gMax = max(np.shape(im)[0], np.shape(im)[1])/2

    # Search for the Highest Frequency Peak
    g = np.hstack((np.shape(im)[0]/4, np.exp(np.linspace(np.log(gMax), np.log(0.15), Ng))))
    d = np.zeros((Nr, 2*Ng))

    number_iterations = 2
    kc = np.zeros(np.shape(g)[0]*number_iterations)
    kc[0] = k0

    SNR = np.zeros(np.shape(g)[0]*number_iterations)
    SNR[0] = snr0

    ind0 = 0


    # Two Step Refinement
    for refin in range(number_iterations):  # 0, 1.
        for h in range(np.shape(g)[0]):  # 0..10

            # Fourier Gaussian Filtering
            Ir = np.multiply(np.transpose(Ik), (1 - np.exp(-2*g[h]*g[h]*R**2)))
            c = np.sqrt(np.sum(np.abs(Ir)**2))

            for k in range(np.shape(r)[0]-1, ind0-1, -1):  # 49...0
                mask = R**2 < r[k]**2
                cc = getCorrcoef(Ir[mask], In[np.transpose(mask)], c)
                if np.isnan(cc):
                    cc = 0
                d[k, h + (Ng * refin) - 1] = cc

            ind, amp = getDcorrLocalMax(d[k:-1, h + (Ng * refin) - 1])

            snr = d[ind, h + (Ng * refin) - 1]
            ind = ind + k

            kc[h + Ng * refin + 1] = r[ind]
            SNR[h + Ng * refin + 1] = snr

    print("kc :", kc)
    print("SNR :", SNR)


    return 5, 5

def main_image_decorr():
    '''
    https://github.com/Ades91/ImDecorr/blob/master/main_imageDecorr.m
    '''
    # Load the Data
    raw_image = np.array(imread('/Users/S155475/Local/Publication materials/2020-SOLS/Data/MV3Membrane/LateralInsets/DetailVesicleTimepoint30.tif'))
    raw_image = np.double(raw_image)

    # projected pixel size
    pps = 5

    Nr = 50
    Ng = 10
    r = np.linspace(0, 1, Nr)

    GPU = False

    # Apodize Image Edges with a Cosine Function over 20 pixels
    image = apod_im_rect(raw_image, 20)

    # Compute Resolution
    figID = 100
    if GPU:
        pass  # [kcMax,A0] = getDcorr(gpuArray(image),r,Ng,figID); gpuDevice(1);
    else:
        kcMax, A0 = getDCorr(image, r, Ng, figID)

    print("kcMax :", kcMax, "A0 :", A0)

    # sectorial resolution
    Na = 8  # number of sectors
    figID = 101
    if GPU:
        pass  # [kcMax,A0] = getDcorrSect(gpuArray(image),r,Ng,Na,figID); gpuDevice(1);
    else:
        pass  #kcMax, A0 = getDcorrSect(image,r,Ng,Na,figID)

    # Local resolution map
    tileSize = 200  # in pixels
    tileOverlap = 0  # in pixels
    figId = 103

    if GPU:
        pass  #  [kcMap,A0Map] = getLocalDcorr(gpuArray(image),tileSize,tileOverlap,r,Ng,figID);gpuDevice(1);
    else:
        pass  # kcMap, A0Map = getLocalDcorr(image,tileSize,tileOverlap,r,Ng,figID)

    return kcMax, A0


if (__name__ == '__main__'):
    kcMax, AO = main_image_decorr()






    print("Guess we are done here")