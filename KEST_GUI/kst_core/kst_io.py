from numpy import arange, tile, fromfile, delete, reshape, zeros
from glob import glob
from tifffile import imread

PIXIRAD_WIDTH = 512 # pixels
PIXIRAD_HEIGHT = 402 # pixels
PIXIRAD_SKIP = 12 # (24 bytes, i.e. 12 pixels)

def read_pixirad_data (filename, mode='2COL', crop=[0,0,0,0]):
	""" Read a single PIXIRAD raw data file as specified in the input filename.

        Parameters
	    ----------
	    filename : string
		    Filename of a pixirad data file.

	    mode : string of the set {'2COL', '1COL'}
		    The single file might contain either 2 images or just one.

        crop : list
		    List having four elements (top, bottom, left, right)

	    Return
	    ----------
	    data | low, high : array_like
		    Image data as 3D matrix (or two 3D matrices)
	
	"""
	# Possible types:
	# '>i2' (big-endian 16-bit signed int)
	# '<i2' (little-endian 16-bit signed int)
	# '<u2' (little-endian 16-bit unsigned int)
	# '>u2' (big-endian 16-bit unsigned int)
	data = fromfile(filename, dtype='<u2')	

	# Skip 24-bytes over each projection:
	size = round(data.shape[0] / (PIXIRAD_WIDTH*PIXIRAD_HEIGHT + PIXIRAD_SKIP))
	a = arange(0,PIXIRAD_SKIP)
	aa = tile(a,(size,1))
	b = (PIXIRAD_WIDTH*PIXIRAD_HEIGHT + PIXIRAD_SKIP)*arange(0,aa.shape[0])
	bb = tile(b.T,(aa.shape[1],1))
	idx = (aa + bb.T).flatten()
	data = delete(data,idx)

	# Reshape and flip:
	data = reshape(data, (PIXIRAD_HEIGHT, PIXIRAD_WIDTH, size),order='F')
	data = data[::-1,:,:]

	if ( mode == '2COL'):
		# Extract low and high:
		low  = data[:,:,::2]
		high = data[:,:,1::2]	

		# Apply crop:
		lim = [ low.shape[0] - crop[1], low.shape[1] - crop[3] ]
		low  = low[ crop[0]:lim[0], crop[2]:lim[1], :]
		high = high[ crop[0]:lim[0], crop[2]:lim[1], :]

		return low, high

	else:
		# Apply crop:
		lim = [ data.shape[0] - crop[1], data.shape[1] - crop[3] ]
		data  = data[ crop[0]:lim[0], crop[2]:lim[1], :]

        # Only 1COL mode is used:
		return data, None



def read_pixirad_stepgo (path, mode='2COL'):
	""" Read a sequence of PIXIRAD raw data as specified in the input path. The 
        output will be a 4D structure having the repetition along the 4-th dim.
        
        Some projection averaging along the 4-th dimension should be considered
        prior to reconstruction.

        Parameters
	    ----------
	    path : string
		    Path where the sequence of pixirad data files are stored. 

	    mode : string of the set {'2COL', '1COL'}
		    The single file might contain either 2 images or just one.

	    Return
	    ----------
	    data | low, high : array_like
		    Image data as 4D matrix (or two 4D matrices)
	
	"""

	tomo_files = sorted(glob(path))
	num_files = len(tomo_files)

    # Read first to understand sizes:
	tomo = read_pixirad_data (tomo_files[0], mode)

	# Prepare dataset:
	data = zeros((tomo.shape[0], tomo.shape[1], tomo.shape[2], num_files), tomo.dtype)

	# Read all files:
	for i in range(0, num_files):    
		
		im = read_pixirad_data (tomo_files[i], mode)
		data[:,:,:,i] = im

	if ( mode == '2COL'):
		# Extract low and high:
		low  = data[:,:,::2,:]
		high = data[:,:,1::2,:]	

		return low, high

	else:
        # Only 1COL mode is used:
		return data, None


def read_tiff_sequence (path):
	"""Read a sequence of TIFF files as specified in the input path.

        Parameters
	    ----------
	    path : string
		    Path where the sequence of TIFF files are located. 

	    Return
	    ----------
	    data : array_like
		    Image data as 3D matrix 
   
    """
	tomo_files = sorted(glob(path))
	num_files = len(tomo_files)

	# Read first to understand sizes:
	tomo = imread(tomo_files[0])

	# Prepare dataset:
	data = zeros((tomo.shape[0], tomo.shape[1], num_files), tomo.dtype)

	# Read all files:
	for i in range(0, num_files):    
		
		im = imread(tomo_files[i])
		data[:,:,i] = im

	return data