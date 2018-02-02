from numpy import arange, tile, fromfile, delete, reshape, zeros
from glob import glob
from tifffile import imread

PIXIRAD_WIDTH = 512 # pixels
PIXIRAD_HEIGHT = 402 # pixels
PIXIRAD_SKIP = 12 # (24 bytes, i.e. 12 pixels)

def read_pixirad_data (filename):
	"""Read the PIXIRAD raw data.
   
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

    # Extract low and high:
	low  = data[:,:,::2]
	high = data[:,:,1::2]	

	return low, high

def read_tiff_sequence (path):
	"""Read a sequence of TIFF files as specified in the input path.
   
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