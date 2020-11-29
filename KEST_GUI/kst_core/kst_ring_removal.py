from numpy import uint16, float32, iinfo, finfo, ndarray
from numpy import copy, pad, zeros, median


def _medfilt (x, k):
	"""Apply a length-k median filter to a 1D array x.
	Boundaries are extended by repeating endpoints.

	Code from https://gist.github.com/bhawkins/3535131

	"""	
	k2 = (k - 1) // 2
	y = zeros ((len (x), k), dtype=x.dtype)
	y[:,k2] = x
	for i in range (k2):
		j = k2 - i
		y[j:,i] = x[:-j]
		y[:j,i] = x[0]
		y[:-j,-(i+1)] = x[j:]
		y[-j:,-(i+1)] = x[-1]
		
	return median (y, axis=1)


def boinhaibel(im, n):
    """Process a sinogram image with the Boin and Haibel de-striping algorithm.

    Parameters
    ----------
    im : array_like
        Image data as numpy array.

    n : int
        Size of the median filtering.

	(Parameter n has to passed as a string ended by ;)
       
    Example (using tifffile.py)
    --------------------------
    >>> im = imread('sino_orig.tif')
    >>> im = boinhaibel(im, 11)    
    >>> imsave('sino_flt.tif', im) 

    References
    ----------
    M. Boin and A. Haibel, Compensation of ring artefacts in synchrotron 
    tomographic images, Optics Express 14(25):12071-12075, 2006.

    """    
    # Compute sum of each column (avoid further division by zero):
    col = im.sum(axis=0) + finfo(float32).eps

    # Perform low pass filtering:
    flt_col = _medfilt(col, n)

    # Apply compensation on each row:
    for i in range(0, im.shape[0]):
        im[i,] = im[i,] * (flt_col / col)

    # Return image:
    return im.astype(float32)

def oimoen(im, n1, n2):
    """Process a sinogram image with the Oimoen de-striping algorithm.

    Parameters
    ----------
    im : array_like
        Image data as numpy array.

    n1 : int
        Size of the horizontal filtering.

    n2 : int
        Size of the vertical filtering.

	(Parameters n1 and n2 have to passed as a string separated by ;)
       
    Example (using tifffile.py)
    --------------------------
    >>> im = imread('sino_orig.tif')
    >>> im = oimoen(im, 51, 121)    
    >>> imsave('sino_flt.tif', im) 

    References
    ----------
    M.J. Oimoen, An effective filter for removal of production artifacts in U.S. 
    geological survey 7.5-minute digital elevation models, Proc. of the 14th Int. 
    Conf. on Applied Geologic Remote Sensing, Las Vegas, Nevada, 6-8 November, 
    2000, pp. 311-319.

    """    
   
	# Padding:
    im = pad(im, ((n2 + n1, n2 + n1), (0, 0)), 'symmetric')
    im = pad(im, ((0, 0), (n1 + n2, n1 + n2)), 'edge')

    im1 = im.copy()

    # Horizontal median filtering:
    for i in range(0, im1.shape[0]):

        im1[i,:] = _medfilt(im1[i,:], n1)        

    # Create difference image (high-pass filter):
    diff = im - im1

    # Vertical filtering:
    for i in range(0, diff.shape[1]):

        diff[:,i] = _medfilt(diff[:,i], n2)

    # Compensate output image:
    im = im - diff

	# Crop padded image:
    im = im[(n2 + n1):im.shape[0] - (n1 + n2), (n1 + n2):im.shape[1] - (n1 + n2)]	

    # Return image according to input type:
    return im.astype(float32)