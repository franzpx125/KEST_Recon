import os.path 
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QTextEdit, QSplitter
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from VoxImageViewer import VoxImageViewer
from VoxLogPanel import VoxLogPanel

class VoxMainPanel(QWidget):

	def __init__(self):

		QWidget.__init__(self)
							
		# Add the widgets to the panel:
		self.imageViewer = VoxImageViewer()
		self.log = VoxLogPanel()		
		self.splitter = QSplitter(Qt.Vertical)

		# Configure the image viewer:


		# Configure the splitter:
		self.splitter.addWidget(self.imageViewer)
		self.splitter.addWidget(self.log)

		# Compose layout of the whole widget:
		layout = QVBoxLayout()		
		layout.addWidget(self.splitter)
		layout.setContentsMargins(2,10,10,10) #left,top,right,bottom
		self.setLayout(layout)

		# Default ratio between image viewer and log panel:
		#print( self.width())
		#print( self.height())
		self.imageViewer.resize( self.width(), int(round(self.height() * 0.85)))



	