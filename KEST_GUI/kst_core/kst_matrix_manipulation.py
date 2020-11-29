from numpy import float32, pad, arange, repeat, reshape
from numpy import sort, nanmean, nansum, squeeze, rint
from scipy.interpolate import interp2d

import tifffile

def rebinning2x2(im):
	"""Perform 2x2 rebinning (i.e. sum of the gray levels of the 2x2 
	neighborhood).

	Parameters
	----------
	im : array_like
		Image data as numpy array. Note: even-number dimensions required

	Return
	----------
	im : array_like
		Rebinned data.

	"""	
	im = im.astype(float32)

	# Make dimensions odd-size by appending a replica of
	# last-row and last column:
	im = pad(im, ((0,1),(0,1)), 'edge')
	
	# Get Center, East, South and South-East:
	im_C = im[0:-2:2, 0:-2:2]
	im_E = im[0:-2:2, 1:-1:2]
	im_S = im[1:-1:2, 0:-2:2]
	im_SE = im[1:-1:2, 1:-1:2]
	
	return (im_C + im_E + im_S + im_SE).astype(float32)



def upscaling2x2(im, method='repeat'):
	"""Perform 2x2 upscaling with either repetition or interpolation.

	Parameters
	----------
	im : array_like
		Image data as numpy array.

    method : {'repeat','linear','cubic'}
        Type of upscaling used.

	Return
	----------
	im : array_like
		Upscaled data.

	"""	
	im = im.astype(float32)
	orig_shape = im.shape

	if method == 'repeat':

		im = repeat(im,2,axis=0)
		im = reshape(im, (orig_shape[0]*2, orig_shape[1]), order='F')
			
		im = repeat(im,2,axis=1)
		im = reshape(im, (orig_shape[0]*2, orig_shape[1]*2), order='F')

	else:

		# Define input grid:
		x = arange(0, im.shape[0], 1)
		y = arange(0, im.shape[1], 1)

		# Get the interpolant function:
		f = interp2d(y, x, im, kind=method)

		# Define the output grid:
		x_out = arange(0, im.shape[0], 0.5)
		y_out = arange(0, im.shape[1], 0.5)

		# Apply interpolation:
		#im = f(y_out, x_out)

	return im.astype(float32)



def proj_averaging(im, method='average', alpha=2):
	"""Perform alpha-trimmed projection averaging or selection.

	Parameters
	----------
	im : array_like
		Image data as 4D numpy array (the 4-th 
		dimension is the dimension to process).

	method : {'median','average','sum','minimum,'maximum','extract'}
		Type of projection averaging.

	alpha

	Return
	----------
	im : array_like
		Image data as 3D numpy array.

	"""	

	# Extraction does not need sorting:
	if (method == 'extract'):
		if ((alpha >= 0) and (alpha < im.shape[3])):
			im = im[:,:,:,alpha]
		else:
			# Default extraction with 0-th image:
			im = im[:,:,:,0]

	elif (method == 'sum'):	
			if ((alpha >= 0) and (alpha < im.shape[3])):
				im = im[:,:,:,0:alpha]
				im = nansum(im, axis=3)
			else:
				# Sum all:
				im = nansum(im, axis=3)
	
	else:
        # Combine remaining images:
		im = sort(im, axis=3)
		# Perform alpha-trimming (if alpha == 0 do nothing):
		if ((alpha > 0) and (alpha < rint(im.shape[3] / 2))):					
			im = im[:,:,:,alpha:-alpha]

		if (method == 'median'):
			im = im[:,:,:,rint(im.shape[3] / 2.0)]
		elif (method == 'minimum'):
			im = im[:,:,:,0]
		elif (method == 'maximum'):
			im = im[:,:,:,-1]
		else: # 'average'
			im = nanmean(im.astype(float32), axis=3)

	# Remove the 4th dimension (usually not necessary):
	im = squeeze(im)

	return im