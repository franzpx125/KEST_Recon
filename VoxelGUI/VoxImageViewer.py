import os.path

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBar, QSizePolicy
from PyQt5.QtWidgets import QToolButton, QSpacerItem, QLabel
from PyQt5.QtGui import QIcon, QFont

from _VoxImagePanel import _VoxImagePanel

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
		dir = os.path.dirname(os.path.realpath(__file__))
		pan_zoom = QAction(QIcon(dir + "/resources/btnDrag.png"),"Pan / ROI Zoom (Mouse Left)",self)        
		self.toolBar.addAction(pan_zoom)
		zoomIn = QAction(QIcon(dir + "/resources/btnZoomIn.png"),"Zoom In (Mouse Wheel)",self)        
		self.toolBar.addAction(zoomIn)
		zoomOut = QAction(QIcon(dir + "/resources/btnZoomOut.png"),"Zoom Out (Mouse Wheel)",self)        
		self.toolBar.addAction(zoomOut)
		zoomReset = QAction(QIcon(dir + "/resources/btnFitToScreen.png"),"Zoom Fit (Mouse Double Click Left)",self)        
		self.toolBar.addAction(zoomReset)

		#toolButton = QToolButton(self)
		#toolButton.setIcon(QIcon("./resources/btnSelect.png"))
		#toolButton.setCheckable(True)
		#self.toolBar.addWidget(toolButton)
						
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
		layout.setContentsMargins(0,0,0,1)	
		self.setLayout(layout)


	def _toolBarBtnPressed(self, button):

		if button.text() == "Pan / ROI Zoom (Mouse Left)":
			self.imagePanel.togglePanZoom = not self.imagePanel.togglePanZoom


	def _handleMouseHover(self, x, y, z):
		s = "{:0.4f}".format(z) if (z > 1e-2) else "{:.4E}".format(z)
		if (x == -1):
			self.hoverLabel.setText("")
		else:
			self.hoverLabel.setText("[" + str(x) + "," + str(y) + "]=" + s)


	def setImage(self, npImage):
		""" Set the scene's current image pixmap to the input image as a numpy float 32 array.
		:type npImage: numpy array
		"""

		# Set the new numpy image:
		self.imagePanel.setImage(npImage)  