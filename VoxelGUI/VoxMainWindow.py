import sys
import os.path 
import h5py

from PyQt5.QtWidgets import QMainWindow, QAction, QHBoxLayout, QToolBox, QSizePolicy, QMessageBox
from PyQt5.QtWidgets import QTextEdit, QSplitter, QStatusBar, QProgressBar, QFileDialog
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from VoxMainPanel import VoxMainPanel
from VoxSidebar import VoxSidebar

SW_TITLE = "VOXELRecon - v. 0.1 alpha"

class VoxMainWindow(QMainWindow):

	def __init__(self):

		QMainWindow.__init__(self)

		dir = os.path.dirname(os.path.realpath(__file__))

		self.createMenus()
		self.createStatusBar()
		newfont = QFont()
		newfont.setPointSize(9) 
		self.setFont(newfont)

		# create progress bar
		self.pb = QProgressBar(self.statusBar())
		self.statusBar().addPermanentWidget(self.pb)
		
							
		# Add the widgets to the panel:
		self.sidebar = VoxSidebar()
		self.mainPanel = VoxMainPanel()		
		self.splitter = QSplitter(Qt.Horizontal)

		# Configure the image viewer:


		# Configure the splitter:
		self.splitter.addWidget(self.sidebar)
		self.splitter.addWidget(self.mainPanel)

		# Compose layout of the window:
		self.setCentralWidget(self.splitter) 

		# Set title, icon and default size:
		self.setWindowTitle(SW_TITLE)
		self.setWindowIcon(QIcon(dir + "/resources/logo_voxel.png"))
		
		# Default size:
		self.resize(1024,768)		
		self.mainPanel.resize(int(round(self.width() * 0.75)), self.height())
		self.mainPanel.imageViewer.resize(self.width(), int(round(self.height() * 0.85)))


	def createMenus(self):		

		openAction = QAction("&Open file...", self)
		openAction.setShortcut("Ctrl+O")
		openAction.setStatusTip("Open a dialog to select a VOXEL file")
		openAction.triggered.connect(self.openFile)

		exitAction = QAction("E&xit", self)
		exitAction.setShortcut("Alt+F4")
		exitAction.setStatusTip("Quit the application")
		exitAction.triggered.connect(self.exitApplication)

		self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
		self.fileMenu.addAction(openAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(exitAction)

		aboutAction = QAction("&About", self)
		aboutAction.setStatusTip("Show application info")
		aboutAction.triggered.connect(self.exitApplication)

		self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
		self.helpMenu.addAction(aboutAction)
		#self.helpMenu.addAction(self.aboutQtAct)


	def createStatusBar(self):

		sb = QStatusBar()
		sb.setFixedHeight(24)
		self.setStatusBar(sb)
		self.statusBar().showMessage(self.tr("Ready"))

	def openFile(self):

		options = QFileDialog.Options()
		options |= QFileDialog.DontUseNativeDialog
		filename, _ = QFileDialog.getOpenFileName(self,"Open VOXEL file", 
                      "","VOXEL Files (*.vox);;All Files (*)", options=options)
		if filename:
			self.sidebar.hdfViewerTab.setHDF5File(filename)

	def closeEvent(self, event):
		""" Override of the window close() event.
		"""
		quit_msg = "This will close the application. Are you sure?"
		reply = QMessageBox.question(self, SW_TITLE, 
						 quit_msg, QMessageBox.Yes, QMessageBox.No)

		if reply == QMessageBox.Yes:
			event.accept()
		else:
			event.ignore()

	def exitApplication(self):

		self.close()





	