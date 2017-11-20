import os.path 
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt


class VoxLogPanel(QWidget):

	def __init__(self):

		QWidget.__init__(self)
							
		# Add the widgets to the panel:
		self.log = QTextEdit()
		self.log.setReadOnly(True)
		self.logLayout = QVBoxLayout()	
		self.log.setLayout(self.logLayout)

		# Compose layout of the whole widget:
		layout = QVBoxLayout()		
		layout.setContentsMargins(0,1,0,0)
		layout.addWidget(self.log)		
		self.setLayout(layout)

		# Startup message:
		self.log.append("VOXELRecon is intended for research use only. It is not a medical device.")




	