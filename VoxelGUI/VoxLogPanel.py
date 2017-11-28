import os.path 
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QTextEdit, QTabWidget, QFrame
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt


class VoxLogPanel(QWidget):

	def __init__(self):

		QWidget.__init__(self)

		# Prepare a tab widget
		self.tabWidget = QTabWidget() 
		self.tabWidget.setTabPosition(QTabWidget.South)
		#self.tabWidget.setTabShape(QTabWidget.Triangular) 

							
		# Add the widgets to the panel:
		self.outputLog = QTextEdit()
		self.outputLog.setFrameStyle(QFrame.NoFrame)
		self.outputLog.setReadOnly(True)
		self.outputLogLayout = QVBoxLayout()	
		self.outputLogLayout.setContentsMargins(0,0,0,0)
		self.outputLog.setLayout(self.outputLogLayout)

		# Add the widgets to the panel:
		self.errorLog = QTextEdit()
		self.errorLog.setFrameStyle(QFrame.NoFrame)
		self.errorLog.setReadOnly(True)
		self.errorLogLayout = QVBoxLayout()	
		self.errorLogLayout.setContentsMargins(0,0,0,0)
		self.errorLog.setLayout(self.errorLogLayout)
				
		self.tabWidget.addTab(self.outputLog, "Output")
		self.tabWidget.addTab(self.errorLog, "Error list")    

		# Compose layout of the whole widget:
		layout = QVBoxLayout()	
		self.setContentsMargins(0,1,0,0)	
		layout.setContentsMargins(0,1,0,0)
		layout.addWidget(self.tabWidget)		
		self.setLayout(layout)

		# Startup message:
		self.outputLog.append("VOXELRecon is intended for research use only. It is not a medical device.")




	