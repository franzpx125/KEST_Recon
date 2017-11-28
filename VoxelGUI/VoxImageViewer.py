import os.path

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBar, QSizePolicy
from PyQt5.QtWidgets import QToolButton, QSpacerItem, QLabel
from PyQt5.QtGui import QIcon, QFont, QBrush, QColor, QPalette

from _VoxImagePanel import _VoxImagePanel

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

class VoxImageViewer(QWidget):

	def __init__(self):

		QWidget.__init__(self)

		exitAct = QAction('Exit', self)
		exitAct.setShortcut('Ctrl+Q')
		
		# Toolbar:
		self.toolBar = QToolBar()
		toolbarSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)        
		self.toolBar.setSizePolicy(toolbarSizePolicy)

		# Buttons on the left:
		

		#pan_zoom = QAction(QIcon(dir + "/resources/btnDrag.png"),"Pan (Mouse Left)",self)        
		#self.toolBar.addAction(pan_zoom)
		#zoomSelect = QAction(QIcon(dir + "/resources/btnZoomSelect.png"),"ROI Zoom (Mouse Left)",self)        
		#self.toolBar.addAction(zoomSelect)

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

		# Initialize image panel:
		self.imagePanel = _VoxImagePanel()

		# Handle mouse hover with custom slot:
		self.imagePanel.mouseHoverEvent.connect(self._handleMouseHover)

		# Compose layout of the whole widget:
		layout = QVBoxLayout()	
		layout.addWidget(self.toolBar)
		layout.addWidget(self.imagePanel)	
		layout.setContentsMargins(0,0,0,0)	
		self.setLayout(layout)
		self.setContentsMargins(0,0,0,0)	

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



	def _handleMouseHover(self, x, y, z):
		s = "{:0.4f}".format(z) if (z > 1e-2) else "{:.4E}".format(z)
		if (x == -1):
			self.hoverLabel.setText("")
		else:
			self.hoverLabel.setText("[" + str(x) + "," + str(y) + "]=" + s + " " )


	def setImage(self, npImage):
		""" Set the scene's current image pixmap to the input image as a numpy float 32 array.
		:type npImage: numpy array
		"""

		# Set the new numpy image:
		self.imagePanel.setImage(npImage)  