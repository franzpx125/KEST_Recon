from numpy import float32, linspace, transpose, roll

import astra

def recon_astra_fdk(proj, angles, ssd, sdd, pixel_size, offset_u, offset_v, short_scan=False):
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

	nr_proj = proj.shape[2] 
	det_row = proj.shape[0] 
	det_col = proj.shape[1] 

	# Handle center of rotation (no internal handling by ASTRA):
	proj = roll(proj,round(offset_u), 1)
	proj = roll(proj,round(offset_v), 0)
	
    # See comments in astra.data3d.create('-proj3d'):
	proj = transpose(proj,(0,2,1))

	# Create output geometry (voxelsize = 1, everything should be rescaled):
	vol_geom = astra.create_vol_geom(det_col, det_col, det_row)

    # Create projection geometry:
    # Parameters: width of detector column, height of detector row, #rows, 
    # #columns, angles, distance source-origin, distance origin-detector
	proj_geom = astra.create_proj_geom('cone', px/vol_px, px/vol_px, det_row, \
        det_col, linspace(0, angles, nr_proj, False), ssd/vol_px, sdd/vol_px)
	
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

def recon_astra_sirt(proj, angles, ssd, sdd, pixel_size, offset_u, offset_v, iterations=100):
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

	short_scan : bool
		Use Parker weights for short scan (i.e. 180 deg plus twice the cone angle).	

    """
    # Reassignment for compatibility with previously developed code: 	
	px = pixel_size

	magn   = (ssd + sdd) / ssd
	vol_px = px / magn

	nr_proj = proj.shape[2] 
	det_row = proj.shape[0] 
	det_col = proj.shape[1] 

	# Handle center of rotation (no internal handling by ASTRA):
	proj = roll(proj,round(offset_u), 1)
	proj = roll(proj,round(offset_v), 0)
	
    # See comments in astra.data3d.create('-proj3d'):
	proj = transpose(proj,(0,2,1))

	# Create output geometry (voxelsize = 1, everything should be rescaled):
	vol_geom = astra.create_vol_geom(det_col, det_col, det_row)

    # Create projection geometry:
    # Parameters: width of detector column, height of detector row, #rows, 
    # #columns, angles, distance source-origin, distance origin-detector
	proj_geom = astra.create_proj_geom('cone', px/vol_px, px/vol_px, det_row, \
        det_col, linspace(0, angles, nr_proj, False), ssd/vol_px, sdd/vol_px)
	
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

#def recon_astra_iterative(im, angles, method, iterations, zerone_mode):
#	"""Reconstruct the input sinogram by using one of the iterative algorithms implemented in ASTRA toolbox.

#    Parameters
#    ----------
#    im : array_like
#		Image data (sinogram) as numpy array. 

#	angles : double
#		Value in radians representing the number of angles of the sinogram.

#	method : string
#		A string with e.g "SIRT" or "SIRT_CUDA" (see ASTRA documentation)

#	iterations : int
#		Number of iterations for the algebraic technique

#	zerone_mode : bool
#		True if the input sinogram has been rescaled to the [0,1] range (therefore positivity 
#		constraints are applied)
	
	
#    """
#	if (method == "SART_CUDA") or (method == "SART"):
#		iterations = int(round(float(iterations))) * im.shape[0]
		
#	vol_geom = astra.create_vol_geom(im.shape[1] , im.shape[1])
#	proj_geom = astra.create_proj_geom('parallel', 1.0, im.shape[1], linspace(0,angles,im.shape[0],False))
	
#	if not (method.endswith("CUDA")):
#		proj_id = astra.create_projector('strip', proj_geom, vol_geom) # Only for CPU-based algorithms
	
#	# Create a data object for the reconstruction
#	rec_id = astra.data2d.create('-vol', vol_geom)

#	# We now re-create the sinogram data object:
#	sinogram_id = astra.data2d.create('-sino', proj_geom, im)

#	# Create configuration:
#	cfg = astra.astra_dict(method)
#	cfg['ReconstructionDataId'] = rec_id
#	cfg['ProjectionDataId'] = sinogram_id
	
#	if not (method.endswith("CUDA")):
#		cfg['ProjectorId'] = proj_id # Only for CPU-based algorithms
	
#	cfg['option'] = {}	
	
#	if (method.startswith("SART")):
#		cfg['option']['ProjectionOrder'] = 'random'
#	#if (zerone_mode) and (method != "CGLS_CUDA"):
#		#cfg['option']['MinConstraint'] = 0
#		#cfg['option']['MaxConstraint'] = 1	

#	#overSampling = False
#	#if (overSampling == True):
#	#	cfg['option']['DetectorSuperSampling'] = 2
#	#	cfg['option']['PixelSuperSampling'] = 2
	

#	# Create and run the algorithm object from the configuration structure
#	alg_id = astra.algorithm.create(cfg)
#	astra.algorithm.run(alg_id, int(round(float(iterations))))

#	# Get the result
#	rec = astra.data2d.get(rec_id)

#	# Clean up:
#	astra.algorithm.delete(alg_id)
#	astra.data2d.delete(rec_id)
#	astra.data2d.delete(sinogram_id)	
#	if not (method.endswith("CUDA")):
#		astra.projector.delete(proj_id) # For CPU-based algorithms
	
#	return rec