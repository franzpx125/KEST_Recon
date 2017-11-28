# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2017 The VOXEL Collaboration.
##
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of VOXEL nor the names of its contributors may 
##     be used to endorse or promote products derived from this software 
##     without specific prior written permission.
##
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
##
#############################################################################

import sys
import tifffile 
import h5py
import numpy

from PyQt5.QtWidgets import QWidget, QApplication

#from VoxImageViewer import VoxImageViewer
#from VoxImagePanel import VoxImagePanel
#from VoxHDFViewer import VoxHDFViewer
#from VoxSidebar import VoxSidebar
#from VoxMainPanel import VoxMainPanel
from VoxMainWindow import VoxMainWindow


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
		# Add text to a QTextEdit...
		self.wg.append(text)



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


    # Init main window:
	mainWindow = VoxMainWindow()

	# Redirect print() and errors:
	sys.stdout = Redirect(mainWindow.mainPanel.log.outputLog)
	sys.stderr = Redirect(mainWindow.mainPanel.log.errorLog)

	#viewer.sidebar.hdfViewerTab.setHDF5File("C:\\Temp\\91777.nxs")
	#viewer.mainPanel.imageViewer.setImage(tifffile.imread("C:\\Temp\\lena32f.tif"))
	f = h5py.File("C:\\Users\\Franz\\Documents\\MyProjects\\voxel\\voxel_data_files\\rule2.vox", 'r')
	dataset = f['C']
	im = numpy.empty((2048,2048), dtype=dataset.dtype)
	dataset.read_direct(im, numpy.s_[:,:])
	mainWindow.mainPanel.imageViewer.setImage(im)


	# Show viewer and run application:
	mainWindow.show()
	sys.exit(app.exec_())
