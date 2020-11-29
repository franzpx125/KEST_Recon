from numpy import float32, finfo, ndarray, isnan, isinf, logical_or, uint16
from numpy import median, amin, amax, nonzero, percentile, pad, array
from numpy import tile, concatenate, reshape, interp, zeros, asfortranarray

from scipy.ndimage.filters import median_filter

from . import _despeckle


def despeckle(im, thresh=0.1, non_negativity=False, nr_threads=16):
	"""Correct impulsive noise (NaN and Inf as well) with a custom non-linear filter.

	Parameters
	----------
	im : array_like
		Image 3D dataset as numpy array organized as [x,y,angles]. 

    thresh : float
		Threshold to determine if a pixel has to be considered as noise. Lower values
        more filtering.

    nr_threads : int
        Number of parallel threads (each image of the dataset is processed in parallel).

	Return
	----------
	im : array_like
		Image 3D data as numpy array with the correction applied.

	"""	
	non_neg_i = 1 if non_negativity else 0

	shp = array([im.shape[0],im.shape[1],im.shape[2]]) # For further reshape
	im = asfortranarray(im.transpose(2,1,0), dtype=float32).flatten()	# Note the flattening
	
    # Call (OpenMP parallel) C-code:
	im = _despeckle.despeckle(im.astype(float32), shp, thresh, non_neg_i, nr_threads)	
	
	im = reshape(im, shp, order='F') # 1-D output
	
	return im



def pixel_correction(im):
	"""Correct with interpolation for NaN, Inf, dead and hot pixels.

	Parameters
	----------
	im : array_like
		Image data as numpy array. 

	Return
	----------
	im : array_like
		Image data as numpy array with the correction applied.

	"""	
	# Save original type to further re-cast:
	t = im.dtype
	im = im.astype(float32)	

	# Flat:
	im_f = im.flatten().astype(float32)

	# Correct for NaNs, Infs, dead, hot:
	try:
		val, x = logical_or.reduce((isnan(im_f), isinf(im_f), (im_f < finfo(float32).eps))), \
				 lambda z: z.nonzero()[0]
		im_f[val] = interp(x(val), x(~val), im_f[~val])

	except:
		pass
	
	finally:

		# Reshape:
		im_f = reshape(im_f, (im.shape[1], im.shape[0]), order='F')
		im_f = im_f.T

	# Re-cast and return:
	return im_f.astype(t) 




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
		print("Afterglow occurred.")		
		im_f = median_filter(im, size_ct)
		im[im < finfo(float32).eps] = im_f[im < finfo(float32).eps]					
		size_ct += 2

	# Compensate negative values by replacing them with zero:
	if (float(amin(im)) < finfo(float32).eps):		
		im[im < finfo(float32).eps] = finfo(float32).eps

	return im



	
