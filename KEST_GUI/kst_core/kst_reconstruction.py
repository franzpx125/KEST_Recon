from numpy import float32, linspace, transpose, roll, squeeze, zeros, float32
from numpy import absolute, arange, tile, newaxis, real, pad, pi, finfo

from pyfftw import n_byte_align, simd_alignment
from pyfftw.interfaces.numpy_fft import rfft, irfft

#import astra
from . import kst_tigre_FDK


def correct_dataset(proj, offset_u=0, offset_v=0, overpadding=False):  	
	"""Apply corrections.

	Parameters

	"""
	# Correct horizontal offset:
	k_u = int(round(offset_u))
	if (overpadding):
		val = int(round(proj.shape[1] /4))
		
		proj = pad(proj, ((0,0), (val + k_u, val - k_u), (0,0)), 'edge')
	else:        
		if ( k_u > 0 ):
			
			proj = pad(proj, ((0,0), (k_u, 0), (0,0)), 'edge')
			proj = proj[:,:-k_u,:]
		else:
			proj = pad(proj, ((0,0), (0, abs(k_u)), (0,0)), 'edge')
			proj = proj[:,abs(k_u):,:]

	# Correct vertical offset:
	k_v = int(round(offset_v))
	if ( k_v > 0 ):
			
		proj = pad(proj, ((k_v, 0), (0,0), (0,0)), 'edge')
		proj = proj[:-k_v,:,:]
	else:
		proj = pad(proj, ((0, abs(k_v)), (0,0), (0,0)), 'edge')
		proj = proj[abs(k_v):,:,:]


    # Return:
	if (overpadding):
		return proj, val
	else:
		return proj, None


def recon_tigre_fdk(proj, ssd, sdd, pixel_size, angles=2*pi, angles_shift=0, 
                   offset_u=0.0, offset_v=0.0, roll_deg=0.0, pitch_deg=0.0, 
                   yaw_deg=0.0, short_scan=False, overpadding=False, filter='ram-lak'):
	"""Reconstruct the input dataset by using the FDK implemented in TIGRE.

    Parameters
    ----------
    proj : array_like
		Image data (3D set of projections) as numpy array. 	

	ssd : double [mm]
		Source-sample distance.

    ssd : double [mm]
		Sample-detector distance.

    pixel_size : double [mm]
		Size of each detector pixel (square pixels assumed).

    angles : double [radians]
		Scalar value in radians representing the number of covered angles.

    angles_shift : double [radians]
        Lossless rotation of the reconstructed images.

    offset_u : double [pixel]
        Horizontal detector offset.

    offset_v : double [pixel]
        Vertical detector offset.

    roll_deg : double [degrees]
        Detector correction.

    pitch_deg : double [degrees]
        Detector correction.
        
    yaw_deg : double [degrees]
        Detector correction.

    filter : string
		The available options are "ram-lak", "shepp-logan", "cosine", "hamming", "hann".

	short_scan : bool
		Use Parker weights for short scan (i.e. 180 deg plus twice the cone angle).	

	"""  
	# Pad:
	if (overpadding):
		val = int(round(proj.shape[1] /4))				
		proj = pad(proj, ((0,0), (val, val), (0,0)), 'edge')

	# Actual reconstruction:
	rec = kst_tigre_FDK.FDK(proj, ssd, sdd, pixel_size, offset_u, offset_v, roll_deg, \
		pitch_deg, yaw_deg, filter, angles, angles_shift)

	# Crop:
	if (overpadding):
		rec = rec[val:-val, val:-val,:] 

	return rec


def recon_astra_fdk(proj, angles, ssd, sdd, pixel_size, offset_u, offset_v, 
                    short_scan=False, overpadding=False, angles_shift=0):
	"""Reconstruct the input dataset by using the FDK implemented in ASTRA toolbox.

    Parameters
    ----------
    proj : array_like
		Image data (3D set of projections) as numpy array. 

	angles : double [radians]
		Value in radians representing the number of covered angles of the CT dataset.

	ssd : double [mm]
		Source-sample distance.

    ssd : double [mm]
		Sample-detector distance.

    pixel_size : double [mm]
		Size of each detector pixel (square pixels assumed).

    offset_u : int [pixel]
        Horizontal detector offset.

    offset_v : int [pixel]
        Vertical detector offset.

	short_scan : bool
		Use Parker weights for short scan (i.e. 180 deg plus twice the cone angle).	

    """
    # Reassignment for compatibility with previously developed code: 	
	px = pixel_size

	magn   = (ssd + sdd) / ssd
	vol_px = px / magn	


	# Get dims:
	nr_proj = proj.shape[2] 
	det_row = proj.shape[0] 
	det_col = proj.shape[1] 
	
    # See comments in astra.data3d.create('-proj3d'):
	proj = transpose(proj,(0,2,1))

	# Create output geometry (voxelsize = 1, everything should be rescaled):
	vol_geom = astra.create_vol_geom(det_col, det_col, det_row)

    # Create projection geometry:
    # Parameters: width of detector column, height of detector row, #rows, 
    # #columns, angles, distance source-origin, distance origin-detector
	ang_range = linspace(0 + angles_shift, angles + angles_shift, nr_proj, False)
	proj_geom = astra.create_proj_geom('cone', px/vol_px, px/vol_px, det_row, \
		det_col, ang_range, ssd/vol_px, sdd/vol_px)
	
	# Create a data object for the reconstruction
	rec_id = astra.data3d.create('-vol', vol_geom)	

	# Create a data object for the projection. Data must be of size 
    # (u,angles,v), where u is the number of columns of the detector 
    # and v the number of rows:
	proj_id = astra.data3d.create('-proj3d', proj_geom, proj)

	# Create configuration:
	cfg = astra.astra_dict('FDK_CUDA')
	cfg['ReconstructionDataId'] = rec_id
	cfg['ProjectionDataId'] = proj_id

	cfg['option'] = {}
	cfg['option']['ShortScan'] = short_scan
	
	# Create and run the algorithm object from the configuration structure:
	alg_id = astra.algorithm.create(cfg)
	astra.algorithm.run(alg_id, 1)

	# Get the result and permute:
	rec = astra.data3d.get(rec_id)
	rec = transpose(rec,(1,2,0) )

	# Clean up GPU memory:
	astra.algorithm.delete(alg_id)
	astra.data3d.delete(rec_id)
	astra.data3d.delete(proj_id)

    # Return:
	return rec


def recon_astra_fbp(proj, angles, angles_shift=0):
	"""Reconstruct the input dataset by using the BP implemented in ASTRA toolbox
       and ram-lak filtering.

    Parameters
    ----------
    proj : array_like
		Image data (3D set of projections) as numpy array. 

	angles : double [radians]
		Value in radians representing the number of covered angles of the CT dataset.

    offset_u : int [pixel]
        Horizontal detector offset.

    """
    # Get infos:
	nr_proj = proj.shape[2] 
	det_row = proj.shape[0] 
	det_col = proj.shape[1] 

	# Ram-Lak filtering:	
	S = rfft(proj, axis=1, threads=2)
	siz = S.shape[1]
	ramp = -2 * absolute(arange(siz) - siz/2) / siz + 1
	ramp = tile(ramp[newaxis,:,newaxis], (det_row, 1, nr_proj))
	S = S * ramp
	proj = real(irfft(S, axis=1)).astype(float32)
	
    # See comments in astra.data3d.create('-proj3d'):
	proj = transpose(proj,(0,2,1))

	# Create output geometry (voxelsize = 1, everything should be rescaled):
	vol_geom = astra.create_vol_geom(det_col, det_col, det_row)

    # Create projection geometry:
    # Parameters: width of detector column, height of detector row, #rows, 
	# #columns, angles, distance source-origin, distance origin-detector
	ang_range = linspace(0 + angles_shift, angles + angles_shift, nr_proj, False)
	proj_geom = astra.create_proj_geom('parallel3d', 1.0, 1.0, det_row, det_col, ang_range)
	
	# Create a data object for the reconstruction
	rec_id = astra.data3d.create('-vol', vol_geom)	

	# Create a data object for the projection. Data must be of size 
    # (u,angles,v), where u is the number of columns of the detector 
    # and v the number of rows:
	proj_id = astra.data3d.create('-proj3d', proj_geom, proj)

	# Create configuration:
	cfg = astra.astra_dict('BP3D_CUDA')
	cfg['ReconstructionDataId'] = rec_id
	cfg['ProjectionDataId'] = proj_id
	
	# Create and run the algorithm object from the configuration structure:
	alg_id = astra.algorithm.create(cfg)
	astra.algorithm.run(alg_id)

	# Get the result and permute:
	rec = astra.data3d.get(rec_id)
	rec = transpose(rec,(1,2,0) )

	# Clean up GPU memory:
	astra.algorithm.delete(alg_id)
	astra.data3d.delete(rec_id)
	astra.data3d.delete(proj_id)
	
    # Return:
	return rec


def recon_astra_sirt_cone(proj, angles, ssd, sdd, pixel_size, iterations=100, angles_shift=0):
	"""Reconstruct the input dataset by using the SIRT3D implemented in ASTRA toolbox.

    Parameters
    ----------
    proj : array_like
		Image data (3D set of projections) as numpy array. 

	angles : double [radians]
		Value in radians representing the number of covered angles of the CT dataset.

	ssd : double [mm]
		Source-sample distance.

    ssd : double [mm]
		Sample-detector distance.

    pixel_size : double [mm]
		Size of each detector pixel (square pixels assumed).

    offset_u : int [pixel]
        Horizontal detector offset.

    offset_v : int [pixel]
        Vertical detector offset.

	iterations : int
		Number of iterations for the algebraic solution.	

    """
    # Reassignment for compatibility with previously developed code: 	
	px = pixel_size

	magn   = (ssd + sdd) / ssd
	vol_px = px / magn

	nr_proj = proj.shape[2] 
	det_row = proj.shape[0] 
	det_col = proj.shape[1] 
	
    # See comments in astra.data3d.create('-proj3d'):
	proj = transpose(proj,(0,2,1))

	# Create output geometry (voxelsize = 1, everything should be rescaled):
	vol_geom = astra.create_vol_geom(det_col, det_col, det_row)

    # Create projection geometry:
    # Parameters: width of detector column, height of detector row, #rows, 
	# #columns, angles, distance source-origin, distance origin-detector
	ang_range = linspace(0 + angles_shift, angles + angles_shift, nr_proj, False)
	proj_geom = astra.create_proj_geom('cone', px/vol_px, px/vol_px, det_row, \
		det_col, ang_range, ssd/vol_px, sdd/vol_px)
	
	# Create a data object for the reconstruction
	rec_id = astra.data3d.create('-vol', vol_geom)	

	# Create a data object for the projection. Data must be of size 
    # (u,angles,v), where u is the number of columns of the detector 
    # and v the number of rows:
	proj_id = astra.data3d.create('-proj3d', proj_geom, proj)

	# Create configuration:
	cfg = astra.astra_dict('SIRT3D_CUDA')
	cfg['ReconstructionDataId'] = rec_id
	cfg['ProjectionDataId'] = proj_id

	
	# Create and run the algorithm object from the configuration structure:
	alg_id = astra.algorithm.create(cfg)
	astra.algorithm.run(alg_id, iterations)

	# Get the result and permute:
	rec = astra.data3d.get(rec_id)
	rec = transpose(rec,(1,2,0) )

	# Clean up GPU memory:
	astra.algorithm.delete(alg_id)
	astra.data3d.delete(rec_id)
	astra.data3d.delete(proj_id)
	
    # Return:
	return rec


def recon_astra_sirt_parallel(proj, angles, iterations=100, angles_shift=0):
	"""Reconstruct the input dataset by using the FBP implemented in ASTRA toolbox.

    Parameters
    ----------
    proj : array_like
		Image data (3D set of projections) as numpy array. 

	angles : double [radians]
		Value in radians representing the number of covered angles of the CT dataset.

    offset_u : int [pixel]
        Horizontal detector offset.

    iterations : int
		Number of iterations for the algebraic solution.	

    """
    # Get infos:
	nr_proj = proj.shape[2] 
	det_row = proj.shape[0] 
	det_col = proj.shape[1] 

    # See comments in astra.data3d.create('-proj3d'):
	proj = transpose(proj,(0,2,1))

	# Create output geometry (voxelsize = 1, everything should be rescaled):
	vol_geom = astra.create_vol_geom(det_col, det_col, det_row)

    # Create projection geometry:
    # Parameters: width of detector column, height of detector row, #rows, 
    # #columns, angles, distance source-origin, distance origin-detector
	ang_range = linspace(0 + angles_shift, angles + angles_shift, nr_proj, False)
	proj_geom = astra.create_proj_geom('parallel3d', 1.0, 1.0, det_row, det_col, ang_range)
	
	# Create a data object for the reconstruction
	rec_id = astra.data3d.create('-vol', vol_geom)	

	# Create a data object for the projection. Data must be of size 
    # (u,angles,v), where u is the number of columns of the detector 
    # and v the number of rows:
	proj_id = astra.data3d.create('-proj3d', proj_geom, proj)

	# Create configuration:
	cfg = astra.astra_dict('SIRT3D_CUDA')
	cfg['ReconstructionDataId'] = rec_id
	cfg['ProjectionDataId'] = proj_id

	
	# Create and run the algorithm object from the configuration structure:
	alg_id = astra.algorithm.create(cfg)
	astra.algorithm.run(alg_id, iterations)

	# Get the result and permute:
	rec = astra.data3d.get(rec_id)
	rec = transpose(rec,(1,2,0) )

	# Clean up GPU memory:
	astra.algorithm.delete(alg_id)
	astra.data3d.delete(rec_id)
	astra.data3d.delete(proj_id)
	
    # Return:
	return rec