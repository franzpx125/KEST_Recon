import sys
import tifffile 
import h5py
import numpy

import kst_core.kst_io as kst_io
import kst_core.kst_flat_fielding as kst_flat_fielding
import kst_core.kst_remove_outliers as kst_remove_outliers
import kst_core.kst_matrix_manipulation as kst_matrix_manipulation
import kst_core.kst_reconstruction as kst_reconstruction

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QTimer

#from VoxImageViewer import VoxImageViewer
#from VoxImagePanel import VoxImagePanel
#from VoxHDFViewer import VoxHDFViewer
#from VoxSidebar import VoxSidebar
#from VoxMainPanel import VoxMainPanel
from kstMainWindow import kstMainWindow


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



#if __name__ == '__main__':

#	low, high = kst_io.read_pixirad_data('C:\Temp\A.dat')
#	flat_low, flat_high = kst_io.read_pixirad_data('C:\Temp\A_flat.dat')

#	#Flow  = kst_io.read_tiff_sequence('J:\\TestDatasets_CWI\\D_conebeam\\projections_0.25\\tomo*.tif')
#	#flat_low = kst_io.read_tiff_sequence('J:\\TestDatasets_CWI\\D_conebeam\\projections_0.25\\airraw*.tif')

#	msk_low = numpy.zeros(low.shape, dtype=bool)
#	msk_flat_low = numpy.zeros(flat_low.shape, dtype=bool)

#	for i in range(0, low.shape[2]):
#		low[:,:,i], msk_low[:,:,i] = kst_remove_outliers.pixel_correction(low[:,:,i].astype(numpy.float32))
#		#flat_low[:,:,i], msk_flat_low[:,:,i] = kst_remove_outliers.pixel_correction(flat_low[:,:,i].astype(numpy.float32))


#	low = kst_flat_fielding.conventional_flat_fielding(low, flat_low)
#	low = -numpy.log(low)	

##	low_up = numpy.zeros( (low.shape[0]*2, low.shape[1]*2, low.shape[2]), low.dtype)
#	for i in range(0, low.shape[2]):

#		imsave('C:\Temp\\buttami\\filt_' + str(i).zfill(4) + '.tif', low[:,:,i].astype(numpy.float32))
#		imsave('C:\Temp\\buttami\\msk_' + str(i).zfill(4) + '.tif', msk_low[:,:,i].astype(numpy.float32))
##		low_up[:,:,i] = kst_matrix_manipulation.upscaling2x2(low[:,:,i], method='linear')
##		#imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\up_' + str(i).zfill(4) + '.tif', low_up[:,:,i].astype(numpy.float32))

##	#low = low[:,:,:363]
##	#rec = kst_reconstruction.recon_astra_fdk(low, 2*numpy.pi, 500.0, 50.0, 0.062, -50, 0, scaling_factor=0.5)
#	rec = kst_reconstruction.recon_astra_fdk(low.astype(numpy.float32), 2*numpy.pi, 80.0, 100.0, 0.025*4.0, -15/4.0, 0.0)


	#for i in range(0, rec.shape[2]):

	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\rec_' + str(i).zfill(4) + '.tif', rec[:,:,i].astype(numpy.float32))

	
	#msk_low = numpy.zeros(low.shape, dtype=bool)
	#msk_high = numpy.zeros(high.shape, dtype=bool)

	#msk_flat_low = numpy.zeros(flat_low.shape, dtype=bool)
	#msk_flat_high = numpy.zeros(flat_high.shape, dtype=bool)

	## Same shape assumed:
	#for i in range(0, 5):

	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\orig_' + str(i).zfill(4) + '.tif', low[:,:,i].astype(numpy.float32))

	#	low[:,:,i], msk_low[:,:,i] = kst_remove_outliers._pixel_correction(low[:,:,i].astype(numpy.float32))
	#	high[:,:,i], msk_high[:,:,i] = kst_remove_outliers._pixel_correction(high[:,:,i].astype(numpy.float32))

	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\tomo_' + str(i).zfill(4) + '.tif', low[:,:,i].astype(numpy.float32))
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\high\\tomo_' + str(i).zfill(4) + '.tif', high[:,:,i].astype(numpy.float32))
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\tomo_msk_' + str(i).zfill(4) + '.tif', msk_low[:,:,i].astype(numpy.float32))
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\high\\tomo_msk_' + str(i).zfill(4) + '.tif', msk_high[:,:,i].astype(numpy.float32))

	## Same shape assumed:
	#for i in range(0, 5):

	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\flat_orig_' + str(i).zfill(4) + '.tif', flat_low[:,:,i].astype(numpy.float32))
		
	#	flat_low[:,:,i], msk_flat_low[:,:,i] = kst_remove_outliers._pixel_correction(flat_low[:,:,i].astype(numpy.float32))
	#	flat_high[:,:,i], msk_flat_high[:,:,i] = kst_remove_outliers._pixel_correction(flat_high[:,:,i].astype(numpy.float32))

	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\flat' + str(i).zfill(4) + '.tif', flat_low[:,:,i].astype(numpy.float32))
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\high\\flat_' + str(i).zfill(4) + '.tif', flat_high[:,:,i].astype(numpy.float32))        
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\flat_msk_' + str(i).zfill(4) + '.tif', msk_flat_low[:,:,i].astype(numpy.float32))
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\high\\flat_msk_' + str(i).zfill(4) + '.tif', msk_flat_high[:,:,i].astype(numpy.float32))
		
    # Prepare plans:
	#EFF_low, filtEFF_low = kst_dynamic_flatfielding.dff_prepare_plan(flat_low, 16)
	#EFF_high, filtEFF_high = kst_dynamic_flatfielding.dff_prepare_plan(flat_high, 16)
	#EFF_sum, filtEFF_sum = kst_dynamic_flatfielding.dff_prepare_plan(flat_sum, 16)
	#EFF_diff, filtEFF_diff = kst_dynamic_flatfielding.dff_prepare_plan(flat_diff, 16)

	# Same shape assumed:
	#for i in range(0, low.shape[2]):
	#	low[:,:,i] = kst_dynamic_flatfielding.dynamic_flat_fielding(low[:,:,i], EFF_low, filtEFF_low, 2)
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\low\\tomo_' + str(i).zfill(4) + '.tif', low[:,:,i].astype(numpy.float32))
		
	#	high[:,:,i] = kst_dynamic_flatfielding.dynamic_flat_fielding(high[:,:,i], EFF_high, filtEFF_high, 2)
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\high\\tomo_' + str(i).zfill(4) + '.tif', high[:,:,i].astype(numpy.float32))

	#	sum[:,:,i] = kst_dynamic_flatfielding.dynamic_flat_fielding(sum[:,:,i], EFF_sum, filtEFF_sum, 2)
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\sum\\tomo_' + str(i).zfill(4) + '.tif', sum[:,:,i].astype(numpy.float32))

	#	diff[:,:,i] = kst_dynamic_flatfielding.dynamic_flat_fielding(diff[:,:,i], EFF_diff, filtEFF_diff, 2)
	#	imsave('J:\\KEST\\MisureNovembrePisa\\DATA\\TestDFF\\diff\\tomo_' + str(i).zfill(4) + '.tif', diff[:,:,i].astype(numpy.float32))


if __name__ == '__main__':

	# Create the application:
	app = QApplication(sys.argv)

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
