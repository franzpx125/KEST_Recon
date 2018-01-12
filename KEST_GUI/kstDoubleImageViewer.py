import os.path 
import h5py
import numpy

from PyQt5.QtWidgets import QWidget,  QAction, QHBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QTextEdit, QSplitter, QTabWidget
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from kstImageViewer import kstImageViewer
from kstLogPanel import kstLogPanel

class kstDoubleImageViewer(QWidget):    	

	def __init__(self):
		""" Class constructor.
		"""
		QWidget.__init__(self)
								
		# Prepare the left tab widget for several image viewers:
		self.tabLeftImageViewers = QTabWidget() 
		self.tabLeftImageViewers.setTabsClosable(True)
		self.tabLeftImageViewers.tabCloseRequested.connect(self.removeLeftTab)

		# Prepare the right tab widget for several image viewers:
		self.tabRightImageViewers = QTabWidget() 
		self.tabRightImageViewers.setTabsClosable(True)
		self.tabRightImageViewers.tabCloseRequested.connect(self.removeRightTab)
		
		# Prepare the splitter:
		self.splitter = QSplitter(Qt.Horizontal) 
		self.splitter.addWidget(self.tabLeftImageViewers)
		self.splitter.addWidget(self.tabRightImageViewers)

		# Compose layout of the whole widget:
		layout = QHBoxLayout()		
		layout.addWidget(self.splitter)
		layout.setContentsMargins(0,0,0,0) #left,top,right,bottom
		self.setLayout(layout)


	def addTab(self, data, sourceFile, tabname, type, position='left'):
		""" Add a new tab with the specified input.
			NOTE: input could be a:
				- 'raw' image (i.e. a 2D raster image ready to be displayed)
				- 'pre-processed' object (i.e. a 4D data structure)
				- 'reconstructed' (i.e. a stack of 2D images)
				- 'post-processed' (i.e. a color RGB image?)
		"""			

		# Decide what to show according to the type:
		#if (type == 'raw'):
		#	im = data
		#elif (type == 'pre-processed'):
		#	# Prepare something to show:
		#	im = data.get_photograph()
		#elif (type == 'reconstructed'):
		#	# Get the central one by default:
		#	im = data[round(data.shape[0] / 2),:,:]
		#elif (type == 'post-processed'):
		#	im = data

		# Get the central one by default:
		im = data[:,:,round(data.shape[2] / 2)]

		# Create the image viewer:
		imageViewer = kstImageViewer(sourceFile, data, type, im)

		# Set value of the refocusing slider (even if it might be hidden):
		imageViewer.sldDataset.setMinimum(0)
		imageViewer.sldDataset.setMaximum(data.shape[2]-1)
		imageViewer.sldDataset.setValue(round(data.shape[2]/2))

		# Add a new tab and have it active:
		if (position == 'left'):

			self.tabLeftImageViewers.addTab(imageViewer, tabname)				
			self.tabLeftImageViewers.setCurrentIndex(self.tabLeftImageViewers.count() - 1) 
		
		else:

			self.tabRightImageViewers.addTab(imageViewer, tabname)				
			self.tabRightImageViewers.setCurrentIndex(self.tabRightImageViewers.count() - 1) 
		

	def removeLeftTab(self, idx):
		""" Called when users want to remove an image viewer.
		"""
		self.tabLeftImageViewers.removeTab(idx)


	def removeRightTab(self, idx):
		""" Called when users want to remove an image viewer.
		"""
		self.tabRightImageViewers.removeTab(idx)