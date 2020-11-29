import os.path
import numpy

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBar, QSizePolicy, QHBoxLayout
from PyQt5.QtWidgets import QToolButton, QSpacerItem, QLabel, QComboBox, QSlider, QFileDialog
from PyQt5.QtGui import QIcon, QFont, QBrush, QColor, QPalette
from PyQt5.QtCore import Qt

from kstUtils import eprint
from _kstImagePanel import _kstImagePanel

import tifffile

dir = os.path.dirname(os.path.realpath(__file__))
PAN_ZOOM_ICON = dir + "/resources/btnDrag.png"
PAN_ZOOM_TOOLTIP = "Pan (Mouse Left)"

ZOOM_SELECT_ICON = dir + "/resources/btnZoomSelect.png"
ZOOM_SELECT_TOOLTIP = "ROI Zoom (Mouse Left)"

ZOOM_IN_ICON = dir + "/resources/btnZoomIn.png"
ZOOM_IN_TOOLTIP = "Zoom In (Mouse Wheel)"

ZOOM_OUT_ICON = dir + "/resources/btnZoomOut.png"
ZOOM_OUT_TOOLTIP = "Zoom Out (Mouse Wheel)"

ZOOM_RESET_ICON = dir + "/resources/btnFitToScreen.png"
ZOOM_RESET_TOOLTIP = "Zoom Fit (Mouse Double Click Left)"

EXPORT_ICON = dir + "/resources/btnExport.png"
EXPORT_TOOLTIP = "Save as TIFF..."

EXPORTALL_ICON = dir + "/resources/btnExport.png"
EXPORTALL_TOOLTIP = "Save as TIFF sequence..."

class kstImageViewer(QWidget):

	def __init__(self, sourceFile, data, type, image, mode):
		""" Class constructor.
		"""
		QWidget.__init__(self)

		# Initialize image panel:
		self.imagePanel = _kstImagePanel()

		# Set original mode:
		self.__originalMode = mode

		# Set the type of image with respect of the lightfield pipeline:        
		self.__imageType = type      # 'raw', 'pre-processed', 'reconstructed', 'post-processed'

		# The actual object handled by the image viewer:
		self.__data = data

		# Properties:
		self.__sourceFile = sourceFile		
		
		# Current view index:
		self.__view = 0	
		
		# Top toolbar:
		self.topToolBar = QToolBar()
		self._createTopToolbar()

		# Bottom toolbar:
		self.bottomToolBar = QToolBar()
		self._createBottomToolbar()	

		# Handle mouse hover with custom slot:
		self.imagePanel.mouseHoverEvent.connect(self._handleMouseHover)

		# Compose layout of the whole widget:
		layout = QVBoxLayout()	
		layout.addWidget(self.topToolBar)
		layout.addWidget(self.imagePanel)
		layout.addWidget(self.bottomToolBar)	
		layout.setContentsMargins(0,0,0,0)	
		self.setLayout(layout)
		self.setContentsMargins(0,0,0,0)	

		# Set image:
		self.__setImage(image)



	def _createTopToolbar(self):
		"""
        """
		topToolbarSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)        
		self.topToolBar.setSizePolicy(topToolbarSizePolicy)

		#pan_zoom = QAction(QIcon(dir + "/resources/btnDrag.png"),"Pan (Mouse
		#Left)",self)
		#self.toolBar.addAction(pan_zoom)
		#zoomSelect = QAction(QIcon(dir + "/resources/btnZoomSelect.png"),"ROI Zoom
		#(Mouse Left)",self)
		#self.toolBar.addAction(zoomSelect)
		exitAct = QAction('Exit', self)
		exitAct.setShortcut('Ctrl+Q')

		self._panZoom = QToolButton(self)
		self._panZoom.setIcon(QIcon(PAN_ZOOM_ICON))
		self._panZoom.setToolTip(PAN_ZOOM_TOOLTIP)
		self._panZoom.setCheckable(True)
		self._panZoom.setChecked(True)
		self._panZoom.clicked.connect(self._panZoomSwitch)
		self.topToolBar.addWidget(self._panZoom)

		self._zoomSelect = QToolButton(self)
		self._zoomSelect.setIcon(QIcon(ZOOM_SELECT_ICON))
		self._zoomSelect.setToolTip(ZOOM_SELECT_TOOLTIP)
		self._zoomSelect.setCheckable(True)
		self._zoomSelect.setChecked(False)
		self._zoomSelect.clicked.connect(self._zoomSelectSwitch)
		self.topToolBar.addWidget(self._zoomSelect)

		self.topToolBar.addSeparator()

		zoomIn = QAction(QIcon(ZOOM_IN_ICON),ZOOM_IN_TOOLTIP,self)        
		self.topToolBar.addAction(zoomIn)
		zoomOut = QAction(QIcon(ZOOM_OUT_ICON),ZOOM_OUT_TOOLTIP,self)        
		self.topToolBar.addAction(zoomOut)
		zoomReset = QAction(QIcon(ZOOM_RESET_ICON),ZOOM_RESET_TOOLTIP,self)        
		self.topToolBar.addAction(zoomReset)

		self.topToolBar.addSeparator()

		# Separator:
		#self.fooWidget = QWidget()
		#self.fooWidget.setFixedWidth(6)
		#self.fooWidgetAction = self.topToolBar.addWidget(self.fooWidget)

		#self.extraSeparatorAction = self.topToolBar.addSeparator()

		export = QAction(QIcon(EXPORT_ICON),EXPORT_TOOLTIP,self)        
		self.topToolBar.addAction(export)

		exportAll = QAction(QIcon(EXPORTALL_ICON),EXPORTALL_TOOLTIP,self)        
		self.topToolBar.addAction(exportAll)
								
		# Spacer:
		spacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)   
		spacer.setSizePolicy(spacerSizePolicy)
		self.topToolBar.addWidget(spacer)
		
		# Label on the right:
		self.hoverLabel = QLabel(self)
		self.hoverLabel.setText("")
		self.topToolBar.addWidget(self.hoverLabel) 
			

		# Connect handler for toolbar buttons:
		self.topToolBar.actionTriggered[QAction].connect(self._toolBarBtnPressed)




	def _createBottomToolbar(self):
		"""
		"""
		
		bottomToolbarSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)        
		self.bottomToolBar.setSizePolicy(bottomToolbarSizePolicy)	
	
		# Combo box for the 4 "views" of a dataset:
		self.lblView = QLabel(" View: ")   # Use spaces		
		self.lblViewAction = self.bottomToolBar.addWidget(self.lblView)			

		self.cbxView = QComboBox()
		self.cbxView.addItems(["Projection/Axial", "Sinogram/Sagittal", "Lateral/Frontal"])
		self.cbxView.currentIndexChanged.connect(self.changeView)
		self.cbxViewAction = self.bottomToolBar.addWidget(self.cbxView)	
		
	
		self.indexLabel = QLabel(self)
		self.indexLabel.setText("")
		self.indexLabel.setFixedWidth(70)
		self.indexLabel.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.bottomToolBar.addWidget(self.indexLabel)


		# Slider for the projection/slices:
		self.lblImageSlider = QLabel(" Image: ") # Use spaces
		self.lblImageSliderAction = self.bottomToolBar.addWidget(self.lblImageSlider)
		
		self.sldDataset = QSlider(Qt.Horizontal) 
		self.sldDataset.setFixedWidth(250)
		self.sldDataset.setFocusPolicy(Qt.StrongFocus)
		self.sldDataset.setTickPosition(QSlider.TicksBelow)
		self.sldDataset.valueChanged.connect(self.changeDatasetView)		
		self.sldDatasetAction = self.bottomToolBar.addWidget(self.sldDataset)		
		
		# Slider for the repetitions:
		self.lblRepetitionIndex = QLabel(self)
		self.lblRepetitionIndex.setText("")
		self.lblRepetitionIndex.setFixedWidth(50)
		self.lblRepetitionIndex.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.bottomToolBar.addWidget(self.lblRepetitionIndex)

		self.lblRepetitionSlider = QLabel(" Repetition: ") # Use spaces
		self.lblRepetitionSlider.setFixedWidth(80)
		self.lblRepetitionSlider.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
		self.lblRepetitionSliderAction = self.bottomToolBar.addWidget(self.lblRepetitionSlider)		
		
		self.sldRepetition = QSlider(Qt.Horizontal) 
		self.sldRepetition.setFixedWidth(150)
		self.sldRepetition.setFocusPolicy(Qt.StrongFocus)
		self.sldRepetition.setTickPosition(QSlider.TicksBelow)
		self.sldRepetition.valueChanged.connect(self.changeRepetitionView)
		self.sldRepetitionAction = self.bottomToolBar.addWidget(self.sldRepetition)		
			

		if self.__data.ndim == 4:
			self.lblRepetitionSliderAction.setVisible(True)
			self.sldRepetitionAction.setVisible(True)
		else:
			self.lblRepetitionSliderAction.setVisible(False)
			self.sldRepetitionAction.setVisible(False)
			

	#def drawBackground(self, painter, rect):

	#	color = self.palette().color(QPalette.Background)
	#	background_brush = QBrush( color, Qt.SolidPattern)
	#	painter.fillRect(rect, background_brush)

	def _panZoomSwitch(self):

		self._zoomSelect.setChecked(not self._panZoom.isChecked())
		self.imagePanel.togglePanZoom = self._zoomSelect.isChecked()

	def _zoomSelectSwitch(self):

		self._panZoom.setChecked(not self._zoomSelect.isChecked())
		self.imagePanel.togglePanZoom = self._zoomSelect.isChecked()
		
	def _toolBarBtnPressed(self, button):

		if button.text() == ZOOM_IN_TOOLTIP:
			self.imagePanel.performZoom(min(400.0,self.imagePanel.zoomFactor*1.15))
		elif button.text() == ZOOM_OUT_TOOLTIP:
			self.imagePanel.performZoom(max(1.0,self.imagePanel.zoomFactor/1.15))
		elif button.text() == ZOOM_RESET_TOOLTIP:
			self.imagePanel.performZoom(1.0)
		elif button.text() == EXPORT_TOOLTIP:

			# Open a Save As dialog:
			try:
				options = QFileDialog.Options()
				options |= QFileDialog.DontUseNativeDialog
				filename, _ = QFileDialog.getSaveFileName(self,"Save as TIFF", 
							  "","TIFF Files (*.tif);;All Files (*)", options=options)
				if filename:
				
					# Call the method to save the current displayed image:
					self.imagePanel.saveAsTIFF(filename)

			except Exception as e:
				eprint(str(e))

		elif button.text() == EXPORTALL_TOOLTIP:

			# Open a Save As dialog:
			try:
				options = QFileDialog.Options()
				options |= QFileDialog.DontUseNativeDialog
				options |= QFileDialog.DirectoryOnly
				folder = QFileDialog.getExistingDirectory(self, "Select Folder for TIFF sequence")

				if folder: 			
				
					for i in range(0,self.__data.shape[2]):
		
						# Prepare filename:
						filename = os.path.join(folder, "image_" + "{:04d}".format(i) + ".tif")

						# Save as TIFF with tiffile library:
						tifffile.imsave(filename, data=self.__data[:,:,i])

			except Exception as e:
				eprint(str(e))
			



	def _handleMouseHover(self, x, y, z, type):

		if (x == -1):
			self.hoverLabel.setText("")
		else:
			if (type == 'float'):
				s = "{:0.4f}".format(z) if (z > 1e-2) else "{:.4E}".format(z)
			else:
				s = "{:d}".format(round(z))
			self.hoverLabel.setText("[" + str(x) + "," + str(y) + "]=" + s + " " )


	def __setImage(self, npImage):
		""" Set the scene's current image pixmap to the input image as a numpy array.
		:type npImage: numpy array
		"""
		# Set the new numpy image:
		self.imagePanel.setImage(npImage)  

		# Enable/disable UI widgets:
		if (self.__imageType == 'raw'):
			self.lblViewAction.setVisible(True)
			self.cbxViewAction.setVisible(True)
			self.lblImageSliderAction.setVisible(True)
			self.sldDatasetAction.setVisible(True)
			if self.__data.ndim == 4:
				self.lblRepetitionSliderAction.setVisible(True)
				self.lblRepetitionIndex.setVisible(True)
				self.sldRepetitionAction.setVisible(True)
			else:
				self.lblRepetitionSliderAction.setVisible(False)
				self.lblRepetitionIndex.setVisible(False)
				self.sldRepetitionAction.setVisible(False)

		elif (self.__imageType == 'pre-processed'):
			self.lblViewAction.setVisible(True)
			self.cbxViewAction.setVisible(True)
			self.lblImageSliderAction.setVisible(True)
			self.sldDatasetAction.setVisible(True)
			self.sldRepetitionAction.setVisible(False)
			self.lblRepetitionIndex.setVisible(False)
			self.lblRepetitionSliderAction.setVisible(False)

		elif (self.__imageType == 'reconstructed'):
			self.lblViewAction.setVisible(True)
			self.cbxViewAction.setVisible(True)
			self.lblImageSliderAction.setVisible(True)
			self.sldDatasetAction.setVisible(True)
			self.sldRepetitionAction.setVisible(False)
			self.lblRepetitionIndex.setVisible(False)
			self.lblRepetitionSliderAction.setVisible(False)

		# Set dimension of the slider and default:
		self.sldDataset.setMinimum(0)
		self.sldDataset.setMaximum(self.__data.shape[2]-1)
		self.sldDataset.setValue(round(self.__data.shape[2]/2))

		self.indexLabel.setText(str(round(self.__data.shape[2]/2)) \
			+ "/" + str(round(self.__data.shape[2])))


	def changeView(self, idx):
		""" Called when the combo box index is changed.
		"""
		# Reset sliders:
		self.sldDataset.setValue(0)
		if self.__data.ndim == 4:
			self.sldRepetition.setValue(0)
	
		# Transpose datasets:
		if idx == 0: # Axial or projection view:
			if self.__data.ndim == 4:
				if self.__view == 1:
					self.__data = numpy.transpose(self.__data, (2,1,0,3)) # OK
				if self.__view == 2:
					self.__data = numpy.transpose(self.__data, (1,2,0,3)) # OK
			else:
				if self.__view == 1:				    
					self.__data = numpy.transpose(self.__data, (2,1,0))   # OK
				if self.__view == 2:
					self.__data = numpy.transpose(self.__data, (1,2,0))   # OK

		elif idx == 1: # Sinogram of sagittal view:
			if self.__data.ndim == 4:
				if self.__view == 0:
					self.__data = numpy.transpose(self.__data, (2,1,0,3)) # OK
				if self.__view == 2:
					self.__data = numpy.transpose(self.__data, (0,2,1,3)) # OK
			else:
				if self.__view == 0:				    
					self.__data = numpy.transpose(self.__data, (2,1,0))   # OK
				if self.__view == 2:
					self.__data = numpy.transpose(self.__data, (0,2,1))   # OK

		else: # Lateral or coronal view:
			if self.__data.ndim == 4:
				if self.__view == 0:
					self.__data = numpy.transpose(self.__data, (2,0,1,3)) # OK
				if self.__view == 1:
					self.__data = numpy.transpose(self.__data, (0,2,1,3)) # OK
			else:
				if self.__view == 0:				    
					self.__data = numpy.transpose(self.__data, (2,0,1))   # OK
				if self.__view == 1:
					self.__data = numpy.transpose(self.__data, (0,2,1))   # OK

		# Set new view:
		self.__view = idx


		# Change to the new numpy image:
		if self.__data.ndim == 4:
			self.imagePanel.changeImage(self.__data[:,:,round(self.__data.shape[2]/2),round(self.__data.shape[3]/2)])
		else:
			self.imagePanel.changeImage(self.__data[:,:,round(self.__data.shape[2]/2)])

		# Set the index:
		self.sldDataset.setMinimum(0)
		self.sldDataset.setMaximum(self.__data.shape[2]-1)
		self.sldDataset.setValue(round(self.__data.shape[2]/2))
	
		# Reset zoom:
		self.imagePanel.performZoom(1.0)

	def changeDatasetView(self):
		""" Called when the slider is moved, so user wants to see a different 
            projection or slice.
		"""
		val = int(self.sldDataset.value())		

		# Change to the new numpy image:
		if self.__data.ndim == 4:
			rep = int(self.sldRepetition.value())
			self.imagePanel.changeImage(self.__data[:,:,val,rep])            
			#self.sldRepetition.setValue(round(self.__data.shape[3]/2))
		else:
			self.imagePanel.changeImage(self.__data[:,:,val])

		# Set the index:
		self.indexLabel.setText(str(val + 1) + "/" + str(round(self.__data.shape[2])))


	def changeRepetitionView(self):
		""" Called when the slider is moved, so user wants to see a different
			repetition of the same projection.
		"""
		img = int(self.sldDataset.value())
		val = int(self.sldRepetition.value())

		# Change to the new numpy image:
		self.imagePanel.changeImage(self.__data[:,:,img,val])

		# Set the index:
		self.lblRepetitionIndex.setText(str(val+1) + "/" + str(round(self.__data.shape[3])))
			

	def getType(self):
		""" Get the type of current image viewer.
		"""

		# Set the new numpy image:
		return self.__imageType


	def getOriginalMode(self):
		""" Get the original mode (2COL or 1COL).
		"""

		# Set the new numpy image:
		return self.__originalMode


	def getSourceFile(self):
		""" Get the source file of current image viewer.
		"""

		# Set the new numpy image:
		return self.__sourceFile


	def getImage(self):
		""" Get the scene's current image pixmap as a numpy array.
		"""

		# Set the new numpy image:
		return self.imagePanel.npImage


	def getData(self):
		""" Get the data connected to this image viewer.
		"""
		
		return self.__data