from numpy import arange, float32, tile, fromfile, delete, reshape, zeros, log as nplog
from glob import glob
from tifffile import imread
from os.path import splitext

from . import kst_io
from . import kst_remove_outliers
from . import kst_flat_fielding
from . import kst_matrix_manipulation

def pre_processing(low, high, filename, dark_th, hot_th, method, rebinning, logTransform):
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
		low[:,:,i], msk_low[:,:,i] = kst_remove_outliers.pixel_correction(low[:,:,i].astype(float32))

	for i in range(0, flat_low.shape[2]):
		flat_low[:,:,i], msk_flat_low[:,:,i] = kst_remove_outliers.pixel_correction(flat_low[:,:,i].astype(float32))

	for i in range(0, high.shape[2]):
		high[:,:,i], msk_high[:,:,i] = kst_remove_outliers.pixel_correction(high[:,:,i].astype(float32))

	for i in range(0, flat_high.shape[2]):
		flat_high[:,:,i], msk_flat_high[:,:,i] = kst_remove_outliers.pixel_correction(flat_high[:,:,i].astype(float32))


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
		for i in range(0, low.shape[2]):
			low[:,:,i] = kst_matrix_manipulation.rebinning2x2(low[:,:,i])

		for i in range(0, low.shape[2]):
			high[:,:,i] = kst_matrix_manipulation.rebinning2x2(high[:,:,i])

	# Apply log transform (if required):
	if (logTransform):
		low = -nplog(low)
		high = -nplog(high)


	return low, high

