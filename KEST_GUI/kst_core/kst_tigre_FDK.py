from __future__ import print_function
from __future__ import division

import numpy as np
import warnings
import scipy.io
import os
import sys
import math
import numpy as np
import copy

from pyfftw import n_byte_align, simd_alignment
from pyfftw.interfaces.numpy_fft import rfft, irfft

#from _tigre_FDK import tigre_FDK

from tifffile import imread, imsave

class Geometry:

	def __init__(self, shp, ssd, sdd, px, offset_u, offset_v, geom, filter):
		
		# VARIABLE DESCRIPTION UNITS
		# -------------------------------------------------------------------------------------
		self.DSD = ssd + sdd                                # Distance Source Detector (mm)
		self.DSO = ssd                                      # Distance Source Origin (mm)
		# Detector parameters
		self.nDetector = np.array((shp[1], shp[0]))         # number of pixels (px)
		self.dDetector = np.array((px, px))                 # size of each pixel (mm)
		self.sDetector = self.nDetector * self.dDetector    # total size of the detector (mm)
		# Image parameters
		self.nVoxel = np.array((shp[1], shp[1], shp[0]))    # number of voxels (vx)
		self.sVoxel = self.nVoxel * px                      # total size of the image (mm)
		self.dVoxel = self.sVoxel / self.nVoxel             # size of each voxel (mm)
		# Offsets
		self.offOrigin = np.array((0, 0, 0))                # Offset of image from origin (mm)
		self.offDetector = np.array((offset_u * px, offset_v * px))  # Offset of Detector (mm)
		# Auxiliary
		self.accuracy = 0.5                                 # Accuracy of FWD proj (vx/sample)
		# Mode
		self.mode = geom
		self.filter = None


def parkerweight(proj,geo,angles,q):
	start = -geo.sDetector[0] / 2 + geo.dDetector[0] / 2
	stop = geo.sDetector[0] / 2 - geo.dDetector[0] / 2
	step = geo.dDetector[0]
	alpha = np.arctan(np.arange(start, stop + step, step) / geo.DSD)
	alpha = -alpha
	delta = abs(alpha[0] - alpha[-1]) / 2
	totangles = np.cumsum(np.diff(angles))
	totangles = totangles[-1]

	if totangles < 2 * np.pi:
		warnings.warn('Computing Parker weigths for scanning angle equal or bigger than 2*pi '
			  'Consider disabling Parker weigths.')
	if totangles < np.pi + 2 * delta:
		warnings.warn('Scanning angles smaller than pi+cone_angle. This is limited angle tomgraphy, \n'
					  'there is nosufficient data, thus weigthing for data redundancy is not required.')
	epsilon = max(totangles - (np.pi + 2 * delta),0)
	data = proj
	# for i in range(proj.shape[0]):
	for i in range(33):
		beta = angles[i]
		w = 0.5 * (s_function(beta / b_subf(alpha,delta,epsilon,q) - 0.5) + s_function((beta - 2 * delta + 2 * alpha - epsilon) / b_subf(alpha,delta,epsilon,q) + 0.5) - s_function((beta - np.pi + 2 * alpha) / b_subf(-alpha,delta,epsilon,q) - 0.5) - s_function((beta - np.pi - 2 * delta - epsilon) / b_subf(-alpha,delta,epsilon,q) + 0.5))
		proj[i]*=w

	return proj

def s_function(abeta):
	w = np.zeros(abeta.shape)
	w[abeta <= -0.5] = 0
	w[abs(abeta) < 0.5] = 0.5 * (1 + np.sin(np.pi * abeta[abs(abeta) < 0.5]))
	w[abeta >= 0.5] = 1
	return w

# b_function = B
def b_function(alpha,delta,epsilon):
	return 2 * delta - 2 * alpha + epsilon

# b_subf = b
def b_subf(alpha,delta,epsilon,q):
	return q * b_function(alpha,delta,epsilon)


def filtering(proj,geo,angles,parker):

	if parker:
		proj = parkerweight(proj.transpose(0,2,1),geo,angles,parker).transpose(0,2,1)
		# proj=parkerweight(proj,geo,angles,parker)

	filt_len = max(64,2 ** nextpow2(2 * geo.nDetector[0]))
	ramp_kernel = ramp_flat(filt_len)

	d = 1
	filt = filter(geo.filter,ramp_kernel[0],filt_len,d)

	filt = np.kron(np.ones((geo.nDetector[1],1)),filt).transpose()    

	for i in range(len(angles)):

        # Zero-padding:
		fproj = np.zeros((filt_len,geo.nDetector[1]),dtype=np.float32)
		fproj[int(filt_len / 2 - geo.nDetector[0] / 2):int(filt_len / 2 + geo.nDetector[0] / 2),:] = proj[:,:,i]   

		# Fourier-transform:
		n_byte_align(fproj, simd_alignment) 
		fproj = rfft(fproj, axis=0, threads=2)

		# Filter:
		fproj = fproj * filt[0:fproj.shape[0],:]

        # Inverse-Fourier:
		n_byte_align(fproj, simd_alignment) 
		fproj = np.real(irfft(fproj, axis=0, threads=2))
		end = len(fproj)

		# Crop:
		fproj = fproj[int(end / 2 - geo.nDetector[0] / 2):int(end / 2 + geo.nDetector[0] / 2),:] / 2 / geo.dDetector[0] * \
				 (2 * np.pi / len(angles)) / 2 * (geo.DSD / geo.DSO)
		proj[:,:,i] = fproj.astype(np.float32)

	return proj

def ramp_flat(n):
	nn = np.arange(-n / 2,n / 2)
	h = np.zeros(nn.shape,dtype=np.float32)
	h[int(n / 2)] = 1 / 4
	odd = nn % 2 == 1
	h[odd] = -1 / (np.pi * nn[odd]) ** 2
	return h, nn


def filter(filter,kernel,order,d):
	f_kernel = abs(np.fft.fft(kernel)) * 2

	filt = f_kernel[:int((order / 2) + 1)]
	w = 2 * np.pi * np.arange(len(filt)) / order
	if filter not in ['ram-lak','shepp-logan','cosine','hamming','hann',None]:
		raise ValueError('filter not recognised: ' + filter)

	if filter in {'ram-lak', None}:
		if filter is None:
			warnings.warn('no filter selected, using default ram-lak')
		pass
	if filter == 'shepp-logan':
		filt[1:]*=(np.sin(w[1:] / (2 * d)) / (w[1:] / (2 * d)))
	if filter == 'cosine':
		filt[1:]*=np.cos(w[1:] / (2 * d))
	if filter == 'hamming':
		filt[1:]*=(.54 + .46 * np.cos(w[1:] / d))
	if filter == 'hann':
		filt[1:]*=(1 + np.cos(w[1:]) / d) / 2

	filt[w > np.pi * d] = 0
	filt = np.hstack((filt,filt[1:-1][::-1]))
	return filt


def nextpow2(n):
	i = 1
	while (2 ** i) < n:
		i+=1
	return i


def FDK(proj_in, ssd, sdd, px, offset_u=0.0, offset_v=0.0, roll_deg=0.0, pitch_deg=0.0, \
		yaw_deg=0.0, filter='ram-lak', tot_angles=2*math.pi, angles_shift=0, geom='cone'):
	"""

	"""
	proj = copy.deepcopy(proj_in)
	nr_proj = proj.shape[2]
	ang_range = np.linspace(0 + angles_shift, tot_angles + angles_shift, nr_proj, False).astype(np.float32)   

	# Create TIGRE geometry object:
	geo = Geometry(proj.shape, ssd, sdd, px, offset_u, offset_v, geom, filter)

	if filter is not None:
		geo.filter = filter

	# Apply weights (offsets are constants...  out of the loop):
	xv = np.arange((-geo.nDetector[0] / 2) + 0.5, 1 + (geo.nDetector[0] / 2) - 0.5) * geo.dDetector[0] + geo.offDetector[0]
	yv = np.arange((-geo.nDetector[1] / 2) + 0.5, 1 + (geo.nDetector[1] / 2) - 0.5) * geo.dDetector[1] + geo.offDetector[1]
	(xx, yy) = np.meshgrid(xv, yv)
	w = geo.DSD / np.sqrt((geo.DSD ** 2 + xx ** 2 + yy ** 2))

	for ii in range(len(ang_range)):		
		proj_in[:,:,ii] = proj_in[:,:,ii] * w

	# Filtering:    
	proj = proj.transpose(1,0,2)
	proj = filtering(proj, geo, ang_range, parker=False)
	proj = proj.transpose(1,0,2)	
	
    # Backproject (one week of debug... please remember...):
	shp = np.array([proj.shape[0],proj.shape[1],proj.shape[2]]) # For further reshape    		
	proj = np.asfortranarray(proj.transpose(2,0,1), dtype=np.float32).flatten()	# Note the flattening
	rec = tigre_FDK(proj, shp, 1, 0, ssd, sdd, px, offset_u, offset_v, roll_deg, pitch_deg, yaw_deg, ang_range) 	
	rec = np.reshape(rec, geo.nVoxel, order='F') # 1-D output


	return rec

