#
# Author: Francesco Brun
# Last modified: August, 16th 2016
#
from numpy import int_, float32, finfo, gradient, sqrt, ndarray, real, dot, sort
from numpy import std, zeros, cov, diag, mean, sum, ComplexWarning, amin, amax
from numpy import concatenate, tile, median, repeat, newaxis

from scipy.signal import medfilt
from scipy.ndimage import zoom


def flat_fielding(im, ff, win_size=5):
	""" Apply basic flat fielding to the whole input projection dataset.
	
	Parameters
	----------
	im : array_like
		The (dark-corrected) projection images to process.
		
	ff : array_like
		Flat field images.

    win_size : int
        The flat field images are longitudinally filtered with a moving 
        median filter.

	Return value
	------------
	im : array_like
		Flat-corrected projections.

	"""				
	# Cast the input image:
	im = im.astype(float32)

	# Running median along the third dimension:
	ff = medfilt(ff, (1,1,win_size) ).astype(float32)	

	# Ensure sizes are the same:
	if (ff.shape[2] != im.shape[2]): 
		ff = zoom(ff,(1,1,im.shape[2] / ff.shape[2]))

	# Point-to-point division:
	im = im / (ff + finfo(float32).eps)	

	# Return pre-processed image:
	return im.astype(float32)




