from numpy import float32, finfo, ndarray, isnan, isinf, logical_or, uint16
from numpy import median, amin, amax, nonzero, percentile, pad
from numpy import tile, concatenate, reshape, interp, zeros

from scipy.ndimage.filters import median_filter

def pixel_correction(im, dead_th=0, hot_th=65535):
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
		(default = 65535, i.e. 16-bit saturation).

	Return
	----------
	im : array_like
		Image data as numpy array with the correction applied.

	msk : array_like
		Image data as numpy array of Python type bool with True for the corrected 
		pixels, False otherwise.

	"""	
	# Save original type to further re-cast:
	t = im.dtype
	im = im.astype(float32)	
	 
	# Prepare the mask:
	msk = zeros(im.shape, dtype=bool)

	# Flat:
	im_f = im.flatten().astype(float32)
	msk_f = msk.flatten()	

	# Correct for NaNs, Infs, dead, hot:
	try:
		val, x = logical_or.reduce((isnan(im_f), isinf(im_f), (im_f <= dead_th), \
			(im_f >= hot_th))), lambda z: z.nonzero()[0]
		im_f[val] = interp(x(val), x(~val), im_f[~val])
		msk_f = logical_or(msk_f, val)

	except:
		pass
	
	finally:

	    # Reshape:
	    im_f = reshape(im_f, (im.shape[1], im.shape[0]), order='F')
	    msk_f = reshape(msk_f, (msk.shape[1], msk.shape[0]), order='F')
	    im_f = im_f.T
	    msk_f = msk_f.T

	# Re-cast and return:
	return im_f.astype(t), msk_f 


def estimate_dead_hot(im, perc_dead=0.1, perc_hot=0.1):
	"""Estimate threshold values for the pixel_correction function.
	
	Parameters
	----------
	im : array_like
		Image data as numpy array. 
		
	Return
	----------
	perc_dead : integer scalar
		Value.
	
	perc_hot : integer scalar
		Value.
	"""

	# Get the tails:
	val_dead = percentile(im, perc_dead) 
	val_hot = percentile(im, 100 - perc_hot) 

	return val_dead, val_hot

	


def despeckle_filter(im, thresh=0.1, win_size=5):
	"""Correct impulsive noise with a selective median filtering.
	
	Parameters
	----------
	im : array_like
		Image data as numpy array. 

	thresh : float 
		A float value in the range [0,1] (suggested = 0.1) used for the automatic 
		identification and correction of outliers pixels. Lower values means more
		correction (i.e. more pixels identified and replaced).

	Return
	----------
	im : array_like
		Image data as numpy array with the correction applied.
	
	"""

    # Selective median filter:
	im_f = median_filter(im, win_size)
	diff_im = abs(im - im_f)
	im[ diff_im > thresh ] = im_f[ diff_im > thresh ]					
	
	return im



def afterglow_correction(im, max_depth=7):
	"""Correct values below zero (such as e.g. after flat fielding) 
	by adaptive median filtering

	Parameters
	----------
	im : array_like
		Image data as numpy array. 

	max_depth : int
		If a single pass with a 3x3 median filter does not correct all the 
		negative values, a second pass with a 5x5 and then a third, and forth,
		... passes until a max_depth x max_depth filter is considered. After
		that, all negative values are replaced with zero.

	Return
	----------
	im : array_like
		Image data as numpy array with the correction applied.
	
	"""

	# Quick and dirty compensation for values below zero:
	size_ct = 3
	while ((float(amin(im)) < finfo(float32).eps) and (size_ct <= max_depth)):			
		im_f = median_filter(im, size_ct)
		im[im < finfo(float32).eps] = im_f[im < finfo(float32).eps]					
		size_ct += 2

	# Compensate negative values by replacing them with zero:
	if (float(amin(im)) < finfo(float32).eps):		
		im[im < finfo(float32).eps] = finfo(float32).eps

	return im