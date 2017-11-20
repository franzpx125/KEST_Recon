import sys
import tifffile 
import h5py
import numpy

from PyQt5.QtWidgets import QApplication

#from VoxImageViewer import VoxImageViewer
#from VoxImagePanel import VoxImagePanel
#from VoxHDFViewer import VoxHDFViewer
#from VoxSidebar import VoxSidebar
#from VoxMainPanel import VoxMainPanel
from VoxMainWindow import VoxMainWindow


if __name__ == '__main__':
	


	# Create the application:
	app = QApplication(sys.argv)

	# Create image viewer and load an image file to display:
	#viewer = VoxImageViewer()
	#viewer.setImage(tifffile.imread("C:\\Temp\\lena32f.tif"))


	#viewer = VoxHDFViewer()
	#viewer.setHDF5File("C:\\Temp\\91777.nxs")


	#viewer = VoxSidebar()
	#viewer.hdfViewerTab.setHDF5File("C:\\Temp\\91777.nxs")

	viewer = VoxMainWindow()
	#viewer.sidebar.hdfViewerTab.setHDF5File("C:\\Temp\\91777.nxs")
	#viewer.mainPanel.imageViewer.setImage(tifffile.imread("C:\\Temp\\lena32f.tif"))
	f = h5py.File("C:\\Users\\Franz\\Documents\\MyProjects\\voxel\\voxel_data_files\\card.vox", 'r')
	dataset = f['C']
	im = numpy.empty((2048,2048), dtype=dataset.dtype)
	dataset.read_direct(im, numpy.s_[:,:])
	viewer.mainPanel.imageViewer.setImage(im)

	# Show viewer and run application:
	viewer.show()
	sys.exit(app.exec_())
