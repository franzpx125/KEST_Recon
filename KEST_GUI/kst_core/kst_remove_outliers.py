from numpy import float32, finfo, ndarray, isnan, isinf, logical_or
from numpy import median, amin, amax, nonzero, percentile, pad
from numpy import tile, concatenate, reshape, interp, zeros

from scipy.ndimage.filters import median_filter


def pixel_correction (im, dead_th=0, hot_th=65535):
	"""Correct with interpolation for NaN, Inf, dead and hot pixels.

	Parameters
	----------
	im : array_like
		Image data as numpy array. 

    dead_th : int
		Pixels having gray level below this threshold are considered as dead.
        (default = 0).

    hot_th : int
		Pixels having gray level above this threshold are considered as hot.
        (default = 655353, i.e. 16-bit saturation).

    Return
	----------
    im : array_like
        Image data as numpy array with the correction applied.

    msk : array_like
        Image data as numpy array of Python type bool with True for the corrected 
        pixels, False otherwise.

	"""	
	
	# Pad:
	im = pad(im, (1,1), 'edge')
	msk = zeros(im.shape, dtype=bool)

	# Flat:
	im_f = im.flatten().astype(float32)
	msk_f = msk.flatten()	

	# Correct for NaNs, Infs, dead, hot:
	val, x = logical_or.reduce(( isnan(im_f), isinf(im_f), (im_f <= dead_th), \
		(im_f >= hot_th))), lambda z: z.nonzero()[0]
	im_f[val] = interp(x(val), x(~val), im_f[~val])
	msk_f = logical_or(msk_f, val)

	# Reshape:
	im_f = reshape(im_f, (im.shape[1], im.shape[0]), order='F')
	msk_f = reshape(msk_f, (msk.shape[1], msk.shape[0]), order='F')
	im_f = im_f.T
	msk_f = msk_f.T

	# Crop:
	im = im_f[1:-1,1:-1]
	msk = msk_f[1:-1,1:-1]

	return im, msk 



def afterglow_correction (im, max_depth=7):
	"""Correct afterglow (i.e. values below zero after flat fielding) 
    by adaptive median filtering

	Parameters
	----------
	im : array_like
		Image data as numpy array. 

    max_depth : int
        If a single pass with a 3x3 median filter does not correct all the 
        negative values, a second pass with a 5x5 and then a third, and forth,
        ... passes until a max_depth x max_depth filter is considered. After
        that, all negative values are replaced with the global average.

    Return
	----------
    im : array_like
        Image data as numpy array with the correction applied.
	
	"""

	# Quick and dirty compensation for detector afterglow (it works well for isolated spots):
	size_ct = 3
	while ( ( float(amin(im)) <  0.0) and (size_ct <= max_depth) ):			
		im_f = median_filter(im, size_ct)
		im[im < 0.0] = im_f[im < 0.0]					
		size_ct += 2

	# Compensate negative values by replacing them with the average value of the image:		
	if (float(amin(im)) <  finfo(float32).eps):			
		rplc_value = sum(im [im > finfo(float32).eps]) / sum(im > finfo(float32).eps)		
		im [im < finfo(float32).eps] = rplc_value

	return im