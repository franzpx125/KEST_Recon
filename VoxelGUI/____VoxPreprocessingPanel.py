import os.path
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBar, QSizePolicy, QLabel, QApplication
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QGroupBox, QSplitter, QTreeWidgetItemIterator
from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox, QGridLayout
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
		self.alignmentGroupLayout = QGridLayout()

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

        # Configure the lenslet input size spinboxes:
		self.lensletEffectiveWidth = QDoubleSpinBox() 
		self.lensletEffectiveHeight = QDoubleSpinBox()
		self.lensletEffectiveOffsetTop = QDoubleSpinBox() 
		self.lensletEffectiveOffsetLeft = QDoubleSpinBox()
		
		#self.lensletEffectiveSize_X. 
		self.alignmentGroupLayout.addWidget(QLabel("Width:"), 1, 0)
		self.alignmentGroupLayout.addWidget(self.lensletEffectiveWidth, 1, 1)
		self.alignmentGroupLayout.addWidget(QLabel("Height:"), 2, 0)
		self.alignmentGroupLayout.addWidget(self.lensletEffectiveHeight, 2, 1)

		self.alignmentGroupLayout.addWidget(QLabel("Top:"), 1, 2)
		self.alignmentGroupLayout.addWidget(self.lensletEffectiveOffsetTop, 1, 3)
		self.alignmentGroupLayout.addWidget(QLabel("Left:"), 2, 2)
		self.alignmentGroupLayout.addWidget(self.lensletEffectiveOffsetLeft, 2, 3)

		#self.alignmentGroupLayout.addWidget(self.lensletEffectiveSize_X)
		#self.alignmentGroupLayout.addWidget(self.lensletEffectiveSize_Y)




        # Configure the flat fielding groupbox:
		self.flatfieldingGroup.setTitle(PREPROC_FLATFIELDING_LABEL)
		self.flatfieldingGroup.setMinimumHeight = 280
		self.flatfieldingGroup.setLayout(self.flatfieldingGroupLayout)


		# Compose layout of the whole widget:
		layout = QVBoxLayout()
		layout.addWidget(self.alignmentGroup)  
		#layout.addWidget(self.flatfieldingGroup)   
		layout.addWidget(spacer)      
		layout.setContentsMargins(0,0,0,0)	
		self.setLayout(layout)


	