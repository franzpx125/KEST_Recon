import os.path 
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QTextEdit, QSplitter, QTabWidget
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from VoxImageViewer import VoxImageViewer
from VoxLogPanel import VoxLogPanel

class VoxMainPanel(QWidget):    	

	def __init__(self):

		QWidget.__init__(self)
								
		# Prepare a tab widget for several image viewers:
		self.tabImageViewers = QTabWidget() 
		self.tabImageViewers.setTabsClosable(True)
		self.tabImageViewers.tabCloseRequested.connect(self.removeTab)
		
		# "Fake" image viewer to basically let user understand what to expect:
		self.imageViewer = VoxImageViewer()

		# Prepare the log panel:
		self.log = VoxLogPanel()		
		self.splitter = QSplitter(Qt.Vertical)

		# TO DO DYNAMICALLY: Configure the image viewer:
		self.tabImageViewers.addTab(self.imageViewer, "Raw Image")		   

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


	def removeTab(self, idx):
		""" Called when users want to remove an image viewer.
		"""

        # Remove current tab:
		self.tabImageViewers.removeTab(idx)