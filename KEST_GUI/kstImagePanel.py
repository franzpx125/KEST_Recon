import os.path 
import h5py
import numpy

from PyQt5.QtWidgets import QWidget,  QAction, QHBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QTextEdit, QSplitter, QTabWidget
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from kstImageViewer import kstImageViewer
from kstLogPanel import kstLogPanel

class kstImagePanel(QWidget):    	

	def __init__(self):
		""" Class constructor.
		"""
		QWidget.__init__(self)
								
		# Prepare the left tab widget for several image viewers:
		self.tabImageViewers = QTabWidget() 
		self.tabImageViewers.setTabsClosable(True)
		self.tabImageViewers.tabCloseRequested.connect(self.removeTab)

		# Compose layout of the whole widget:
		layout = QHBoxLayout()		
		layout.addWidget(self.tabImageViewers)
		layout.setContentsMargins(0,0,0,0) #left,top,right,bottom
		self.setLayout(layout)


	def addTab(self, data, sourceFile, tabname, type, mode):
		""" Add a new tab with the specified input.
			NOTE: input could be a:
				- 'raw' image (i.e. a 2D raster image ready to be displayed)
				- 'pre-processed' object (i.e. a 4D data structure)
				- 'reconstructed' (i.e. a stack of 2D images)
				- 'post-processed' (i.e. a color RGB image?)
		"""			

		# Get the central image by default:
		im = data[:,:,round(data.shape[2] / 2)]

		# Create the image viewer:
		imageViewer = kstImageViewer(sourceFile, data, type, im, mode)

		# Set value of the refocusing slider (even if it might be hidden):
		imageViewer.sldDataset.setMinimum(0)
		imageViewer.sldDataset.setMaximum(data.shape[2]-1)
		imageViewer.sldDataset.setValue(round(data.shape[2]/2))

		# Add a new tab:
		self.tabImageViewers.addTab(imageViewer, tabname)	

        # To have it active uncomment this line:			
		#self.tabLeftImageViewers.setCurrentIndex(self.tabLeftImageViewers.count() - 1) 	
		

	def removeTab(self, idx):
		""" Called when users want to remove an image viewer.
		"""
		self.tabImageViewers.removeTab(idx)