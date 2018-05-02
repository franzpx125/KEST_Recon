import sys
import os.path 
import h5py
import numpy
import platform
import psutil
import timeit

from tifffile import imread, imsave # debug
from PyQt5.QtWidgets import QMainWindow, QAction, QHBoxLayout, QToolBox, QSizePolicy, QMessageBox
from PyQt5.QtWidgets import QTextEdit, QSplitter, QStatusBar, QProgressBar, QFileDialog, QApplication
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QSize, QPoint

from kstImageViewer import kstImageViewer
from kstMainPanel import kstMainPanel
from kstSidebar import kstSidebar
from kstUtils import eprint

from kst_core.kst_preprocessing import pre_processing
from kst_core.kst_io import read_pixirad_data
from kst_core.kst_reconstruction import recon_astra_fdk, recon_astra_sirt_cone
from kst_core.kst_reconstruction import recon_astra_fbp, recon_astra_sirt_parallel
from kst_core.kst_remove_outliers import estimate_dead_hot

SW_TITLE = "KEST Recon - v. 0.3 alpha"
SW_QUIT_MSG = "This will close the application. Are you sure?"
RAW_TABLABEL = "raw"
PREPROC_TABLABEL = "preprocessed"
RECON_TABLABEL = "reconstructed"


class StatThread(QThread):
	
	statusMessage = pyqtSignal(object)          

	def __init__(self, parent):
		super(StatThread, self).__init__(parent)

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

class ReadThread(QThread):
	
	readDone = pyqtSignal(object, object, object, object, object, object) 
	logOutput = pyqtSignal(object)         
	error = pyqtSignal(object, object)

	def __init__(self, parent, filename, mode='2COL', is_sequence=False):
		""" Class constructor.
		"""
		super(ReadThread, self).__init__(parent)

		self.filename = filename
		self.mode = mode
		self.is_sequence = is_sequence


	def run(self):
		""" Run the thread.
		"""
		try:

			# Log info:
			t1 = timeit.default_timer()
			self.logOutput.emit('Opening: ' + self.filename + '...')

			# Load the file (high might be None):
			low, high = read_pixirad_data(self.filename, self.mode)
	
			# At the end emit a signal with the outputs:
			self.readDone.emit(low, high, self.filename, self.mode, \
                self.is_sequence, RAW_TABLABEL)

			# Log info:
			t2 = timeit.default_timer()
			self.logOutput.emit(self.filename + ' opened succesfully in ' + \
				'{:.3f}'.format(t2 - t1) + ' sec.')

		except Exception as e:

			# Log error:
			self.error.emit('Error while reading ' + self.filename + \
                '. Operation aborted.', str(e))			

		

class PreprocessThread(QThread):
	
	processDone = pyqtSignal(object, object, object, object, object, object, object, \
             object, object, object, object) 
	logOutput = pyqtSignal(object)         
	error = pyqtSignal(object, object)         

	def __init__(self, parent, sourceFile, low_dark_th, low_hot_th, high_dark_th, \
            high_hot_th, rebinning, flatfielding_window, despeckle_window, \
            despeckle_thresh, output_low, output_high, output_diff, output_sum, \
            mode, crop_top, crop_bottom, crop_left, crop_right ):
		""" Class constructor.
		"""
		super(PreprocessThread, self).__init__(parent)

		self.sourceFile = sourceFile		
		self.low_dark_th = low_dark_th
		self.low_hot_th = low_hot_th
		self.high_dark_th = high_dark_th
		self.high_hot_th = high_hot_th
		self.rebinning = rebinning
		self.flatfielding_window = flatfielding_window
		self.despeckle_window = despeckle_window
		self.despeckle_thresh = despeckle_thresh
		self.output_low = output_low
		self.output_high = output_high
		self.output_diff = output_diff
		self.output_sum = output_sum
		self.mode = mode
		self.crop = [ crop_top, crop_bottom, crop_left, crop_right ]

	def run(self):
		""" Run the thread.
		"""
		try:
            # Log info:
			t1 = timeit.default_timer()
			self.logOutput.emit('Performing pre-processing...')
			
			# Do the pre-processing:
			low, high, diff, sum = pre_processing( self.sourceFile, self.low_dark_th, \
				self.low_hot_th, self.high_dark_th, self.high_hot_th, self.rebinning, \
                self.flatfielding_window, self.despeckle_window, self.despeckle_thresh, \
                self.output_low, self.output_high, self.output_diff, self.output_sum, \
                self.mode, self.crop )		

			# At the end emit a signal with the outputs:
			self.processDone.emit( low, high, diff, sum, self.output_low, self.output_high, \
                                    self.output_diff, self.output_sum, self.sourceFile, \
                                    PREPROC_TABLABEL, self.mode )

            # Log info:
			t2 = timeit.default_timer()
			self.logOutput.emit('Pre-processing performed succesfully in ' + \
				'{:.3f}'.format(t2 - t1) + ' sec.')

		except Exception as e:

            # Log error:
			self.error.emit('Error while performing pre-processing. ' + \
                'Operation aborted.', str(e))


class ReconThread(QThread):
	
	reconDone = pyqtSignal(object, object, object, object)      
	logOutput = pyqtSignal(object)         
	error = pyqtSignal(object, object)     

	def __init__(self, parent, im, sourceFile, angles, geometry, ssd, sdd, \
            px, det_u, det_v, short_scan=False, method='FDK / FBP', \
            iterations=1, mode='2COL'):
		""" Class constructor.
		"""
		super(ReconThread, self).__init__(parent)

		self.im = im.astype(numpy.float32)
		self.angles = angles
		self.geometry = geometry
		self.ssd = ssd
		self.sdd = sdd
		self.px = px
		self.det_u = det_u
		self.det_v = det_v
		self.sourceFile = sourceFile
		self.method = method
		self.iterations = iterations
		self.short_scan = short_scan
		self.mode = mode

	def run(self):
		""" Run the thread.
		"""
		try:
			# Log info:
			t1 = timeit.default_timer()
			self.logOutput.emit('Performing reconstruction...')
			
			if (self.geometry == 'parallel-beam'):
                # Do the reconstruction:
				if (self.method == 'SIRT'):
					rec = recon_astra_sirt_parallel(self.im, self.angles, self.det_u, \
                        self.iterations)  
								  
				else: # default FBP       
					rec = recon_astra_fbp(self.im, self.angles, self.det_u)
			
			else:    

				# Do the reconstruction:
				if (self.method == 'SIRT'):
					rec = recon_astra_sirt_cone(self.im, self.angles, self.ssd, self.sdd - self.ssd, \
							self.px, self.det_u, self.det_v, self.iterations)  
								  
				else: # default FDK       
					rec = recon_astra_fdk(self.im, self.angles, self.ssd, self.sdd - self.ssd, \
							self.px, self.det_u, self.det_v, self.short_scan)			

			# At the end emit a signal with the outputs:
			self.reconDone.emit(rec, self.sourceFile, RECON_TABLABEL, self.mode)

			# Log info:
			t2 = timeit.default_timer()
			self.logOutput.emit('Reconstruction performed succesfully in ' + \
				'{:.3f}'.format(t2 - t1) + ' sec.')

		except Exception as e:
			# Log error:
			self.error.emit('Error while performing reconstruction. ' + \
				'Operation aborted.', str(e))



class kstMainWindow(QMainWindow):

	def __init__(self):
		""" Class constructor.
		"""
		QMainWindow.__init__(self)

		dir = os.path.dirname(os.path.realpath(__file__))

		self.__createMenus__()
		newfont = QFont()
		newfont.setPointSize(9) 
		self.setFont(newfont)

		sb = QStatusBar()
		sb.setFixedHeight(24)
		self.setStatusBar(sb)  

		self.statusBarThread = StatThread(self)        
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
		self.sidebar.preprocessingTab.preprocessingRequestedEvent.connect(self.applyPreprocessing)
		self.sidebar.preprocessingTab.calibrateRequestedEvent.connect(self.applyAutoCalibration)
		self.sidebar.reconstructionTab.recostructionRequestedEvent.connect(self.applyReconstruction)


		# Configure the splitter:
		self.splitter.addWidget(self.sidebar)
		self.splitter.addWidget(self.mainPanel)

		# Compose layout of the window:
		self.setCentralWidget(self.splitter) 

		# Set title, icon and default size:
		self.setWindowTitle(SW_TITLE)
		self.setWindowIcon(QIcon(dir + "/resources/logo_kest.png"))
		
		# Default size:
		self.resize(1024,768)		
		self.mainPanel.resize(int(round(self.width() * 0.75)), self.height())
		self.mainPanel.imagePanel.resize(self.width(), int(round(self.height() * 0.85)))		


	def __createMenus__(self):	

		openFile2COLAction = QAction("&Open PIXIRAD 2COL file...", self)
		openFile2COLAction.setShortcut("Ctrl+O")
		openFile2COLAction.setStatusTip("Open a dialog to select a PIXIRAD 2COL file")
		openFile2COLAction.triggered.connect(self.openFile2COL)

		openFile1COLAction = QAction("&Open PIXIRAD 1COL file...", self)
		openFile1COLAction.setShortcut("Ctrl+O")
		openFile1COLAction.setStatusTip("Open a dialog to select a PIXIRAD 1COL file")
		openFile1COLAction.triggered.connect(self.openFile1COL)

		openSequence2COLAction = QAction("&Open PIXIRAD 2COL sequence...", self)
		openSequence2COLAction.setShortcut("Ctrl+O")
		openSequence2COLAction.setStatusTip("Open a dialog to select a PIXIRAD 2COL folder")
		openSequence2COLAction.triggered.connect(self.openFolder2COL)

		openSequence1COLAction = QAction("&Open PIXIRAD 1COL sequence...", self)
		openSequence1COLAction.setShortcut("Ctrl+O")
		openSequence1COLAction.setStatusTip("Open a dialog to select a PIXIRAD 1COL folder")
		openSequence1COLAction.triggered.connect(self.openFolder1COL)

		exitAction = QAction("E&xit", self)
		exitAction.setShortcut("Alt+F4")
		exitAction.setStatusTip("Quit the application")
		exitAction.triggered.connect(self.exitApplication)

		self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
		self.fileMenu.addAction(openFile1COLAction)
		self.fileMenu.addAction(openFile2COLAction)
		self.fileMenu.addSeparator()
		self.fileMenu.addAction(openSequence1COLAction)
		self.fileMenu.addAction(openSequence2COLAction)
		self.fileMenu.addSeparator()		
		self.fileMenu.addAction(exitAction)

		aboutAction = QAction("&About", self)
		aboutAction.setStatusTip("Show application info")
		aboutAction.triggered.connect(self.exitApplication)

		#self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
		#self.helpMenu.addAction(aboutAction)
		#self.helpMenu.addAction(self.aboutQtAct)

	def onQApplicationStarted(self):
		""" Things done as the main window is fully loaded.
		"""
		try:
			# Startup message:
			platf = platform.uname()

			cpus = psutil.cpu_count()
			stat = psutil.virtual_memory()
			ram = (stat.total) / (1024.0 * 1024 * 1024) # GB
	
			# system, node, release, version, machine, and processor.
			val = "KEST started on " + platf.node + " (# of CPUs: " + str(cpus) + \
				", RAM: " + "{:.2f}".format(ram) + " GB)"
		
			# Log string:
			self.mainPanel.log.logOutput(val)

			# Read settings:
			self.read_settings()

		except Exception as e:
			eprint(str(e))
			pass


	def handleStatusMessage(self, message):
		""" Function called by an infinite thread monitoring CPU and GPU stats.
		"""
		self.statusBar().showMessage(self.tr(message))


	def handleOutputLog(self, message):
		""" Function called by job threads to log messages.
		"""		
		self.mainPanel.log.logOutput(self.tr(message))


	def handleThreadError(self, message, error):
		""" Function called by job threads when an exception is raised.
		"""
		self.mainPanel.log.logOutput(self.tr(message))
		self.mainPanel.log.logError(self.tr(error))

        # Restore the buttons:
		self.sidebar.reconstructionTab.button.setEnabled(True) 
		self.sidebar.preprocessingTab.btnApply.setEnabled(True)


	def openFile(self, mode):
		""" Called when user wants to open a new KEST file.
			NOTE: a thread is started when this function is invoked.
		"""

		try:

			options = QFileDialog.Options()
			options |= QFileDialog.DontUseNativeDialog
			filename, _ = QFileDialog.getOpenFileName(self,"Open KEST file", 
						  "","KEST Files (*.dat);;All Files (*)", options=options)
			if filename:

				# Disable buttons:
				self.sidebar.reconstructionTab.button.setEnabled(False)
				self.sidebar.preprocessingTab.btnApply.setEnabled(False)

				# Read the file (on a separate thread):
				self.readThread = ReadThread(self, filename, mode, False)
				self.readThread.readDone.connect(self.readJobDone)
				self.readThread.logOutput.connect(self.handleOutputLog)
				self.readThread.error.connect(self.handleThreadError)
				self.readThread.start()	

				# Open the related HDF5 (if exists):
				#self.sidebar.hdfViewerTab.setHDF5File("C:\\Temp\\test.kest")		

		except Exception as e:
			eprint(str(e))

			# Restore the buttons:
			self.sidebar.reconstructionTab.button.setEnabled(True) 
			self.sidebar.preprocessingTab.btnApply.setEnabled(True) 		

	def openFile1COL(self):
		self.openFile('1COL')

	def openFile2COL(self):
		self.openFile('2COL')

	def openFolder(self, mode):
		""" Called when user wants to open a sequence of KEST files.
			NOTE: a thread is started when this function is invoked.
		"""

		try:

			options = QFileDialog.Options()
			options |= QFileDialog.DontUseNativeDialog
			options |= QFileDialog.ShowDirsOnly
			folder = QFileDialog.getExistingDirectory(self,"Open KEST sequence", 
						  "", options=options)
			if folder:

				# Disable buttons:
				self.sidebar.reconstructionTab.button.setEnabled(False)
				self.sidebar.preprocessingTab.btnApply.setEnabled(False)

				# Read the file (on a separate thread):
				self.readThread = ReadThread(self, folder, mode, True)
				self.readThread.readDone.connect(self.readJobDone)
				self.readThread.logOutput.connect(self.handleOutputLog)
				self.readThread.error.connect(self.handleThreadError)
				self.readThread.start()	

				# Open the related HDF5 (if exists):
				#self.sidebar.hdfViewerTab.setHDF5File("C:\\Temp\\test.kest")		

		except Exception as e:
			eprint(str(e))

			# Restore the buttons:
			self.sidebar.reconstructionTab.button.setEnabled(True) 
			self.sidebar.preprocessingTab.btnApply.setEnabled(True)

	def openFolder1COL(self):
		self.openFolder('1COL')

	def openFolder2COL(self):
		self.openFolder('2COL')

	def applyPreprocessing(self):
		""" Called when user wants to apply the preprocessing on current image.
			NOTE: the current image should be a 'raw' image. The UI should avoid
				  to let this method callable when current image is not a 'raw'.

			NOTE: a thread is started when this function is invoked.
		"""
		try:
			# Disable buttons:
			self.sidebar.reconstructionTab.button.setEnabled(False)
			self.sidebar.preprocessingTab.btnApply.setEnabled(False)

			# Get current left image:
			curr_tab = self.mainPanel.getCurrentTab()
			sourceFile = curr_tab.getSourceFile()
			mode = curr_tab.getOriginalMode()

			# Get params from UI:
			crop_top = self.sidebar.preprocessingTab.getValue("Crop_Top")
			crop_bottom = self.sidebar.preprocessingTab.getValue("Crop_Bottom")
			crop_left = self.sidebar.preprocessingTab.getValue("Crop_Left")
			crop_right = self.sidebar.preprocessingTab.getValue("Crop_Right")

			low_dark_th = self.sidebar.preprocessingTab.getValue("Low_DefectCorrection_DarkPixels")
			low_hot_th = self.sidebar.preprocessingTab.getValue("Low_DefectCorrection_HotPixels")
			high_dark_th = self.sidebar.preprocessingTab.getValue("High_DefectCorrection_DarkPixels")
			high_hot_th = self.sidebar.preprocessingTab.getValue("High_DefectCorrection_HotPixels")
			
			rebinning = self.sidebar.preprocessingTab.getValue("MatrixManipulation_Rebinning2x2")
			
			flatfielding_window = self.sidebar.preprocessingTab.getValue("FlatFielding_Window")

			despeckle_window = self.sidebar.preprocessingTab.getValue("Despeckle_Window")	
			despeckle_thresh = self.sidebar.preprocessingTab.getValue("Despeckle_Threshold")	

			output_low = self.sidebar.preprocessingTab.getValue("Output_LowEnergy")	
			output_high = self.sidebar.preprocessingTab.getValue("Output_HighEnergy")
			output_diff = self.sidebar.preprocessingTab.getValue("Output_LogSubtraction")	
			output_sum = self.sidebar.preprocessingTab.getValue("Output_EnergyIntegration")            
			
			# Call pre-processing (on a separate thread):
			self.preprocessThread = PreprocessThread(self, sourceFile, low_dark_th, low_hot_th, \
				low_dark_th, high_hot_th, rebinning, flatfielding_window, despeckle_window, \
				despeckle_thresh, output_low, output_high, output_diff, output_sum, mode, \
                crop_top, crop_bottom, crop_left, crop_right)
			self.preprocessThread.processDone.connect(self.preprocessJobDone)            
			self.preprocessThread.logOutput.connect(self.handleOutputLog)
			self.preprocessThread.error.connect(self.handleThreadError)
			self.preprocessThread.start()

		except Exception as e:
				
			eprint("Error while pre-processing: " + str(e))   

			# Restore the buttons:
			self.sidebar.reconstructionTab.button.setEnabled(True) 
			self.sidebar.preprocessingTab.btnApply.setEnabled(True) 	



	def applyReconstruction(self):
		""" Called when user wants to perform the reconstruction on current flat-fielded image:
			
			NOTE: the current image should be a 'pre-processed' image. The UI should avoid
				  to let this method callable when current image is not a 'pre-processed'.

			NOTE: a thread is started when this function is invoked.
		"""
		try:
			# Disable buttons:
			self.sidebar.reconstructionTab.button.setEnabled(False)
			self.sidebar.preprocessingTab.btnApply.setEnabled(False)

			# Get current left image:
			curr_tab = self.mainPanel.getCurrentTab()
			im = curr_tab.getData()
			sourceFile = curr_tab.getSourceFile()
			mode = curr_tab.getOriginalMode()


			# Get parameters from UI:
			method = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Method")
			iterations = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Iterations")
			weights = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Weights")
			angles = self.sidebar.reconstructionTab.getValue("Reconstruction_Angles")
			nr_proj = self.sidebar.reconstructionTab.getValue("Reconstruction_Projections")
			upsampling = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Upsampling")
			overpadding = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Overpadding")
			geometry = self.sidebar.reconstructionTab.getValue("Geometry_Type")
			ssd = self.sidebar.reconstructionTab.getValue("Geometry_Source-Sample")
			sdd = self.sidebar.reconstructionTab.getValue("Geometry_Source-Detector")
			px = self.sidebar.reconstructionTab.getValue("Geometry_DetectorPixelSize")
			det_u = self.sidebar.reconstructionTab.getValue("Offsets_Detector-u")
			det_v = self.sidebar.reconstructionTab.getValue("Offsets_Detector-v")
				
			# Remove extra projections:
			im = im[:,:,:nr_proj]

			# Convert from degrees to radians:
			angles = angles * numpy.pi / 180.0

			# Convert to boolean for short_scan:
			short_scan = False if (weights == 0) else True

			# Call reconstruction (on a separate thread):
			self.reconThread = ReconThread(self, im, sourceFile, angles, geometry, \
                ssd, sdd, px, det_u, det_v, short_scan, method, iterations, mode)

			self.reconThread.reconDone.connect(self.reconstructJobDone)                        
			self.reconThread.logOutput.connect(self.handleOutputLog)
			self.reconThread.error.connect(self.handleThreadError)
			self.reconThread.start()	

		except Exception as e:
				
			# Print the exception:
			eprint("Error while performing reconstruction: " + str(e))
			
			# Restore the buttons:
			self.sidebar.reconstructionTab.button.setEnabled(True) 
			self.sidebar.preprocessingTab.btnApply.setEnabled(True)  

		

	def readJobDone(self, low, high, sourceFile, mode, is_sequence, type):
		""" When a job thread has completed this function is called.
		"""
		
		# Open a new tab in the image viewer with the output of reconstruction:
		self.mainPanel.addTab(low, sourceFile, str(os.path.basename(sourceFile)) \
			+ " - " + type, type, mode)
	
		if high is not None:
			self.mainPanel.addTab(high, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type, mode)

		else:
            # Leave only "low" as True but everything deactivated:
			prop = self.sidebar.preprocessingTab.idToProperty["Output_LowEnergy"] 
			prop.setValue(True)
			prop.setEnabled(False)

			prop = self.sidebar.preprocessingTab.idToProperty["Output_HighEnergy"] 
			prop.setValue(False)
			prop.setEnabled(False)

			prop = self.sidebar.preprocessingTab.idToProperty["Output_LogSubtraction"] 
			prop.setValue(False)
			prop.setEnabled(False)

			prop = self.sidebar.preprocessingTab.idToProperty["Output_EnergyIntegration"] 
			prop.setValue(False)
			prop.setEnabled(False)

		# Restore the reconstruction button:
		self.sidebar.reconstructionTab.button.setEnabled(True) 
		self.sidebar.preprocessingTab.btnApply.setEnabled(True) 

	

	def preprocessJobDone( self, low, high, diff, sum, output_low, output_high, \
                           output_diff, output_sum, sourceFile, type, mode ):
		""" This function is called when the preprocessing job thread has completed.
		"""
		
		# Open a new tab in the image viewer with the output of reconstruction:
		if (output_low):
			self.mainPanel.addTab(low, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type, mode)
	
		if (output_high):    
			self.mainPanel.addTab(high, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type, mode)

		if (output_diff):    
			self.mainPanel.addTab(diff, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type, mode)
		
		if (output_sum):    
			self.mainPanel.addTab(sum, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type, mode)

		# Restore the reconstruction button:
		self.sidebar.reconstructionTab.button.setEnabled(True) 
		self.sidebar.preprocessingTab.btnApply.setEnabled(True) 


	def reconstructJobDone(self, im, sourceFile, type, mode):
		""" This function is called when the preprocessing job thread has completed.
		"""
		
		# Open a new tab in the image viewer with the output of reconstruction:
		self.mainPanel.addTab(im, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type, mode )

		# Restore the reconstruction button:
		self.sidebar.reconstructionTab.button.setEnabled(True) 
		self.sidebar.preprocessingTab.btnApply.setEnabled(True)


	def closeEvent(self, event):
		""" Override of the window close() event.
		"""
		quit_msg = SW_QUIT_MSG
		reply = QMessageBox.question(self, SW_TITLE, 
						 quit_msg, QMessageBox.Yes, QMessageBox.No)

		if reply == QMessageBox.Yes:
			self.write_settings()
			event.accept()
		else:
			event.ignore()



	def exitApplication(self):
		""" Close the application
		"""
		self.close()



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

			# Disable buttons:
			self.sidebar.reconstructionTab.button.setEnabled(False)
			self.sidebar.preprocessingTab.btnApply.setEnabled(False)

			# Get current left image:
			curr_left_tab = self.mainPanel.getCurrentLeftTab()
			low = curr_left_tab.getData()
			sourceFile = curr_left_tab.getSourceFile()

			# Get current right image:
			curr_right_tab = self.mainPanel.getCurrentRightTab()
			high = curr_right_tab.getData()

			# Call automatic dark/hot isolation:
			low_dark_th, low_hot_th = estimate_dead_hot(low)
			high_dark_th, high_hot_th = estimate_dead_hot(high)

			# Fill the UI properties with the values:
			self.sidebar.preprocessingTab.setValue("Low_DefectCorrection_DarkPixels", int(low_dark_th))
			self.sidebar.preprocessingTab.setValue("Low_DefectCorrection_HotPixels", int(low_hot_th))
			self.sidebar.preprocessingTab.setValue("High_DefectCorrection_DarkPixels", int(high_dark_th))
			self.sidebar.preprocessingTab.setValue("High_DefectCorrection_HotPixels", int(high_hot_th))

		except Exception as e:
				
			eprint("Error while performing automatic defect correction: " + str(e))   

		finally:

            # Disable buttons:
			self.sidebar.reconstructionTab.button.setEnabled(True)
			self.sidebar.preprocessingTab.btnApply.setEnabled(True)

			# Restore mouse cursor:
			QApplication.restoreOverrideCursor()

	def write_settings(self):
		""" Save UI settings to disk.

		"""
		settings = QSettings()

		settings.beginGroup("MainWindow")
		settings.setValue("size", self.size())
		settings.setValue("pos", self.pos())
		settings.endGroup() 
		
        # Pre-processing group:
		settings.beginGroup("Preprocessing")

		settings.setValue("Crop_Top", \
			self.sidebar.preprocessingTab.getValue("Crop_Top"))
		settings.setValue("Crop_Bottom", \
			self.sidebar.preprocessingTab.getValue("Crop_Bottom"))
		settings.setValue("Crop_Left", \
			self.sidebar.preprocessingTab.getValue("Crop_Left"))
		settings.setValue("Crop_Right", \
			self.sidebar.preprocessingTab.getValue("Crop_Right"))

		settings.setValue("Low_DefectCorrection_DarkPixels", \
			self.sidebar.preprocessingTab.getValue("Low_DefectCorrection_DarkPixels"))
		settings.setValue("Low_DefectCorrection_HotPixels", \
			self.sidebar.preprocessingTab.getValue("Low_DefectCorrection_HotPixels"))
		settings.setValue("High_DefectCorrection_DarkPixels", \
			self.sidebar.preprocessingTab.getValue("High_DefectCorrection_DarkPixels"))
		settings.setValue("High_DefectCorrection_HotPixels", \
			self.sidebar.preprocessingTab.getValue("High_DefectCorrection_HotPixels"))

		settings.setValue("MatrixManipulation_Rebinning2x2", \
			self.sidebar.preprocessingTab.getValue("MatrixManipulation_Rebinning2x2"))  
		
		settings.setValue("FlatFielding_Window", \
			self.sidebar.preprocessingTab.getValue("FlatFielding_Window"))         

		settings.setValue("Despeckle_Threshold", \
			self.sidebar.preprocessingTab.getValue("Despeckle_Threshold"))  
		settings.setValue("Despeckle_Window", \
			self.sidebar.preprocessingTab.getValue("Despeckle_Window"))  

		settings.setValue("Output_LowEnergy", \
			self.sidebar.preprocessingTab.getValue("Output_LowEnergy"))  
		settings.setValue("Output_HighEnergy", \
			self.sidebar.preprocessingTab.getValue("Output_HighEnergy"))
		settings.setValue("Output_LogSubtraction", \
			self.sidebar.preprocessingTab.getValue("Output_LogSubtraction"))  
		settings.setValue("Output_EnergyIntegration", \
			self.sidebar.preprocessingTab.getValue("Output_EnergyIntegration")) 

		settings.endGroup()   


        # Pre-processing group:
		settings.beginGroup("Reconstruction")

		settings.setValue("Geometry_Type", \
			self.sidebar.reconstructionTab.getValue("Geometry_Type"))
		settings.setValue("Geometry_Source-Sample", \
			self.sidebar.reconstructionTab.getValue("Geometry_Source-Sample"))
		settings.setValue("Geometry_Source-Detector", \
			self.sidebar.reconstructionTab.getValue("Geometry_Source-Detector"))
		settings.setValue("Geometry_DetectorPixelSize", \
			self.sidebar.reconstructionTab.getValue("Geometry_DetectorPixelSize"))

		settings.setValue("ReconstructionAlgorithm_Method", \
			self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Method"))
		settings.setValue("ReconstructionAlgorithm_Iterations", \
			self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Iterations"))
		settings.setValue("ReconstructionAlgorithm_Weights", \
			self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Weights"))        
		
		settings.setValue("Reconstruction_Angles", \
			self.sidebar.reconstructionTab.getValue("Reconstruction_Angles"))     
		settings.setValue("Reconstruction_Projections", \
			self.sidebar.reconstructionTab.getValue("Reconstruction_Projections"))     

		settings.setValue("Offsets_Detector-u", \
			self.sidebar.reconstructionTab.getValue("Offsets_Detector-u"))
		settings.setValue("Offsets_Detector-v", \
			self.sidebar.reconstructionTab.getValue("Offsets_Detector-v"))	

		settings.setValue("ReconstructionAlgorithm_Upsampling", \
			self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Upsampling"))     
		settings.setValue("ReconstructionAlgorithm_Overpadding", \
			self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Overpadding"))     

		settings.endGroup()   


	def read_settings(self):
		""" Restore UI settings from previous session.

		"""
		settings = QSettings()

		settings.beginGroup("MainWindow")
		self.resize(settings.value("size", QSize(1024, 768)))
		self.move(settings.value("pos", QPoint(200, 200)))
		settings.endGroup()


		# Fill the UI properties with the values:
		settings.beginGroup("Preprocessing")

		self.sidebar.preprocessingTab.setValue("Crop_Top", \
			int(settings.value("Crop_Top", 0)))
		self.sidebar.preprocessingTab.setValue("Crop_Bottom", \
			int(settings.value("Crop_Bottom", 0)))
		self.sidebar.preprocessingTab.setValue("Crop_Left", \
			int(settings.value("Crop_Left", 0)))
		self.sidebar.preprocessingTab.setValue("Crop_Right", \
			int(settings.value("Crop_Right", 0)))

		self.sidebar.preprocessingTab.setValue("Low_DefectCorrection_DarkPixels", \
			int(settings.value("Low_DefectCorrection_DarkPixels", 0)))
		self.sidebar.preprocessingTab.setValue("Low_DefectCorrection_HotPixels", \
			int(settings.value("Low_DefectCorrection_HotPixels", 65535)))
		self.sidebar.preprocessingTab.setValue("High_DefectCorrection_DarkPixels", \
			int(settings.value("High_DefectCorrection_DarkPixels", 0)))
		self.sidebar.preprocessingTab.setValue("High_DefectCorrection_HotPixels", \
			int(settings.value("High_DefectCorrection_HotPixels", 65535)))

        # Bug in PyQT (or at least unexpected behaviour):
		if ( (str(settings.value("MatrixManipulation_Rebinning2x2")) == 'False') or  
			 (str(settings.value("MatrixManipulation_Rebinning2x2")) == 'false') ):
			self.sidebar.preprocessingTab.setValue("MatrixManipulation_Rebinning2x2", False)
		else:
			self.sidebar.preprocessingTab.setValue("MatrixManipulation_Rebinning2x2", True)

		self.sidebar.preprocessingTab.setValue("FlatFielding_Window", \
			int(settings.value("FlatFielding_Window", 5))) 

		self.sidebar.preprocessingTab.setValue("Despeckle_Threshold", \
			float(settings.value("Despeckle_Threshold", 0.25))) 
		self.sidebar.preprocessingTab.setValue("Despeckle_Window", \
			int(settings.value("Despeckle_Window", 5))) 
		
        # Bug in PyQT (or at least unexpected behaviour):
		if ( (str(settings.value("Output_LowEnergy")) == 'False') or  
			 (str(settings.value("Output_LowEnergy")) == 'false') ):
			self.sidebar.preprocessingTab.setValue("Output_LowEnergy", False)
		else:
			self.sidebar.preprocessingTab.setValue("Output_LowEnergy", True)

        # Bug in PyQT (or at least unexpected behaviour):
		if ( (str(settings.value("Output_HighEnergy")) == 'False') or  
			 (str(settings.value("Output_HighEnergy")) == 'false') ):
			self.sidebar.preprocessingTab.setValue("Output_HighEnergy", False)
		else:
			self.sidebar.preprocessingTab.setValue("Output_HighEnergy", True)

        # Bug in PyQT (or at least unexpected behaviour):
		if ( (str(settings.value("Output_LogSubtraction")) == 'False') or  
			 (str(settings.value("Output_LogSubtraction")) == 'false') ):
			self.sidebar.preprocessingTab.setValue("Output_LogSubtraction", False)
		else:
			self.sidebar.preprocessingTab.setValue("Output_LogSubtraction", True)

        # Bug in PyQT (or at least unexpected behaviour):
		if ( (str(settings.value("Output_EnergyIntegration")) == 'False') or  
			 (str(settings.value("Output_EnergyIntegration")) == 'false') ):
			self.sidebar.preprocessingTab.setValue("Output_EnergyIntegration", False)
		else:
			self.sidebar.preprocessingTab.setValue("Output_EnergyIntegration", True)

		settings.endGroup()  


        # Fill the UI properties with the values:
		settings.beginGroup("Reconstruction")

		self.sidebar.reconstructionTab.setValue("Geometry_Type", \
			self.sidebar.reconstructionTab.geometry_type.index( \
            settings.value("Geometry_Type", 0)))
		self.sidebar.reconstructionTab.setValue("Geometry_Source-Sample", \
			float(settings.value("Geometry_Source-Sample", 170.0)))
		self.sidebar.reconstructionTab.setValue("Geometry_Source-Detector", \
			float(settings.value("Geometry_Source-Detector", 240.0)))
		self.sidebar.reconstructionTab.setValue("Geometry_DetectorPixelSize", \
			float(settings.value("Geometry_DetectorPixelSize", 0.062)))

		self.sidebar.reconstructionTab.setValue("ReconstructionAlgorithm_Method", \
			self.sidebar.reconstructionTab.reconstruction_methods.index( \
			settings.value("ReconstructionAlgorithm_Method", 0)))
		self.sidebar.reconstructionTab.setValue("ReconstructionAlgorithm_Iterations", \
			int(settings.value("ReconstructionAlgorithm_Iterations", 200)))
		self.sidebar.reconstructionTab.setValue("ReconstructionAlgorithm_Weights", \
			self.sidebar.reconstructionTab.weighting_methods.index( \
			settings.value("ReconstructionAlgorithm_Weights", 0)))

		self.sidebar.reconstructionTab.setValue("Reconstruction_Angles", \
			float(settings.value("Reconstruction_Angles", 360.0)))
		self.sidebar.reconstructionTab.setValue("Reconstruction_Projections", \
			int(settings.value("Reconstruction_Projections", 720)))

		self.sidebar.reconstructionTab.setValue("Offsets_Detector-u", \
			float(settings.value("Offsets_Detector-u", 0.0)))		
		self.sidebar.reconstructionTab.setValue("Offsets_Detector-v", \
			float(settings.value("Offsets_Detector-v", 0.0)))
		

         # Bug in PyQT (or at least unexpected behaviour):
		if ( (str(settings.value("ReconstructionAlgorithm_Upsampling")) == 'False') or  
			 (str(settings.value("ReconstructionAlgorithm_Upsampling")) == 'false') ):
			self.sidebar.reconstructionTab.setValue("ReconstructionAlgorithm_Upsampling", False)
		else:
			self.sidebar.reconstructionTab.setValue("ReconstructionAlgorithm_Upsampling", True)

        # Bug in PyQT (or at least unexpected behaviour):
		if ( (str(settings.value("ReconstructionAlgorithm_Overpadding")) == 'False') or  
			 (str(settings.value("ReconstructionAlgorithm_Overpadding")) == 'false') ):
			self.sidebar.reconstructionTab.setValue("ReconstructionAlgorithm_Overpadding", False)
		else:
			self.sidebar.reconstructionTab.setValue("ReconstructionAlgorithm_Overpadding", True)

		settings.endGroup()  





	