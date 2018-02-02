from numpy import arange, float32, tile, fromfile, delete, reshape, zeros, log as nplog
from glob import glob
from tifffile import imread
from os.path import splitext

from . import kst_io
from . import kst_remove_outliers
from . import kst_flat_fielding
from . import kst_matrix_manipulation

def pre_processing(low, high, filename, low_dark_th, low_hot_th, high_dark_th, \
         high_hot_th, method, rebinning, logTransform):
	""" Perform pre-processing
	"""
	# Open the flat image by manipulating the orig filename:
	name, ext = splitext(filename)
	flat_filename = name + '_flat' + ext
	flat_low, flat_high = kst_io.read_pixirad_data(flat_filename)

	msk_low = zeros(low.shape, dtype=bool)
	msk_flat_low = zeros(flat_low.shape, dtype=bool)
	msk_high = zeros(low.shape, dtype=bool)
	msk_flat_high = zeros(flat_low.shape, dtype=bool)

	# Apply defect correction:
	for i in range(0, low.shape[2]):
		low[:,:,i], msk_low[:,:,i] = kst_remove_outliers.pixel_correction(low[:,:,i], low_dark_th, low_hot_th)
		#low[:,:,i] = kst_remove_outliers.despeckle_filter(low[:,:,i])

	for i in range(0, flat_low.shape[2]):
		flat_low[:,:,i], msk_flat_low[:,:,i] = kst_remove_outliers.pixel_correction(flat_low[:,:,i], low_dark_th, low_hot_th)
		#flat_low[:,:,i] = kst_remove_outliers.despeckle_filter(flat_low[:,:,i])

	for i in range(0, high.shape[2]):
		high[:,:,i], msk_high[:,:,i] = kst_remove_outliers.pixel_correction(high[:,:,i], high_dark_th, high_hot_th)
		#high[:,:,i] = kst_remove_outliers.despeckle_filter(high[:,:,i])

	for i in range(0, flat_high.shape[2]):
		flat_high[:,:,i], msk_flat_high[:,:,i] = kst_remove_outliers.pixel_correction(flat_high[:,:,i], high_dark_th, high_hot_th)
		#flat_high[:,:,i] = kst_remove_outliers.despeckle_filter(flat_high[:,:,i])


    # Apply actual flatfielding:
	if (method == 0): # 'conventional'
		low = kst_flat_fielding.conventional_flat_fielding(low, flat_low)
		high = kst_flat_fielding.conventional_flat_fielding(high, flat_high)
	else:
		# TO DO: dynamic flat fielding:
		low = kst_flat_fielding.conventional_flat_fielding(low, flat_low)
		high = kst_flat_fielding.conventional_flat_fielding(high, flat_high)

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

		for i in range(0, low.shape[2]):
			new_high[:,:,i] = kst_matrix_manipulation.rebinning2x2(high[:,:,i])

        # Re-assign:
		low = new_low
		high = new_high


    # Apply afterglow correction:
	for i in range(0, low.shape[2]):
		low[:,:,i] = kst_remove_outliers.afterglow_correction(low[:,:,i])

	for i in range(0, high.shape[2]):
		high[:,:,i] = kst_remove_outliers.afterglow_correction(high[:,:,i])

	
    # Apply log transform (if required):
	if (logTransform):
		low = -nplog(low)
		high = -nplog(high)


    # Re-apply defect correction:
	#for i in range(0, low.shape[2]):
	#	low[:,:,i], msk_low[:,:,i] = kst_remove_outliers.pixel_correction(low[:,:,i])
	#	low[:,:,i] = kst_remove_outliers.despeckle_filter(low[:,:,i])

	#	high[:,:,i], msk_high[:,:,i] = kst_remove_outliers.pixel_correction(high[:,:,i])
	#	high[:,:,i] = kst_remove_outliers.despeckle_filter(high[:,:,i])

	return low, high

