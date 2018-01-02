import sys
import os.path 
import h5py
import numpy
import psutil

from PyQt5.QtWidgets import QMainWindow, QAction, QHBoxLayout, QToolBox, QSizePolicy, QMessageBox
from PyQt5.QtWidgets import QTextEdit, QSplitter, QStatusBar, QProgressBar, QFileDialog, QApplication
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from kstImageViewer import kstImageViewer
from kstMainPanel import kstMainPanel
from kstSidebar import kstSidebar
from kstUtils import eprint

SW_TITLE = "KEST - v. 0.1 alpha"
SW_QUIT_MSG = "This will close the application. Are you sure?"
RAW_TABLABEL = "raw"
PREPROC_TABLABEL = "preprocessed"
RECON_TABLABEL = "reconstruction"

class WorkThread(QThread):
	
	statusMessage = pyqtSignal(object)          

	def __init__(self, parent):
		super(WorkThread, self).__init__(parent)

	def run(self):
		try:
			while(True):

				# Get CPU and RAM infos:
				text = "CPU: " + "{:.0f}".format(psutil.cpu_percent()) + "%"
				stat = psutil.virtual_memory()
				tot = stat.total / (1024.0 * 1024 * 1024) # GB
				ava = stat.available / (1024.0 * 1024 * 1024) # GB
				text = text + " - RAM: " + "{:.2f}".format(tot - ava) + \
					" GB (" + "{:.0f}".format(stat.percent) + "%)"
				
				# Get GPU infos:
				try:
					import GPUtil                    
					GPUs = GPUtil.getGPUs()
					tot = GPUs[0].memoryTotal
					ava = GPUs[0].memoryUsed                    
					text = text + " | GPU: " + "{:.0f}".format(GPUs[0].load * 100) + "%" \
						+ " - MEM: " + "{:.2f}".format(GPUs[0].memoryUsed / 1024.0) + \
						" GB (" + "{:.0f}".format(GPUs[0].memoryUtil * 100) + "%)"

				except Exception as e:
					pass
				
				finally:
					self.statusMessage.emit(text)
					self.sleep(1)
		except:
			pass

class kstMainWindow(QMainWindow):

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

		self.statusBarThread = WorkThread(self)        
		self.statusBarThread.statusMessage.connect(self.handleStatusMessage)
		self.statusBarThread.start()        

		# Create progress bar:
		#self.pb = QProgressBar(self.statusBar())
		#self.statusBar().addPermanentWidget(self.pb)
		
							
		# Add the widgets to the panel:
		self.sidebar = kstSidebar()
		self.mainPanel = kstMainPanel()		
		self.splitter = QSplitter(Qt.Horizontal)

		# Configure the sidebar:
		self.sidebar.hdfViewerTab.openImageDataEvent.connect(self.openImage)
		#self.sidebar.preprocessingTab.preprocessingRequestedEvent.connect(self.applyPreprocessing)
		#self.sidebar.preprocessingTab.calibrateRequestedEvent.connect(self.applyAutoCalibration)
		self.sidebar.refocusingTab.recostructionRequestedEvent.connect(self.applyRefocusing)


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

	def handleStatusMessage(self, message):
	    self.statusBar().showMessage(self.tr(message))


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
		self.mainPanel.addTab(im, filename,  \
			str(os.path.basename(filename)) + " - " + RAW_TABLABEL \
			+ " " + str(os.path.basename(key)), 'raw')


	def applyAutoCalibration(self):
		""" Called when user wants to apply the auto-calibration on current image.
			NOTE: the current image should be a 'raw' image. The UI should avoid
				  to let this method callable when current image is not a 'raw'.
		"""
		try:
			# Set mouse wait cursor:
			QApplication.setOverrideCursor(Qt.WaitCursor)

			# Get current image:
			curr_tab = self.mainPanel.tabImageViewers.currentWidget()
			sourceFile = curr_tab.getSourceFile()
						
			# Call vox core library to create the 4D light field data structure:
			#
			
			# Fake calibration: #####################################
			with h5py.File(sourceFile, 'r') as f:
				# Convert from HDF5 datasets to numpy arrays:
				key = '/instrument/camera/micro_lenses_array/array_offsets'
				array_offsets = numpy.empty((f[key].shape[0], f[key].shape[1]), dtype=f[key].dtype)
				f[key].read_direct(array_offsets, numpy.s_[:, :])

				# Convert from HDF5 datasets to numpy arrays:
				key = '/instrument/camera/micro_lenses_array/lenslet_effective_size'
				lenslet_effective_size = numpy.empty((f[key].shape[0], f[key].shape[1]), dtype=f[key].dtype)
				f[key].read_direct(lenslet_effective_size, numpy.s_[:, :])


			# Fill the UI properties with the values:
			self.sidebar.preprocessingTab.setValue("InputLenslet_Width", float(lenslet_effective_size[1][0]))
			self.sidebar.preprocessingTab.setValue("InputLenslet_Height", float(lenslet_effective_size[0][0]))
			self.sidebar.preprocessingTab.setValue("InputLenslet_OffsetLeft", float(array_offsets[1][0]))
			self.sidebar.preprocessingTab.setValue("InputLenslet_OffsetTop", float(array_offsets[0][0]))

			self.sidebar.preprocessingTab.setValue("OutputLenslet_Width", int(round(lenslet_effective_size[1][0])))
			self.sidebar.preprocessingTab.setValue("OutputLenslet_Height", int(round(lenslet_effective_size[0][0])))

		except Exception as e:
				
			eprint("Error while performing auto-calibration: " + str(e))   

		finally:
			# Restore mouse cursor:
			QApplication.restoreOverrideCursor()



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

			# Get params from UI:
			lenslet_width = self.sidebar.preprocessingTab.getValue("InputLenslet_Width")
			lenslet_height = self.sidebar.preprocessingTab.getValue("InputLenslet_Height")
			lenslet_offsetTop = self.sidebar.preprocessingTab.getValue("InputLenslet_OffsetTop")
			lenslet_offsetLeft = self.sidebar.preprocessingTab.getValue("InputLenslet_OffsetLeft")

			acq_params = { 'lenslet_effective_size': numpy.array([lenslet_width, lenslet_height]),
					   'array_offsets': numpy.array([lenslet_offsetTop, lenslet_offsetLeft]) }  

			# Call vox core library to create the 4D light field data structure:
			camera = vox.lightfield.get_camera('imagineoptic_haso3')
			lf = vox.dist_tools_io.import_lightfield_from_2D_image(in_im, camera=camera, \
				acq_params=acq_params, data_type=numpy.float32)	

			# Open a new tab in the image viewer with the output of preprocessing:
			self.mainPanel.addTab(lf, sourceFile, str(os.path.basename(sourceFile)) + " - " + \
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
			alpha_start = self.sidebar.refocusingTab.getValue("RefocusingDistance_Minimum")
			alpha_end = self.sidebar.refocusingTab.getValue("RefocusingDistance_Maximum")
			alpha_step = self.sidebar.refocusingTab.getValue("RefocusingDistance_Step")
			alphas = numpy.arange(alpha_start, alpha_end, alpha_step)
						
			# Get method parameters from UI:
			method = self.sidebar.refocusingTab.getValue("RefocusingAlgorithm_Method")
			iterations = self.sidebar.refocusingTab.getValue("RefocusingAlgorithm_Iterations")
			beamGeometry = self.sidebar.refocusingTab.getValue("RefocusingAlgorithm_BeamGeometry")

			# Get padding paramters from UI:
			padding = self.sidebar.refocusingTab.getValue("RefocusingAlgorithm_PaddingMethod")
			padding_width = self.sidebar.refocusingTab.getValue("RefocusingAlgorithm_PaddingWidth")
			upsampling = self.sidebar.refocusingTab.getValue("RefocusingAlgorithm_Upsampling")

			# Prepare for refocus:
			z0 = lf.camera.get_focused_distance()
			z0s = lf.camera.get_refocusing_distances(alphas)
			refocusing_distances = lf.camera.get_refocusing_distances(alphas)


			# Call vox core library to refocus the 4D light field data structure:
			if method == 'integration':
				imgs = vox.refocus.compute_refocus_integration(lf, alphas, \
					up_sampling=upsampling, border=padding_width, \
                    border_padding=padding, beam_geometry=beamGeometry)
			
			elif method == 'Fourier':
				imgs = vox.refocus.compute_refocus_fourier(lf, alphas, \
					 up_sampling=upsampling, border=padding_width, \
                     border_padding=padding, beam_geometry=beamGeometry)

			elif method == 'backprojection':
				imgs = vox.tomo.compute_refocus_backprojection(lf, z0s, \
                    up_sampling=upsampling, border=padding_width, \
                    border_padding=padding, beam_geometry=beamGeometry)
                    #, super_sampling=supersampling )

			elif method == 'iterative':
				imgs = vox.tomo.compute_refocus_iterative(lf, z0s, \
                    up_sampling=upsampling, border=padding_width, \
                    border_padding=padding, num_iters = iterations, \
                    beam_geometry=beamGeometry)
                    #, super_sampling=supersampling )

			# Open a new tab in the image viewer with the output of refocusing:
			self.mainPanel.addTab(imgs, sourceFile, str(os.path.basename(sourceFile)) + " - " + \
				RECON_TABLABEL, 'refocused')

		except Exception as e:
				
			eprint("Error while refocusing: " + str(e))   

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





	