from numpy import arange, float32, tile, fromfile, delete, reshape, zeros, array, finfo, ndarray 
from numpy import logical_or, isnan, isinf, log as nplog, r_, iinfo, uint16, asfortranarray
from numpy import copy, pad, zeros, median
from glob import glob
from tifffile import imread, imsave # only for debug
from os.path import splitext, isfile, isdir

import cv2

from . import kst_io
from . import kst_flat_fielding
from . import kst_matrix_manipulation
from . import kst_remove_outliers
from . import kst_ring_removal



from numpy import arange, float32, tile, fromfile, delete, reshape, zeros, array, finfo, ndarray 
from numpy import logical_or, isnan, isinf, log as nplog, r_, iinfo, uint16, asfortranarray
from numpy import copy, pad, zeros, median, asarray, int32, amin, amax
from glob import glob
from tifffile import imread, imsave # only for debug
from os.path import splitext, isfile, isdir

import cv2

#from . import kst_io
#from . import kst_flat_fielding
#from . import kst_matrix_manipulation
#from . import kst_remove_outliers
#from . import kst_ring_removal



def _medfilt(x, k):
	"""Apply a length-k median filter to a 1D array x.
	Boundaries are extended by repeating endpoints.

	Code from https://gist.github.com/bhawkins/3535131

	"""	
	k2 = (k - 1) // 2
	y = zeros((len(x), k), dtype=x.dtype)
	y[:,k2] = x
	for i in range(k2):
		j = k2 - i
		y[j:,i] = x[:-j]
		y[:j,i] = x[0]
		y[:-j,-(i + 1)] = x[j:]
		y[-j:,-(i + 1)] = x[-1]
		
	return median(y, axis=1)


def oimoen(im, n1=21, n2=131):
	"""Process a sinogram image with the Oimoen de-striping algorithm.

	Parameters
	----------
	im : array_like
		Image data as numpy array.

	n1 : int
		Size of the horizontal filtering.

	n2 : int
		Size of the vertical filtering.
	   
	Example (using tifffile.py)
	--------------------------
	>>> im = imread('sino_orig.tif')
	>>> im = oimoen(im, 21, 131)    
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


def post_processing(dset, n1, n2):
	""" Perform post-processing composed of the following steps:
	
		- Ring removal

	"""	
		
	# For each slice:
	for i in range(0, dset.shape[2]):
		
		# Get image:
		im = dset[:,:,i]

		# Padding:
		row_pad = round(im.shape[0] / 4)
		col_pad = round(im.shape[1] / 4)
		im = pad(im, ((row_pad, row_pad), (col_pad, col_pad)), 'edge')

		# Get original size:
		origsize = im.shape

		# Up-scaling:
		im = cv2.resize(im, None, 2, 2, cv2.INTER_CUBIC)

		# Get new shape and center:
		rows, cols = im.shape
		cen_x = im.shape[1] / 2 - 0.5
		cen_y = im.shape[0] / 2 - 0.5

		# Conversion to Polar:
		im = cv2.linearPolar(im, (cen_x, cen_y), amax([rows,cols]), cv2.INTER_CUBIC)

		# Padding for Polar filtering:
		im = pad(im, ((n2, n2), (0, 0)), 'wrap')
		im = pad(im, ((0, 0), (n1, 0)), 'symmetric')

		# Actual filtering:
		im = oimoen(im,n1,n2)

		# Crop after Polar filtering:
		im = im[n2:-n2,n1:]

		# Conversion to Cartesian:
		im = cv2.linearPolar(im, (cen_x, cen_y), amax([rows,cols]), cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP)

		# Down-scaling to original size:
		im = cv2.resize(im, (origsize[0], origsize[1]), interpolation = cv2.INTER_CUBIC)

		# Crop:
		im = im[row_pad:-row_pad,col_pad:-col_pad]

		# Set ouput:
		dset[:,:,i] = im

	# Return:
	return dset
