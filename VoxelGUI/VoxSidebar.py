import os.path 
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from VoxHDFViewer import VoxHDFViewer
from VoxPreprocessingPanel import VoxPreprocessingPanel
from VoxRefocusingPanel import VoxRefocusingPanel

VOX_SIDEBAR_HDFVIEW = "Dataset Info"
VOX_SIDEBAR_PREPROC = "Pre-processing"
VOX_SIDEBAR_REFOCUS = "Refocusing"

class VoxSidebar(QWidget):

	def __init__(self):

		QWidget.__init__(self)
							
		# Add a toolbox to the sidebar:
		self.toolbox = QToolBox()

		# Each tab of the toolbox contains a widget:
		self.hdfViewerTab = VoxHDFViewer()

		# Configure the alignment tab:
		self.preprocessingTab = VoxPreprocessingPanel()

		# Configure the refocusing tab:
		self.refocusingTab = VoxRefocusingPanel()

		# Configure the whole widget:
		self.toolbox.addItem(self.hdfViewerTab, VOX_SIDEBAR_HDFVIEW)
		self.toolbox.addItem(self.preprocessingTab, VOX_SIDEBAR_PREPROC)
		self.toolbox.addItem(self.refocusingTab, VOX_SIDEBAR_REFOCUS)

        # Define layout:
		layout = QVBoxLayout()
		layout.addWidget(self.toolbox)	
		layout.setContentsMargins(10,10,2,10) #left,top,right,bottom
		self.setLayout(layout)



	