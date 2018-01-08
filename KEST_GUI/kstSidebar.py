import os.path 
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from kstHDFViewer import kstHDFViewer
from kstPreprocessingPanel import kstPreprocessingPanel
from kstReconstructionPanel import kstReconstructionPanel

KST_SIDEBAR_HDFVIEW = "Dataset Info"
KST_SIDEBAR_PREPROC = "Pre-processing"
KST_SIDEBAR_RECON = "Reconstruction"

class kstSidebar(QWidget):

	def __init__(self):

		QWidget.__init__(self)
							
		# Add a toolbox to the sidebar:
		self.toolbox = QToolBox()

		# Each tab of the toolbox contains a widget:
		self.hdfViewerTab = kstHDFViewer()

		# Configure the alignment tab:
		self.preprocessingTab = kstPreprocessingPanel()

		# Configure the refocusing tab:
		self.refocusingTab = kstReconstructionPanel()

		# Configure the whole widget:
		self.toolbox.addItem(self.hdfViewerTab, KST_SIDEBAR_HDFVIEW)
		self.toolbox.addItem(self.preprocessingTab, KST_SIDEBAR_PREPROC)
		self.toolbox.addItem(self.refocusingTab, KST_SIDEBAR_RECON)

		# Define layout:
		layout = QVBoxLayout()
		layout.addWidget(self.toolbox)	
		layout.setContentsMargins(10,10,2,10) #left,top,right,bottom
		self.setLayout(layout)



	