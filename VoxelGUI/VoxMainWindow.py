import sys
import os.path 
import h5py
import numpy
import vox

from PyQt5.QtWidgets import QMainWindow, QAction, QHBoxLayout, QToolBox, QSizePolicy, QMessageBox
from PyQt5.QtWidgets import QTextEdit, QSplitter, QStatusBar, QProgressBar, QFileDialog, QApplication
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt

from VoxImageViewer import VoxImageViewer
from VoxMainPanel import VoxMainPanel
from VoxSidebar import VoxSidebar
from VoxUtils import eprint

SW_TITLE = "VOXELRecon - v. 0.1 alpha"
SW_QUIT_MSG = "This will close the application. Are you sure?"
RAW_TABLABEL = "raw"
PREPROC_TABLABEL = "preprocessed"
REFOCUS_TABLABEL = 'refocused'

class VoxMainWindow(QMainWindow):

	def __init__(self):
		""" Class constructor.
		"""
		QMainWindow.__init__(self)

		dir = os.path.dirname(os.path.realpath(__file__))

		self.__createMenus()
		self.__createStatusBar()
		newfont = QFont()
		newfont.setPointSize(9) 
		self.setFont(newfont)

		# Create progress bar:
		#self.pb = QProgressBar(self.statusBar())
		#self.statusBar().addPermanentWidget(self.pb)
		
							
		# Add the widgets to the panel:
		self.sidebar = VoxSidebar()
		self.mainPanel = VoxMainPanel()		
		self.splitter = QSplitter(Qt.Horizontal)

		# Configure the sidebar:
		self.sidebar.hdfViewerTab.openImageDataEvent.connect(self.openImage)
		self.sidebar.preprocessingTab.preprocessingRequestedEvent.connect(self.applyPreprocessing)
		self.sidebar.refocusingTab.refocusingRequestedEvent.connect(self.applyRefocusing)


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


	def __createMenus(self):		

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

		#self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
		#self.helpMenu.addAction(aboutAction)
		#self.helpMenu.addAction(self.aboutQtAct)


	def __createStatusBar(self):

		sb = QStatusBar()
		sb.setFixedHeight(24)
		self.setStatusBar(sb)
		self.statusBar().showMessage(self.tr("Ready"))


	def openFile(self):
		""" Called when user wants to open a new vox file.
		"""

		try:
			options = QFileDialog.Options()
			options |= QFileDialog.DontUseNativeDialog
			filename, _ = QFileDialog.getOpenFileName(self,"Open VOXEL file", 
						  "","VOXEL Files (*.vox);;All Files (*)", options=options)
			if filename:
				# Open in sidebar:
				self.sidebar.hdfViewerTab.setHDF5File(filename)

				# By default open a tab with the main image:
				self.openImage(filename, '/data/image')

		except Exception as e:
			eprint(str(e))



	def openImage(self, filename, key):
		""" Called when user wants to open a new tab with an image, e.g. via
			context menu of the HDF5 viewer.
		"""

		# Load the specified 'key' image from the HDF5 specified file:
		f = h5py.File(filename, 'r')
		dataset = f[key]
		im = numpy.empty(dataset.shape, dtype=dataset.dtype)
		dataset.read_direct(im, numpy.s_[:,:])
		im = im.T

		# Open a new tab in the image viewer:
		self.mainPanel.addTab(im, str(os.path.basename(filename)),  \
			str(os.path.basename(filename)) + " - " + RAW_TABLABEL \
			+ " " + str(os.path.basename(key)), 'raw')



	def applyPreprocessing(self):
		""" Called when user wants to apply the preprocessing on current image.
			NOTE: the current image should be a 'raw' image. The UI should avoid
				  to let this method callable when current image is not a 'raw'.
		"""
		try:
			# Set mouse wait cursor:
			QApplication.setOverrideCursor(Qt.WaitCursor)

			# Get current image:
			curr_tab = self.mainPanel.tabImageViewers.currentWidget()
			in_im = curr_tab.getData()
			sourceFile = curr_tab.getSourceFile()

			# Get params from UI: ##############################################
			acq_params = { 'lenslet_effective_size': numpy.array([15.565, 15.565]),
					   'array_offsets': numpy.array([10.5, 2.75]) }  

			# Call vox core library to create the 4D light field data structure:
			camera = vox.lightfield.get_camera('imagineoptic_haso3')
			lf = vox.dist_tools_io.import_lightfield_from_2D_image(in_im, camera=camera, \
				acq_params=acq_params, data_type=numpy.float32)		

			# Open a new tab in the image viewer with the output of preprocessing:
			self.mainPanel.addTab(lf, sourceFile, sourceFile + " - " + \
				PREPROC_TABLABEL, 'lightfield')

		except Exception as e:
				
			eprint("Error while pre-processing: " + str(e))   

		finally:
			# Restore mouse cursor:
			QApplication.restoreOverrideCursor()



	def applyRefocusing(self):
		""" Called when user wants to apply the refocusing on current lightfield image:
            NOTE: the current image should be a 'lightfield' image. The UI should avoid
                  to let this method callable when current image is not a 'lightfield'.
		"""
		try:
			# Set mouse wait cursor:
			QApplication.setOverrideCursor(Qt.WaitCursor)

			# Get current image:
			curr_tab = self.mainPanel.tabImageViewers.currentWidget()
			lf = curr_tab.getData()
			sourceFile = curr_tab.getSourceFile()

			# Get alphas from UI:
			alpha_start = self.sidebar.refocusingTab.getRefocusingDistance_Minimum()
			alpha_end = self.sidebar.refocusingTab.getRefocusingDistance_Maximum()
			alpha_step = self.sidebar.refocusingTab.getRefocusingDistance_Step()
			alphas = numpy.arange(alpha_start, alpha_end, alpha_step)

			# Prepare for refocus:
			z0 = lf.camera.get_focused_distance()
			z0s = lf.camera.get_refocusing_distances(alphas)
			refocusing_distances = lf.camera.get_refocusing_distances(alphas)

			# Get method from UI:
			method = self.sidebar.refocusingTab.getRefocusingAlgorithm_Method()

			# Call vox core library to refocus the 4D light field data structure:
			if method == 0: # 'integration':
				imgs = vox.refocus.compute_refocus_integration(lf, alphas)
			elif method == 1: # 'Fourier':
				imgs = vox.refocus.compute_refocus_fourier(lf, alphas)
			elif method == 2: # 'backprojection':
				imgs = vox.tomo.compute_refocus_backprojection(lf, z0s)
			elif method == 3: # 'iterative':
				#imgs = vox.tomo.compute_refocus_iterative(lf, z0s[numpy.r_[(0, 4)]])
				imgs = vox.tomo.compute_refocus_iterative(lf, z0s)

			# Open a new tab in the image viewer with the output of refocusing:
			self.mainPanel.addTab(imgs, sourceFile, sourceFile + " - " + \
				REFOCUS_TABLABEL, 'refocused')

		except Exception as e:
				
			eprint("Error while pre-processing: " + str(e))   

		finally:
			# Restore mouse cursor:
			QApplication.restoreOverrideCursor()

	def closeEvent(self, event):
		""" Override of the window close() event.
		"""
		quit_msg = SW_QUIT_MSG
		reply = QMessageBox.question(self, SW_TITLE, 
						 quit_msg, QMessageBox.Yes, QMessageBox.No)

		if reply == QMessageBox.Yes:
			event.accept()
		else:
			event.ignore()



	def exitApplication(self):
		""" Close the application
		"""
		self.close()





	