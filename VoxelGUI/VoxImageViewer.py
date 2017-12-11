import os.path

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBar, QSizePolicy
from PyQt5.QtWidgets import QToolButton, QSpacerItem, QLabel, QComboBox, QSlider, QFileDialog
from PyQt5.QtGui import QIcon, QFont, QBrush, QColor, QPalette
from PyQt5.QtCore import Qt

from VoxUtils import eprint
from _VoxImagePanel import _VoxImagePanel

import vox.lightfield

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
EXPORT_TOOLTIP = "Save as TIFF"

class VoxImageViewer(QWidget):

	def __init__(self, sourceFile, data, type, image ):

		QWidget.__init__(self)

		# Initialize image panel:
		self.imagePanel = _VoxImagePanel()

		# Set the type of image with respect of the lightfield pipeline:        
		self.__imageType = type      # 'raw', 'lightfield', 'refocused', 'depth_map'

		# The actual object handled by the image viewer:
		self.__data = data

		# Properties:
		self.__sourceFile = sourceFile			
		
		# Toolbar:
		self.toolBar = QToolBar()
		toolbarSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)        
		self.toolBar.setSizePolicy(toolbarSizePolicy)
			

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
		self.toolBar.addWidget(self._panZoom)

		self._zoomSelect = QToolButton(self)
		self._zoomSelect.setIcon(QIcon(ZOOM_SELECT_ICON))
		self._zoomSelect.setToolTip(ZOOM_SELECT_TOOLTIP)
		self._zoomSelect.setCheckable(True)
		self._zoomSelect.setChecked(False)
		self._zoomSelect.clicked.connect(self._zoomSelectSwitch)
		self.toolBar.addWidget(self._zoomSelect)

		self.toolBar.addSeparator()

		zoomIn = QAction(QIcon(ZOOM_IN_ICON),ZOOM_IN_TOOLTIP,self)        
		self.toolBar.addAction(zoomIn)
		zoomOut = QAction(QIcon(ZOOM_OUT_ICON),ZOOM_OUT_TOOLTIP,self)        
		self.toolBar.addAction(zoomOut)
		zoomReset = QAction(QIcon(ZOOM_RESET_ICON),ZOOM_RESET_TOOLTIP,self)        
		self.toolBar.addAction(zoomReset)

		self.toolBar.addSeparator()

		# Combo box for the 4 "views" of a light-field image:
		self.lblLightField = QLabel(" Lightfield: ")   # Use spaces		
		self.lblLightFieldAction = self.toolBar.addWidget(self.lblLightField)		

		self.cbxLightField = QComboBox()
		for mode in vox.lightfield.VoxLightfield.available_modes:
			self.cbxLightField.addItem(mode)
		self.cbxLightFieldAction = self.toolBar.addWidget(self.cbxLightField)		

		# Slider for the refocusing:
		self.lblRefocusing = QLabel(" Refocusing: ") # Use spaces
		self.lblRefocusingAction = self.toolBar.addWidget(self.lblRefocusing)		
		
		self.sldRefocusing = QSlider(Qt.Horizontal) 
		self.sldRefocusing.setFixedWidth(150)
		self.sldRefocusing.setFocusPolicy(Qt.StrongFocus)
		self.sldRefocusing.setTickPosition(QSlider.TicksBelow)
		self.sldRefocusingAction = self.toolBar.addWidget(self.sldRefocusing)		
		self.sldRefocusing.valueChanged.connect(self.changeRefocusedView)

        # Separator:
		self.fooWidget = QWidget()
		self.fooWidget.setFixedWidth(6)
		self.fooWidgetAction = self.toolBar.addWidget(self.fooWidget)

		self.extraSeparatorAction = self.toolBar.addSeparator()

		export = QAction(QIcon(EXPORT_ICON),EXPORT_TOOLTIP,self)        
		self.toolBar.addAction(export)
								
		# Spacer:
		spacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)   
		spacer.setSizePolicy(spacerSizePolicy)
		self.toolBar.addWidget(spacer)
		
		# Label on the right:
		self.hoverLabel = QLabel(self)
		self.hoverLabel.setText("")
		self.toolBar.addWidget(self.hoverLabel) 
			

		# Connect handler for toolbar buttons:
		self.toolBar.actionTriggered[QAction].connect(self._toolBarBtnPressed)

	

		# Handle mouse hover with custom slot:
		self.imagePanel.mouseHoverEvent.connect(self._handleMouseHover)

		# Compose layout of the whole widget:
		layout = QVBoxLayout()	
		layout.addWidget(self.toolBar)
		layout.addWidget(self.imagePanel)	
		layout.setContentsMargins(0,0,0,0)	
		self.setLayout(layout)
		self.setContentsMargins(0,0,0,0)	


		# Set image:
		self.__setImage(image)

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
			self.lblLightFieldAction.setVisible(False)
			self.cbxLightFieldAction.setVisible(False)
			self.lblRefocusingAction.setVisible(False)
			self.sldRefocusingAction.setVisible(False)
			self.fooWidgetAction.setVisible(False)
			self.extraSeparatorAction.setVisible(False)
		elif (self.__imageType == 'lightfield'):
			self.lblLightFieldAction.setVisible(True)
			self.cbxLightFieldAction.setVisible(True)
			self.lblRefocusingAction.setVisible(False)
			self.sldRefocusingAction.setVisible(False)
			self.fooWidgetAction.setVisible(True)
			self.extraSeparatorAction.setVisible(True)
		elif (self.__imageType == 'refocused'):
			self.lblLightFieldAction.setVisible(False)
			self.cbxLightFieldAction.setVisible(False)
			self.lblRefocusingAction.setVisible(True)
			self.sldRefocusingAction.setVisible(True)
			self.fooWidgetAction.setVisible(True)
			self.extraSeparatorAction.setVisible(True)

			# Set dimension of the slider:
			self.sldRefocusing.setMinimum(0)
			self.sldRefocusing.setMaximum(self.__data.shape[0]-1)
			self.sldRefocusing.setValue(round(self.__data.shape[0]))


	def changeRefocusedView(self):
		""" Called when the slider is moved, so user wants to see a different
			refocused image.
		"""
		val = int(self.sldRefocusing.value())

		# Change to the new numpy image:
		self.imagePanel.changeImage(self.__data[val,:,:])
			

	def getType(self):
		""" Get the type of current image viewer.
		"""

		# Set the new numpy image:
		return self.__imageType

	def getSourceFile(self):
		""" Get the source file of current image viewer.
		"""

		# Set the new numpy image:
		return self.__sourceFile

	def getImage(self):
		""" Get the scene's current image pixmap to the input image as a numpy array.
		"""

		# Set the new numpy image:
		return self.imagePanel.npImage

	def getData(self):
		""" Get the data connected to this image viewer.
		"""
		
		return self.__data