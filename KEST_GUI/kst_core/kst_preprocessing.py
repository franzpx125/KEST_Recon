from numpy import arange, float32, tile, fromfile, delete, reshape, zeros, array 
from numpy import logical_or, isnan, isinf, log as nplog, r_, iinfo, uint16, asfortranarray
from glob import glob
from tifffile import imread, imsave # only for debug
from os.path import splitext, isfile, isdir


from . import kst_io
from . import kst_flat_fielding
from . import kst_matrix_manipulation
from . import kst_remove_outliers
from . import kst_ring_removal



def pre_processing(dset, rebinning, flatfielding_window, despeckle_thresh, \
				   output_low, output_high, output_diff, output_sum, mode, \
				   crop, proj_avg_mode, proj_avg_alpha, dering_thresh):
	""" Perform pre-processing composed of the following steps:

		- Crop (at first to speed-up everything else)        
		- Projection averaging (if 4D-data with Nan compensation)
		- Removal of the first column (Pixirad has a bad first column)
		- Create energy integrated image (if required)
		- Flat fielding
		- Rebinning (if required)
		- Despeckle with NaNs and Infs removal 
		- Ring removal

	"""	
	
	# Init
	low = None
	high = None
	diff = None
	sum = None

	# Get the portion of the image to process:
	lim = [dset.low.shape[0] - crop[1], dset.low.shape[1] - crop[3]]

	# Crop (check if 4D-data or 3D-data):
	if (dset.low.ndim == 4):		
		low = dset.low[crop[0]:lim[0], crop[2]:lim[1], :, :]
		flat_low = dset.flat_low[crop[0]:lim[0], crop[2]:lim[1], :, :]	
	else:
		low = dset.low[crop[0]:lim[0], crop[2]:lim[1], :]
		flat_low = dset.flat_low[crop[0]:lim[0], crop[2]:lim[1], :]	

	# Projection averaging (only for 4D-data):
	if (low.ndim == 4):
		low = kst_matrix_manipulation.proj_averaging(low, proj_avg_mode, proj_avg_alpha)
		flat_low = kst_matrix_manipulation.proj_averaging(flat_low, proj_avg_mode, proj_avg_alpha)


	# Remove first column (of each image):
	low[:,0,:] = low[:,1,:]
	flat_low[:,0,:] = flat_low[:,1,:]

	if dset.high is not None:

		# Crop (check if 4D-data or 3D-data):
		if (dset.high.ndim == 4):
			high = dset.high[crop[0]:lim[0], crop[2]:lim[1], :, :]
			flat_high = dset.flat_high[crop[0]:lim[0], crop[2]:lim[1], :, :]
		else:
			high = dset.high[crop[0]:lim[0], crop[2]:lim[1], :]
			flat_high = dset.flat_high[crop[0]:lim[0], crop[2]:lim[1], :]


		# Projection averaging (only for 4D-data):
		if (high.ndim == 4):
			high = kst_matrix_manipulation.proj_averaging(high, proj_avg_mode, proj_avg_alpha)
			flat_high = kst_matrix_manipulation.proj_averaging(flat_high, proj_avg_mode, proj_avg_alpha)


		# Remove first column (of each image):
		high[:,0,:] = high[:,1,:]
		flat_high[:,0,:] = flat_high[:,1,:]
	


	# Create energy-integration image (if required):
	if (output_sum):
		sum = low + high
		flat_sum = flat_low + flat_high		


	# Apply flat fielding:
	low = kst_flat_fielding.flat_fielding(low, flat_low, flatfielding_window)
	if dset.high is not None:
		high = kst_flat_fielding.flat_fielding(high, flat_high, flatfielding_window)	

	if (output_sum):
		sum = kst_flat_fielding.flat_fielding(sum, flat_sum, flatfielding_window)	
	
		
	# Apply rebinning (if required):
	if (rebinning):

		# Get new size by calling code once:
		new_im = kst_matrix_manipulation.rebinning2x2(low[:,:,0])
		
		# Prepare output matrix:
		new_low = zeros((new_im.shape[0], new_im.shape[1], low.shape[2]), dtype=low.dtype)
		if dset.high is not None:
			new_high = zeros((new_im.shape[0], new_im.shape[1], high.shape[2]), dtype=high.dtype)
		
		# Do the job:
		for i in range(0, low.shape[2]):
			new_low[:,:,i] = kst_matrix_manipulation.rebinning2x2(low[:,:,i])

		if dset.high is not None:
			for i in range(0, high.shape[2]):
				new_high[:,:,i] = kst_matrix_manipulation.rebinning2x2(high[:,:,i])       

		# Re-assign:
		low = new_low
		if dset.high is not None:
			high = new_high

		# Do-it also for the sum image (if required):
		if (output_sum):
			new_sum = zeros((new_im.shape[0], new_im.shape[1], sum.shape[2]), dtype=sum.dtype) 

			for i in range(0, sum.shape[2]):
				new_sum[:,:,i] = kst_matrix_manipulation.rebinning2x2(sum[:,:,i])

			sum = new_sum

    # Correct outliers:
	low = kst_remove_outliers.despeckle(low, despeckle_thresh, True)	

	# Apply ring removal:
	#for j in range(0, low.shape[0]):
	#	low[j,:,:] = kst_ring_removal.boinhaibel(low[j,:,:].T, dering_thresh).T
	

	if dset.high is not None:		
		# Correct outliers:		
		high = kst_remove_outliers.despeckle(high, despeckle_thresh, True)

		# Apply ring removal:
		#for j in range(0, low.shape[0]):
		#	high[j,:,:] = kst_ring_removal.boinhaibel(high[j,:,:].T, dering_thresh).T


	if (output_sum):		
		# Correct outliers:
		sum = kst_remove_outliers.despeckle(sum, despeckle_thresh, True) 

		# Apply ring removal:
		#for j in range(0, low.shape[0]):
		#	sum[j,:,:] = kst_ring_removal.boinhaibel(sum[j,:,:].T, dering_thresh).T			


	# Compute the subtraction image (if required):
	if (output_diff):
		diff = nplog(high) - nplog(low)				

        # Correct outliers:
		#diff = kst_remove_outliers.despeckle(diff, despeckle_thresh, False) 

		# Apply ring removal:
		#for j in range(0, diff.shape[0]):
		#	diff[j,:,:] = kst_ring_removal.boinhaibel(diff[j,:,:].T, dering_thresh).T	
	

	# Apply log transform (if required):
	if (output_low):
		low = -nplog(low)
	if high is not None:
		high = -nplog(high)	
	if (output_sum):
		sum = -nplog(sum)


	# Return:
	return low, high, diff, sum