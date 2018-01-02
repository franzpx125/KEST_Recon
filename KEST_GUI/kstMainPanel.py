import os.path 
import h5py
import numpy

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QTextEdit, QSplitter, QTabWidget
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from kstImageViewer import kstImageViewer
from kstLogPanel import kstLogPanel

class kstMainPanel(QWidget):    	

	def __init__(self):
		""" Class constructor.
		"""
		QWidget.__init__(self)
								
		# Prepare a tab widget for several image viewers:
		self.tabImageViewers = QTabWidget() 
		self.tabImageViewers.setTabsClosable(True)
		self.tabImageViewers.tabCloseRequested.connect(self.removeTab)
		
		# "Fake" image viewer to basically let user understand what to expect:
		data = numpy.zeros((1024,1024))
		self.imageViewer = kstImageViewer("", data, 'raw', data)

		# Prepare the log panel:
		self.log = kstLogPanel()		
		self.splitter = QSplitter(Qt.Vertical) 

		# Configure the splitter:
		self.splitter.addWidget(self.tabImageViewers)
		self.splitter.addWidget(self.log)

		# Compose layout of the whole widget:
		layout = QVBoxLayout()		
		layout.addWidget(self.splitter)
		layout.setContentsMargins(2,10,10,10) #left,top,right,bottom
		self.setLayout(layout)

		# Default ratio between image viewer and log panel:
		self.imageViewer.resize( self.width(), int(round(self.height() * 0.85)))



	def addTab(self, data, sourceFile, tabname, type):
		""" Add a new tab with the specified input.
            NOTE: input could be a:
                - 'raw' image (i.e. a 2D raster image ready to be displayed)
                - 'lightfield' object (i.e. a 4D data structure)
                - 'refocused' (i.e. a stack of 2D images)
                - 'depth_map' (i.e. a color RGB image?)
		"""			

		# Decide what to show according to the type:
		if (type == 'raw'):
			im = data
		elif (type == 'lightfield'):
			# Prepare something to show:
			im = data.get_photograph()
		elif (type == 'refocused'):
			# Get the central one by default:		
			im = data[round(data.shape[0]/2),:,:]
		elif (type == 'depth_map'):
			im = data

		# Create the image viewer:
		imageViewer = kstImageViewer(sourceFile, data, type, im)

		# Set value of the refocusing slider (even if it might be hidden):
		if (type == 'refocused'):
			val = round(imageViewer.sldRefocusing.maximum() / 2)
			imageViewer.sldRefocusing.setValue(val)

		# Add a new tab:
		self.tabImageViewers.addTab(imageViewer, tabname)	

		# To have it active:
		self.tabImageViewers.setCurrentIndex(self.tabImageViewers.count() - 1) 
		

	def removeTab(self, idx):
		""" Called when users want to remove an image viewer.
		"""

        # Remove current tab:
		self.tabImageViewers.removeTab(idx)