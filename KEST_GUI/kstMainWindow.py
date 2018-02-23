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
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from kstImageViewer import kstImageViewer
from kstMainPanel import kstMainPanel
from kstSidebar import kstSidebar
from kstUtils import eprint

from kst_core.kst_preprocessing import pre_processing
from kst_core.kst_io import read_pixirad_data
from kst_core.kst_reconstruction import recon_astra_fdk, recon_astra_sirt
from kst_core.kst_remove_outliers import estimate_dead_hot

SW_TITLE = "KEST Recon - v. 0.1 alpha"
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
	
	readDone = pyqtSignal(object, object, object, object) 
	logOutput = pyqtSignal(object)         
	error = pyqtSignal(object, object)

	def __init__(self, parent, filename):
		""" Class constructor.
		"""
		super(ReadThread, self).__init__(parent)

		self.filename = filename


	def run(self):
		""" Run the thread.
		"""
		try:

			# Log info:
			t1 = timeit.default_timer()
			self.logOutput.emit('Opening: ' + self.filename + '...')

			# Load the file:
			low, high = read_pixirad_data(self.filename)		

			# At the end emit a signal with the outputs:
			self.readDone.emit(low, high, self.filename, RAW_TABLABEL)

			# Log info:
			t2 = timeit.default_timer()
			self.logOutput.emit(self.filename + ' opened succesfully in ' + \
				'{:.3f}'.format(t2 - t1) + ' sec.')

		except Exception as e:

			# Log error:
			self.error.emit('Error while reading ' + self.filename + \
                '. Operation aborted.', str(e))			

		

class PreprocessThread(QThread):
	
	processDone = pyqtSignal(object, object, object, object, object, object, object, object, object, object) 
	logOutput = pyqtSignal(object)         
	error = pyqtSignal(object, object)         

	def __init__(self, parent, sourceFile, low_dark_th, low_hot_th, high_dark_th, \
            high_hot_th, rebinning, flatfielding_window, despeckle_window, \
            despeckle_thresh, output_low, output_high, output_diff, output_sum):
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
                self.output_low, self.output_high, self.output_diff, self.output_sum )		

			# At the end emit a signal with the outputs:
			self.processDone.emit( low, high, diff, sum, self.output_low, self.output_high, \
                                    self.output_diff, self.output_sum, self.sourceFile, \
                                    PREPROC_TABLABEL )

            # Log info:
			t2 = timeit.default_timer()
			self.logOutput.emit('Pre-processing performed succesfully in ' + \
				'{:.3f}'.format(t2 - t1) + ' sec.')

		except Exception as e:

            # Log error:
			self.error.emit('Error while performing pre-processing. ' + \
                'Operation aborted.', str(e))


class ReconThread(QThread):
	
	reconDone = pyqtSignal(object, object, object)      
	logOutput = pyqtSignal(object)         
	error = pyqtSignal(object, object)     

	def __init__(self, parent, im, sourceFile, angles, ssd, sdd, px, \
            det_u, det_v, short_scan=False, method='FDK', iterations=1):
		""" Class constructor.
		"""
		super(ReconThread, self).__init__(parent)

		self.im = im.astype(numpy.float32)
		self.angles = angles
		self.ssd = ssd
		self.sdd = sdd
		self.px = px
		self.det_u = det_u
		self.det_v = det_v
		self.sourceFile = sourceFile
		self.method = method
		self.iterations = iterations
		self.short_scan = short_scan


	def run(self):
		""" Run the thread.
		"""
		try:
			# Log info:
			t1 = timeit.default_timer()
			self.logOutput.emit('Performing reconstruction...')
			
			# Do the reconstruction:
			if (self.method == 'SIRT'):
				im = recon_astra_sirt(self.im, self.angles, self.ssd, self.sdd - self.ssd, \
						self.px, self.det_u, self.det_v, iterations=self.iterations)  
								  
			else: # default FDK       
				im = recon_astra_fdk(self.im, self.angles, self.ssd, self.sdd - self.ssd, \
						self.px, self.det_u, self.det_v, short_scan=self.short_scan)			

			# At the end emit a signal with the outputs:
			self.reconDone.emit(im, self.sourceFile, RECON_TABLABEL)

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

	def onQApplicationStarted(self):
		""" Things done as the main window is fully loaded.
		"""
		# Startup message:
		platf = platform.uname()

		cpus = psutil.cpu_count()
		stat = psutil.virtual_memory()
		ram = (stat.total) / (1024.0 * 1024 * 1024) # GB
	
		# system, node, release, version, machine, and processor.
		val = "KEST started on " + platf.node + " (# of CPUs: " + str(cpus) + ", RAM: " + \
			"{:.2f}".format(ram) + " GB)"
		
		# Log string:
		self.mainPanel.log.logOutput(val)


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


	def openFile(self):
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
				self.readThread = ReadThread(self, filename)
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

			# Get params from UI:
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
                despeckle_thresh, output_low, output_high, output_diff, output_sum)
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


			# Get parameters from UI:
			method = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Method")
			iterations = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Iterations")
			weights = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Weights")
			angles = self.sidebar.reconstructionTab.getValue("Reconstruction_Angles")
			nr_proj = self.sidebar.reconstructionTab.getValue("Reconstruction_Projections")
			upsampling = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Upsampling")
			overpadding = self.sidebar.reconstructionTab.getValue("ReconstructionAlgorithm_Overpadding")
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
			self.reconThread = ReconThread(self, im, sourceFile, angles, ssd, sdd, \
                px, det_u, det_v, short_scan, method, iterations)

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

		

	def readJobDone(self, low, high, sourceFile, type):
		""" When a job thread has completed this function is called.
		"""
		
		# Open a new tab in the image viewer with the output of reconstruction:
		self.mainPanel.addTab(low, sourceFile, str(os.path.basename(sourceFile)) \
			+ " - " + type, type)
	
		self.mainPanel.addTab(high, sourceFile, str(os.path.basename(sourceFile)) \
			+ " - " + type, type)

		# Restore the reconstruction button:
		self.sidebar.reconstructionTab.button.setEnabled(True) 
		self.sidebar.preprocessingTab.btnApply.setEnabled(True) 

	

	def preprocessJobDone( self, low, high, diff, sum, output_low, output_high, \
                           output_diff, output_sum, sourceFile, type ):
		""" This function is called when the preprocessing job thread has completed.
		"""
		
		# Open a new tab in the image viewer with the output of reconstruction:
		if (output_low):
			self.mainPanel.addTab(low, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type)
	
		if (output_high):    
			self.mainPanel.addTab(high, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type)

		if (output_diff):    
			self.mainPanel.addTab(diff, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type)
		
		if (output_sum):    
			self.mainPanel.addTab(sum, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type)

		# Restore the reconstruction button:
		self.sidebar.reconstructionTab.button.setEnabled(True) 
		self.sidebar.preprocessingTab.btnApply.setEnabled(True) 


	def reconstructJobDone(self, im, sourceFile, type):
		""" This function is called when the preprocessing job thread has completed.
		"""
		
		# Open a new tab in the image viewer with the output of reconstruction:
		self.mainPanel.addTab(im, sourceFile, str(os.path.basename(sourceFile)) \
				+ " - " + type, type)

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






	