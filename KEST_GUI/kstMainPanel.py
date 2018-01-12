import os.path 
import h5py
import numpy

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBox, QSizePolicy 
from PyQt5.QtWidgets import QTextEdit, QSplitter, QTabWidget
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from kstDoubleImageViewer import kstDoubleImageViewer
from kstLogPanel import kstLogPanel

class kstMainPanel(QWidget):    	

	def __init__(self):
		""" Class constructor.
		"""
		QWidget.__init__(self)								
	
		# Prepare the double image viewer:
		self.doubleImageViewer = kstDoubleImageViewer()

		# Prepare the log panel:
		self.log = kstLogPanel()		
		self.splitter = QSplitter(Qt.Vertical) 

		# Configure the splitter:
		self.splitter.addWidget(self.doubleImageViewer)
		self.splitter.addWidget(self.log)

		# Compose layout of the whole widget:
		layout = QVBoxLayout()		
		layout.addWidget(self.splitter)
		layout.setContentsMargins(2,10,10,10) #left,top,right,bottom
		self.setLayout(layout)


	def addLeftTab(self, data, sourceFile, tabname, type):
		
		self.doubleImageViewer.addTab(data, sourceFile, tabname, type, position='left')

	def addRightTab(self, data, sourceFile, tabname, type):
		
		self.doubleImageViewer.addTab(data, sourceFile, tabname, type, position='right')
			

	def getCurrentLeftTab(self):

		return self.doubleImageViewer.tabLeftImageViewers.currentWidget()

	def getCurrentRightTab(self):

		return self.doubleImageViewer.tabRightImageViewers.currentWidget()


	def removeLeftTab(self, idx):

		self.doubleImageViewer.removeTabe(idx, position='left')

	def removeRightTab(self, idx):

		self.doubleImageViewer.removeTabe(idx, position='right')

