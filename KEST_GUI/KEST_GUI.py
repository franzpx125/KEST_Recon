﻿import sys
import tifffile 
import h5py
import numpy as np
import math

#import kst_core.kst_io as kst_io
#import kst_core.kst_flat_fielding as kst_flat_fielding
#import kst_core.kst_remove_outliers as kst_remove_outliers
#import kst_core.kst_matrix_manipulation as kst_matrix_manipulation
#import kst_core.kst_reconstruction as kst_reconstruction
import kst_core.kst_preprocessing as kst_preprocessing
#import kst_core.kst_tigre_FDK as kst_tigre_FDK
#import kst_core.kst_astra_TVRDART as kst_astra_TVRDART
from kstDataset import kstDataset

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QTimer, QCoreApplication

#from kstImageViewer import kstImageViewer
#from VoxImagePanel import VoxImagePanel
#from VoxHDFViewer import VoxHDFViewer
#from VoxSidebar import VoxSidebar
#from VoxMainPanel import VoxMainPanel
from kstMainWindow import kstMainWindow


import copy
from tifffile import imread, imsave

class Redirect(object):
	""" Trivial class used to redirect print() command to a QT widget.
	"""
	def __init__(self, widget):
		""" Class constructor.
		"""
		self.wg = widget


	def write(self, text):
		""" Forwarding of a print() command.
		"""

        # Append without new line:
		self.wg.append(text)


from numpy import arange, float32, tile, fromfile, delete, reshape, zeros, array, finfo, ndarray 
from numpy import logical_or, isnan, isinf, log as nplog, r_, iinfo, uint16, asfortranarray
from numpy import copy, pad, zeros, median, asarray, int32, amin, amax
from glob import glob
from tifffile import imread, imsave # only for debug
from os.path import splitext, isfile, isdir

import cv2

#from . import kst_io
#from . import kst_flat_fielding
#from . import kst_matrix_manipulation
#from . import kst_remove_outliers
#from . import kst_ring_removal



def _medfilt(x, k):
	"""Apply a length-k median filter to a 1D array x.
	Boundaries are extended by repeating endpoints.

	Code from https://gist.github.com/bhawkins/3535131

	"""	
	k2 = (k - 1) // 2
	y = zeros((len(x), k), dtype=x.dtype)
	y[:,k2] = x
	for i in range(k2):
		j = k2 - i
		y[j:,i] = x[:-j]
		y[:j,i] = x[0]
		y[:-j,-(i + 1)] = x[j:]
		y[-j:,-(i + 1)] = x[-1]
		
	return median(y, axis=1)


def oimoen(im, n1=21, n2=131):
	"""Process a sinogram image with the Oimoen de-striping algorithm.

	Parameters
	----------
	im : array_like
		Image data as numpy array.

	n1 : int
		Size of the horizontal filtering.

	n2 : int
		Size of the vertical filtering.
	   
	Example (using tifffile.py)
	--------------------------
	>>> im = imread('sino_orig.tif')
	>>> im = oimoen(im, 21, 131)    
	>>> imsave('sino_flt.tif', im) 

	References
	----------
	M.J. Oimoen, An effective filter for removal of production artifacts in U.S. 
	geological survey 7.5-minute digital elevation models, Proc. of the 14th Int. 
	Conf. on Applied Geologic Remote Sensing, Las Vegas, Nevada, 6-8 November, 
	2000, pp. 311-319.

	"""    

	# Padding:
	im = pad(im, ((n2 + n1, n2 + n1), (0, 0)), 'symmetric')
	im = pad(im, ((0, 0), (n1 + n2, n1 + n2)), 'edge')

	im1 = im.copy()

	# Horizontal median filtering:
	for i in range(0, im1.shape[0]):

		im1[i,:] = _medfilt(im1[i,:], n1)        

	# Create difference image (high-pass filter):
	diff = im - im1

	# Vertical filtering:
	for i in range(0, diff.shape[1]):

		diff[:,i] = _medfilt(diff[:,i], n2)

	# Compensate output image:
	im = im - diff

	# Crop padded image:
	im = im[(n2 + n1):im.shape[0] - (n1 + n2), (n1 + n2):im.shape[1] - (n1 + n2)]	

	# Return image according to input type:
	return im.astype(float32)


def post_processing(dset, n1, n2):
	""" Perform post-processing composed of the following steps:
	
		- Ring removal

	"""	
	out_path = 'J:\\Zacchigna\\topo_completo\\posizione_45_kes_recon_filtpython\\'
	
	# For each slice-by-slice:
	for i in range(0, dset.shape[2]):
		
		im = dset[:,:,i]

		#imsave('C:\\Temp\\1_original.tif', im.astype(float32))	

		# Padding:
		row_pad = round(im.shape[0] / 4)
		col_pad = round(im.shape[1] / 4)
		im = pad(im, ((row_pad, row_pad), (col_pad, col_pad)), 'edge')

		#imsave('C:\\Temp\\2_padded.tif', im.astype(float32))	

		# Get original size:
		origsize = im.shape

		# Up-scaling:
		im = cv2.resize(im, None, 2, 2, cv2.INTER_CUBIC)

		# Get new shape and center:
		rows, cols = im.shape
		cen_x = im.shape[1] / 2 - 0.5
		cen_y = im.shape[0] / 2 - 0.5

		# Conversion to Polar:
		im = cv2.linearPolar(im, (cen_x, cen_y), amax([rows,cols]), cv2.INTER_CUBIC)

		imsave('C:\\Temp\\3_polar.tif', im.astype(np.float32))

		# Padding for Polar filtering:
		im = pad(im, ((n2, n2), (0, 0)), 'wrap')
		im = pad(im, ((0, 0), (n1, 0)), 'symmetric')

		#imsave('C:\\Temp\\3bis_polar_padded.tif', im.astype(np.float32))

		# Actual filtering:
		im = oimoen(im,n1,n2)

		#imsave('C:\\Temp\\4_polar_filtered.tif', im.astype(np.float32))

		# Crop after Polar filtering:
		im = im[n2:-n2,n1:]

		#imsave('C:\\Temp\\4bis_polar_filtered_crop.tif', im.astype(np.float32))

		# Conversion to Cartesian:
		im = cv2.linearPolar(im, (cen_x, cen_y), amax([rows,cols]), cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP)

		#imsave('C:\\Temp\\5_cartesian.tif', im.astype(np.float32))

		# Down-scaling to original size:
		im = cv2.resize(im, (origsize[0], origsize[1]), interpolation = cv2.INTER_CUBIC)

		# Crop:
		im = im[row_pad:-row_pad,col_pad:-col_pad]


		#imsave('C:\\Temp\\6_output.tif', dset[:,:,i].astype(np.float32))
		imsave(out_path + 'rec_' + str(i).zfill(4) + '.tif', im.astype(float32))	

		dset[:,:,i] = im

	# Return:
	return dset



if __name__ == '__neinmain__':

	from glob import glob

	in_path = 'J:\\Zacchigna\\topo_completo\\posizione_45_kes_recon\\'
	out_path = 'J:\\Zacchigna\\topo_completo\\posizione_45_kes_recon_filtpython\\'


	files = sorted(glob(in_path + '*.tif*'))
	nr_proj = len(files)

	im = imread(files[0]).astype(np.float32) 
	det_row = im.shape[0]
	det_col = im.shape[1]
	Nan = nr_proj

	data = np.zeros((det_row, det_col, nr_proj), np.float32)

	for i in range(nr_proj):
	
		# Read uncorrected tomo:
		rec = imread(files[i]).astype(np.float32) 
	
		# Fill volume:
		data[:,:,i] = rec

	data = post_processing(data, 21, 131)

	# For each slice-by-slice:
	#for i in range(0, data.shape[2]):
	# 	
	#	im = data[:,:,i]
	#
	#	imsave(out_path + 'rec_' + str(i).zfill(4) + '.tif', im.astype(float32))	


if __name__ == '__main__':

	# Create the application:
	app = QApplication(sys.argv)

	# Define application details:
	QCoreApplication.setOrganizationName("INFN")
	QCoreApplication.setApplicationName("KEST Recon")

	# Init main window:
	mainWindow = kstMainWindow()

	# Redirect print() and errors:
	sys.stdout = Redirect(mainWindow.mainPanel.log.outputLog)
	sys.stderr = Redirect(mainWindow.mainPanel.log.errorLog)

	# Run application:
	mainWindow.show()
	t = QTimer()
	t.singleShot(0,mainWindow.onQApplicationStarted)
	sys.exit(app.exec_())
