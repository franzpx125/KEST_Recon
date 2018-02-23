from numpy import arange, float32, tile, fromfile, delete, reshape, zeros, log as nplog, r_
from glob import glob
from tifffile import imread
from os.path import splitext

from . import kst_io
from . import kst_remove_outliers
from . import kst_flat_fielding
from . import kst_matrix_manipulation

# TO DO: play better with masks (they have to be rebinned as well)


def pre_processing( filename, low_dark_th, low_hot_th, high_dark_th, high_hot_th, \
                    rebinning, flatfielding_window, despeckle_window, despeckle_thresh, \
                    output_low, output_high, output_diff, output_sum ):
	""" Perform pre-processing
	"""
	# Open the flat image by manipulating the orig filename:
	name, ext = splitext(filename)
	flat_filename = name + '_flat' + ext

	# Read high low and high (as well as flat data):
	low, high = kst_io.read_pixirad_data(filename)
	flat_low, flat_high = kst_io.read_pixirad_data(flat_filename)


	# Prepare masks:
	msk_low = zeros(low.shape, dtype=bool)
	msk_flat_low = zeros(flat_low.shape, dtype=bool)
	msk_high = zeros(low.shape, dtype=bool)
	msk_flat_high = zeros(flat_low.shape, dtype=bool)

	# Prepare subtraction and energy integration image:
	diff = zeros(low.shape, dtype=bool)
	sum = zeros(low.shape, dtype=bool)


	# Apply defect correction:
	for i in range(0, low.shape[2]):
        # Remove first column:
		tmp_im = low[:,1:,i]
		low[:,:,i] = tmp_im[:,r_[0,:tmp_im.shape[1]]]
		low[:,:,i], msk_low[:,:,i] = kst_remove_outliers.pixel_correction(low[:,:,i], low_dark_th, low_hot_th)
		
	for i in range(0, flat_low.shape[2]):
        # Remove first column:
		tmp_im = flat_low[:,1:,i]
		flat_low[:,:,i] = tmp_im[:,r_[0,:tmp_im.shape[1]]]
		flat_low[:,:,i], msk_flat_low[:,:,i] = kst_remove_outliers.pixel_correction(flat_low[:,:,i], low_dark_th, low_hot_th)
		
	for i in range(0, high.shape[2]):
        # Remove first column:
		tmp_im = high[:,1:,i]
		high[:,:,i] = tmp_im[:,r_[0,:tmp_im.shape[1]]]
		high[:,:,i], msk_high[:,:,i] = kst_remove_outliers.pixel_correction(high[:,:,i], high_dark_th, high_hot_th)
		
	for i in range(0, flat_high.shape[2]):
        # Remove first column:
		tmp_im = flat_high[:,1:,i]
		flat_high[:,:,i] = tmp_im[:,r_[0,:tmp_im.shape[1]]]
		flat_high[:,:,i], msk_flat_high[:,:,i] = kst_remove_outliers.pixel_correction(flat_high[:,:,i], high_dark_th, high_hot_th)		

	# Create energy-integration image (if required):
	if (output_sum):
		sum = low + high
		flat_sum = flat_low + flat_high
		


	# Apply flat fielding:
	low = kst_flat_fielding.flat_fielding(low, flat_low, flatfielding_window)
	high = kst_flat_fielding.flat_fielding(high, flat_high, flatfielding_window)	

	if (output_sum):
		sum = kst_flat_fielding.flat_fielding(sum, flat_sum, flatfielding_window)	
	


	# Apply rebinning (if required):
	if (rebinning):

		# Get new size by calling code once:
		new_im = kst_matrix_manipulation.rebinning2x2(low[:,:,0])
		
		# Prepare output matrix:
		new_low = zeros( (new_im.shape[0], new_im.shape[1], low.shape[2]), dtype=low.dtype )
		new_high = zeros( (new_im.shape[0], new_im.shape[1], high.shape[2]), dtype=high.dtype )
		
		# Do the job:
		for i in range(0, low.shape[2]):
			new_low[:,:,i] = kst_matrix_manipulation.rebinning2x2(low[:,:,i])

		for i in range(0, high.shape[2]):
			new_high[:,:,i] = kst_matrix_manipulation.rebinning2x2(high[:,:,i])       

		# Re-assign:
		low = new_low
		high = new_high

		# Do-it also for the sum image (if required):
		if (output_sum):
			new_sum = zeros( (new_im.shape[0], new_im.shape[1], sum.shape[2]), dtype=sum.dtype ) 

			for i in range(0, sum.shape[2]):
				new_sum[:,:,i] = kst_matrix_manipulation.rebinning2x2(sum[:,:,i])

			sum = new_sum



	# Apply despeckle and afterglow correction:
	for i in range(0, low.shape[2]):
		low[:,:,i] = kst_remove_outliers.despeckle_filter(low[:,:,i], despeckle_thresh, despeckle_window)
		low[:,:,i] = kst_remove_outliers.afterglow_correction(low[:,:,i])
	
	for i in range(0, high.shape[2]):
		high[:,:,i] = kst_remove_outliers.despeckle_filter(high[:,:,i], despeckle_thresh, despeckle_window)
		high[:,:,i] = kst_remove_outliers.afterglow_correction(high[:,:,i])

	if (output_sum):
		for i in range(0, sum.shape[2]):
			sum[:,:,i] = kst_remove_outliers.despeckle_filter(sum[:,:,i], despeckle_thresh, despeckle_window)
			sum[:,:,i] = kst_remove_outliers.afterglow_correction(sum[:,:,i])  


	# Compute the subtraction image (if required):
	if (output_diff):
		diff = nplog(high) - nplog(low)
	

	# Apply log transform (if required):
	low = -nplog(low)
	high = -nplog(high)
	
	if (output_sum):
		sum = -nplog(sum)


	return low, high, diff, sum

