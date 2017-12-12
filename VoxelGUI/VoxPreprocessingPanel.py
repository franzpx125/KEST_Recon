from PyQt5.QtWidgets import QApplication, QLineEdit, QVBoxLayout
from PyQt5.QtCore import QVariant, QSize
#    QDate, 
#    QTime, 
#    QDateTime, 
#    Qt, 
#    QLocale, 
#    QPoint, 
#    QPointF, 
#    QSize, 
#    QSizeF, 
#    QRect, 
#    QRectF
#    )

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QSizePolicy, QPushButton, QHBoxLayout

from QtProperty.pyqtcore import QList, QMap
from QtProperty.qtvariantproperty import QtVariantEditorFactory, QtVariantPropertyManager
from QtProperty.qttreepropertybrowser import QtTreePropertyBrowser
from QtProperty.qtgroupboxpropertybrowser import QtGroupBoxPropertyBrowser



class VoxPreprocessingPanel(QWidget):

    # Event raised when the user wants to perform the pre-processing:
	preprocessingRequestedEvent = pyqtSignal()

    # Event raised when the user wants to perform the auto calibrate:
	calibrateRequestedEvent = pyqtSignal()

	def __init__(self):
		""" Class constructor.
		"""
		QWidget.__init__(self)		

		# Property manager and related events:
		self.variantManager = QtVariantPropertyManager()
		self.propertyToId = QMap()
		self.idToProperty = QMap()
		self.variantManager.valueChangedSignal.connect(self.valueChanged)

        # Un/comment the following two lines for a different look & feel:
		#self.variantEditor = QtGroupBoxPropertyBrowser()
		self.variantEditor = QtTreePropertyBrowser()
		self.variantFactory = QtVariantEditorFactory()
		self.variantEditor.setFactoryForManager(self.variantManager, self.variantFactory)

		# Spacer widget to have left and right aligned buttons:
		btnWidget = QWidget()
		btnWidgetLayout = QHBoxLayout()
		btnWidgetSpacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum) 
		btnWidgetSpacer.setSizePolicy(spacerSizePolicy)

        # Calibrate button (left aligned):
		self.btnCalibrate = QPushButton('Calibrate', self)
		self.btnCalibrate.clicked.connect(self.handleCalibrate)

        # Apply button (right aligned):
		self.btnApply = QPushButton('Apply', self)
		self.btnApply.clicked.connect(self.handleApply)

        # Compose the layout with the buttons and the spacer:
		btnWidgetLayout.addWidget(self.btnCalibrate)
		btnWidgetLayout.addWidget(btnWidgetSpacer)  
		btnWidgetLayout.addWidget(self.btnApply)    
		btnWidgetLayout.setContentsMargins(0,0,0,0)	
		btnWidget.setLayout(btnWidgetLayout)

		# Extra vertical spacer to have all the properties top-aligned:
		spacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)   
		spacer.setSizePolicy(spacerSizePolicy)
	
        # Configuration of the properties manager:
		self.inputLensletItem = self.variantManager.addProperty(\
            QtVariantPropertyManager.groupTypeId(), "Input lenslet")
	
		item = self.variantManager.addProperty(QVariant.Double, "Width")
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		item.setValue(-1) # default
		self.inputLensletItem.addSubProperty(item)        
		self.addProperty(item, "InputLenslet_Width")

		item = self.variantManager.addProperty(QVariant.Double, "Height")
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		item.setValue(-1) # default
		self.inputLensletItem.addSubProperty(item)        
		self.addProperty(item, "InputLenslet_Height")

		item = self.variantManager.addProperty(QVariant.Double, "Offset Top")
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		item.setValue(-1) # default
		self.inputLensletItem.addSubProperty(item)        
		self.addProperty(item, "InputLenslet_OffsetTop")

		item = self.variantManager.addProperty(QVariant.Double, "Offset Left")
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		item.setValue(-1) # default
		self.inputLensletItem.addSubProperty(item)        
		self.addProperty(item, "InputLenslet_OffsetLeft")

		self.outputLensletItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Output lenslet")
	
		item = self.variantManager.addProperty(QVariant.Int, "Width")
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 1024)
		item.setAttribute("singleStep", 1)
		item.setValue(0)
		self.outputLensletItem.addSubProperty(item)        
		self.addProperty(item, "OutputLenslet_Width")

		item = self.variantManager.addProperty(QVariant.Int, "Height")
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 1024)
		item.setAttribute("singleStep", 1)
		item.setValue(0) # default
		self.outputLensletItem.addSubProperty(item)        
		self.addProperty(item, "OutputLenslet_Height")


		

	
		self.variantEditor.addProperty(self.inputLensletItem)
		self.variantEditor.addProperty(self.outputLensletItem)

		if isinstance(self.variantEditor, QtTreePropertyBrowser):
			self.variantEditor.setPropertiesWithoutValueMarked(True)
			self.variantEditor.setRootIsDecorated(False)
			self.variantEditor.setHeaderVisible(False)
	
		layout = QVBoxLayout()
		layout.addWidget(self.variantEditor)   
		layout.addWidget(btnWidget)     
		layout.addWidget(spacer)    
		layout.setContentsMargins(0,0,0,0)	
		self.setLayout(layout)


	def addProperty(self, property, id):
		""" Add the specified property to the internal table of properties.
		"""
		self.propertyToId[property] = id
		self.idToProperty[id] = property 


	def valueChanged(self, property, value):
		""" Updates the property when a value is changed in the UI.
		"""
		if (not self.propertyToId.contains(property)):
			return
		
        # Nothing done...

	def getValue(self, id):
		""" Get the value of the specified property.
		"""
		if (self.idToProperty.contains(id)):

			p = self.idToProperty[id]
			return self.variantManager.value(p)


	def setValue(self, id, val):
		""" Set the specified property with the specified value.
		"""
		if (self.idToProperty.contains(id)):

			p = self.idToProperty[id]
			self.variantManager.setValue(p, val)

	
	def handleApply(self):
		""" Raise an event when user wants to perform the preprocessing.
		"""

		# Emit the event:
		self.preprocessingRequestedEvent.emit()



	def handleCalibrate(self):
		""" Raise an event when user wants to perform the calibration.
		"""

		# Emit the event:
		self.calibrateRequestedEvent.emit()


