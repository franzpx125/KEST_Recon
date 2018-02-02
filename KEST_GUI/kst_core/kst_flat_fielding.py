#
# Author: Francesco Brun
# Last modified: August, 16th 2016
#
from numpy import int_, float32, finfo, gradient, sqrt, ndarray, real, dot, sort
from numpy import std, zeros, cov, diag, mean, sum, ComplexWarning, amin, amax
from numpy import concatenate, tile, median, repeat, newaxis

from numpy.random import randn
from numpy.linalg import eig
from scipy.optimize import fmin

from scipy.ndimage.filters import median_filter
from warnings import simplefilter


def __parallelAnalysis(ff, n):
	""" Select the number of components for PCA using parallel analysis.
	
	Parameters
	----------
	ff : array_like
		Flat field data as numpy array. Each flat field is a single row 
		of this matrix, different rows are different observations.

	n : int
		Number of repetitions for parallel analysis.

	Return value
	------------
	V : array_like
		Eigen values.

	numPC : int
		Number of components for PCA.

	"""
	# Disable a warning:
	simplefilter("ignore", ComplexWarning)
	stdEFF = std(ff, axis=1, ddof=1)

	kpTrk = zeros((ff.shape[1], n), dtype=float32)
	stdMat = tile(stdEFF,(ff.shape[1], 1)).T

	for i in range(0, n):
		
		sample = stdMat * (randn(ff.shape[0], ff.shape[1])).astype(float32)		
		D, V = eig(cov(sample, rowvar=False))
		kpTrk[:,i] = sort(D).astype(float32)

	mean_ff_EFF = mean(ff,axis=1)
	
	F = ff - tile(mean_ff_EFF, (ff.shape[1], 1)).T
	D, V = eig(cov(F, rowvar=False))

	# Sort eigenvalues from smallest to largest:
	idx = D.argsort()   
	D = D[idx]
	V = V[:,idx]

	sel = zeros(ff.shape[1], dtype=float32)	
	sel[D > (mean(kpTrk, axis=1) + 2*std(kpTrk, axis=1, ddof=1))] = 1
	numPC = sum(sel).astype(int_)

	return (V, numPC)


def __condTVmean(proj, meanFF, FF, DS):	
	""" Find the optimal estimates of the coefficients of the eigen flat fields.
	
	"""

	# Downsample images (without interpolation):
	proj = proj[::DS, ::DS]       
	meanFF = meanFF[::DS, ::DS]     
	FF2 = zeros((meanFF.shape[0], meanFF.shape[1], FF.shape[2]), dtype=float32)
	for i in range(0, FF.shape[2]):
		FF2[:,:,i] = FF[::DS, ::DS,i]

	# Optimize coefficients:
	xopt = fmin(func=__f, x0=zeros(FF.shape[2], dtype=float32), args=(proj, meanFF, FF2), disp=False)
	
	return xopt.astype(float32)


def __f(x, proj, meanFF, FF):
	""" Objective function to be minimized.
	
	"""
	FF_eff = zeros((FF.shape[0], FF.shape[1]), dtype=float32)
	
	for i in range(0, FF.shape[2]):		
		FF_eff = FF_eff + x[i]*FF[:,:,i]
	
	corProj = proj / (meanFF + FF_eff + finfo(float32).eps) * mean(meanFF + FF_eff)
	[Gx,Gy] = gradient(corProj) 
	mag  = sqrt(Gx ** 2 + Gy ** 2)
	cost = sum(mag)

	return cost


def dff_prepare_plan(flat_dset, repetitions):
	""" Prepare the Eigen Flat Fields (EFFs) and the filtered EFFs to
	be used for dynamic flat fielding.

	(Function to be called once before the actual filtering of each projection).
	
	Parameters
	----------
	white_dset : array_like
		3D matrix where each flat field image is stacked along the 3rd dimension.

	repetitions: int
		Number of iterations to consider during parallel analysis.

	dark : array_like
		Single dark image (perhaps the average of a series) to be subtracted from
		each flat field image. If the images are already dark corrected or dark
		correction is not required (e.g. due to a photon counting detector) a matrix
		of the proper shape with zeros has to be passed.

	Return value
	------------
	EFF : array_like
		Eigen flat fields stacked along the 3rd dimension.

	filtEFF : array_like
		Filtered eigen flat fields stacked along the 3rd dimension.

	Note
	----
	In this implementation all the collected white field images have to be loaded into
	memory and an internal 32-bit copy of the white fields is created. Considering also
	that the method better performs with several (i.e. hundreds) flat field images, this 
	function might raise memory errors.

	References
	----------
	V. Van Nieuwenhove, J. De Beenhouwer, F. De Carlo, L. Mancini, F. Marone, 
	and J. Sijbers, "Dynamic intensity normalization using eigen flat fields 
	in X-ray imaging", Optics Express, 23(11), 27975-27989, 2015.

	"""	
	# Get dimensions of flat-field (or white-field) images:
	num_flats = flat_dset.shape[2]
	num_rows  = flat_dset.shape[0]
	num_cols  = flat_dset.shape[1]
		
	# Create local copy of white-field dataset:
	tmp_dset = zeros((num_rows * num_cols, num_flats), dtype=float32)
	avg      = zeros((num_rows * num_cols), dtype=float32)
					
	# For all the flat images:
	for i in range(0, tmp_dset.shape[1]):                 
		
		# Read i-th flat image:       
		tmp_dset[:,i] =  flat_dset[:,:,i].astype(float32).flatten()
					
		# Sum the image:
		avg = avg + tmp_dset[:,i]

	# Compute the mean:
	avg = avg / num_flats

	# Subtract mean white-field:
	for i in range(0, tmp_dset.shape[1]): 
		tmp_dset[:,i] = tmp_dset[:,i] - avg
			
	# Calculate the number of Eigen Flat Fields (EFF) to use:
	V, nrEFF = __parallelAnalysis(tmp_dset, repetitions)

	# Compute the EFFs (0-th image is the average "conventional" flat field):
	EFF  = zeros((num_rows, num_cols, nrEFF + 1), dtype=float32)
	EFF[:,:,0] = avg.reshape((num_rows, num_cols))			
	for i in range(0, nrEFF): 		
		EFF[:,:,i + 1] = dot(tmp_dset, V[:,num_flats - (i + 1)]).reshape((num_rows, num_cols))	
		
	# Filter the EFFs:
	filtEFF = zeros((num_rows, num_cols, 1 + nrEFF), dtype=float32)
	for i in range(1, 1 + nrEFF):		
		filtEFF[:,:,i] = median_filter(EFF[:,:,i], 3)		

	return EFF, filtEFF


def dynamic_flat_fielding(im, EFF, filtEFF, downsample):
	""" Apply dynamic flat fielding to input projection image.

	(Function to be called for each projection).
	
	Parameters
	----------
	im : array_like
		The (dark-corrected) projection image to process.
		
	EFF : array_like
		Stack of eigen flat fields as return from the dff_prepare_plan function.

	filtEFF : array_like
		Stack of filtered eigen flat fields as return from dff_prepare_plan.

	downsample: int
		Downsampling factor greater than 2 to be used for the estimates of weights.

	Return value
	------------
	im : array_like
		Filtered projection.

	References
	----------
	V. Van Nieuwenhove, J. De Beenhouwer, F. De Carlo, L. Mancini, F. Marone, 
	and J. Sijbers, "Dynamic intensity normalization using eigen flat fields 
	in X-ray imaging", Optics Express, 23(11), 27975-27989, 2015.

	"""				
	# Cast the input image:
	im = im.astype(float32)
		
	# Estimate weights for a single projection:
	x = __condTVmean(im, EFF[:,:,0], filtEFF[:,:,1:], downsample)

	# Dynamic flat field correction:
	FFeff = zeros(im.shape, dtype=float32)
	for j in range(0, EFF.shape[2] - 1):
		FFeff = FFeff + x[j] * filtEFF[:,:,j + 1]
	
	# Conventional flat fielding (to get mean value):
	tmp = im / (EFF[:,:,0] + finfo(float32).eps)
	tmp[tmp < finfo(float32).eps] = finfo(float32).eps
	mean_val = mean(tmp)

	# Dynamic flat fielding:
	im = im / (EFF[:,:,0] + FFeff + finfo(float32).eps)

	# Re-normalization of the mean with respect to conventional flat fielding:
	im = im / (mean(im) + finfo(float32).eps) * mean_val
			
	# Quick and dirty compensation for detector afterglow:
	#size_ct = 3
	#while ((float(amin(im)) < finfo(float32).eps) and (size_ct <= 7)):			
	#	im_f = median_filter(im, size_ct)
	#	im[im < finfo(float32).eps] = im_f[im < finfo(float32).eps]								
	#	size_ct += 2
				
	#if (float(amin(im)) < finfo(float32).eps):				
	#	im[im < finfo(float32).eps] = finfo(float32).eps	

	# Return pre-processed image:
	return im


def conventional_flat_fielding(im, ff):
	""" Apply conventional flat fielding to the whole input projection dataset.
	
	Parameters
	----------
	im : array_like
		The (dark-corrected) projection images to process.
		
	ff : array_like
		Flat field images.

	Return value
	------------
	im : array_like
		Filtered projections.

	"""				
	# Cast the input image:
	im = im.astype(float32)
		
    # Medianize along the third dimension:
	ff = median(ff, axis=2)

	# Filter the ff image:
	#ff = median_filter(ff, 3)

	# Replicate as many input projections:
	ff = repeat(ff[:, :, newaxis], im.shape[2], axis=2)

	# Conventional flat fielding (point-to-point division):
	im = im / (ff + finfo(float32).eps)	

	# Return pre-processed image:
	return im.astype(float32)




