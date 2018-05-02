import sys
import tifffile 
import h5py
import numpy

import kst_core.kst_io as kst_io
import kst_core.kst_flat_fielding as kst_flat_fielding
import kst_core.kst_remove_outliers as kst_remove_outliers
import kst_core.kst_matrix_manipulation as kst_matrix_manipulation
import kst_core.kst_reconstruction as kst_reconstruction
import kst_core.kst_preprocessing as kst_preprocessing

from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QTimer, QCoreApplication

#from kstImageViewer import kstImageViewer
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


#	low, _ = kst_io.read_pixirad_data('C:\\Temp\\KEST_ESRF\\6652_sou=38.5_E1=27_VtHit=2.0_t=100ms.dat', '1COL')
#	low, _, _, _ = kst_preprocessing.pre_processing('C:\\Temp\\KEST_ESRF\\6652_sou=38.5_E1=27_VtHit=2.0_t=100ms.dat', 
#					0, 65535, 0, 65535, \
#					False, 5, 5, 0.25, \
#					True, False, False, False, '1COL', [149, 173, 0, 0])
	
#	#∟for i in range(0, low.shape[2]):
#	#	imsave('C:\\Temp\\KEST_ESRF\\low\\tomo_' + str(i).zfill(4) + '.tif', low[:,:,i])

#	angles = 180

#	# Convert from degrees to radians:
#	angles = angles * numpy.pi / 180.0
#	rec = kst_reconstruction.recon_astra_fbp(low, angles, 15)

#	for i in range(0, rec.shape[2]):
#		imsave('C:\\Temp\\KEST_ESRF\\rec\\rec_' + str(i).zfill(4) + '.tif', rec[:,:,i])


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
