import os.path 
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBar, QSizePolicy, QLabel, QApplication
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QGroupBox, QSplitter, QTreeWidgetItemIterator
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

PREPROC_ALIGNMENT_LABEL = "Alignment"
PREPROC_FLATFIELDING_LABEL = "Flat fielding"

class VoxPreprocessingPanel(QWidget):

	def __init__(self):

		QWidget.__init__(self)

		self.HDF5File = None
						
		# Add a group box for the alignment:
		self.alignmentGroup = QGroupBox()
		self.alignmentGroupLayout = QVBoxLayout()

        # Add a group box for the flat fielding:
		self.flatfieldingGroup = QGroupBox()
		self.flatfieldingGroupLayout = QVBoxLayout()	
		
		# Add a separator to keep the layout dock to top:
		spacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)   
		spacer.setSizePolicy(spacerSizePolicy)
		

	
		# Configure the alignment groupbox:
		self.alignmentGroup.setTitle(PREPROC_ALIGNMENT_LABEL)
		self.alignmentGroup.setMinimumHeight = 280
		self.alignmentGroup.setLayout(self.alignmentGroupLayout)


        # Configure the flat fielding groupbox:
		self.flatfieldingGroup.setTitle(PREPROC_FLATFIELDING_LABEL)
		self.flatfieldingGroup.setMinimumHeight = 280
		self.flatfieldingGroup.setLayout(self.flatfieldingGroupLayout)


		# Compose layout of the whole widget:
		layout = QVBoxLayout()
		layout.addWidget(self.alignmentGroup)  
		layout.addWidget(self.flatfieldingGroup)   
		layout.addWidget(spacer)      
		layout.setContentsMargins(0,0,0,0)	
		self.setLayout(layout)


	