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



class kstPreprocessingPanel(QWidget):

    # Event raised when the user wants to perform the pre-processing:
	preprocessingRequestedEvent = pyqtSignal()

    # Event raised when the user wants to perform the auto calibrate:
	calibrateRequestedEvent = pyqtSignal()

    # Available projection averaging methods:
	projection_averaging_methods = ('average', 'median', 'sum', 'minimum', 'maximum','extract')

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
		self.variantEditor = QtGroupBoxPropertyBrowser()
		#self.variantEditor = QtTreePropertyBrowser() # Not working in Python 3.8
		self.variantFactory = QtVariantEditorFactory()
		self.variantEditor.setFactoryForManager(self.variantManager, self.variantFactory)

		# Spacer widget to have left and right aligned buttons:
		btnWidget = QWidget()
		btnWidgetLayout = QHBoxLayout()
		btnWidgetSpacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum) 
		btnWidgetSpacer.setSizePolicy(spacerSizePolicy)


        # Apply button (right aligned):
		self.btnApply = QPushButton('Apply', self)
		self.btnApply.clicked.connect(self.handleApply)
		btnWidgetLayout.addWidget(btnWidgetSpacer)  
		btnWidgetLayout.addWidget(self.btnApply)    
		btnWidgetLayout.setContentsMargins(0,0,0,0)	
		btnWidget.setLayout(btnWidgetLayout)

		# Extra vertical spacer to have all the properties top-aligned:
		spacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)   
		spacer.setSizePolicy(spacerSizePolicy)


        # Configuration of the properties manager:
		self.cropItem = self.variantManager.addProperty(\
            QtVariantPropertyManager.groupTypeId(), "Crop")
		
		item = self.variantManager.addProperty(QVariant.Int, "Top")
		item.setValue(0) # default for dead pixels
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 402)
		item.setAttribute("singleStep", 1)
		item.setEnabled(True) # default
		self.cropItem.addSubProperty(item)        
		self.addProperty(item, "Crop_Top")

		item = self.variantManager.addProperty(QVariant.Int, "Bottom")
		item.setValue(0) # default for hot pixels
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 402)
		item.setAttribute("singleStep", 1)
		item.setEnabled(True) # default
		self.cropItem.addSubProperty(item)        
		self.addProperty(item, "Crop_Bottom")

		item = self.variantManager.addProperty(QVariant.Int, "Left")
		item.setValue(0) # default for dead pixels
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 512)
		item.setAttribute("singleStep", 1)
		item.setEnabled(True) # default
		self.cropItem.addSubProperty(item)        
		self.addProperty(item, "Crop_Left")

		item = self.variantManager.addProperty(QVariant.Int, "Right")
		item.setValue(0) # default for hot pixels
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 512)
		item.setAttribute("singleStep", 1)
		item.setEnabled(True) # default
		self.cropItem.addSubProperty(item)        
		self.addProperty(item, "Crop_Right")

         # Configuration of the properties manager:
		self.projectionAveragingItem = self.variantManager.addProperty(\
            QtVariantPropertyManager.groupTypeId(), "Projection averaging")

		
		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Mode")
		enumNames = QList()
		for method in kstPreprocessingPanel.projection_averaging_methods:  
			enumNames.append(method)
		item.setAttribute("enumNames", enumNames)
		item.setValue(0) 
		self.projectionAveragingItem.addSubProperty(item)        
		self.addProperty(item, "ProjectionAveraging_Mode")

		item = self.variantManager.addProperty(QVariant.Int, "Alpha-trimmed")
		item.setValue(2) # default for dead pixels
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 10)
		item.setAttribute("singleStep", 1)
		item.setEnabled(True) # default
		self.projectionAveragingItem.addSubProperty(item)        
		self.addProperty(item, "ProjectionAveraging_AlphaTrimmed")


        # Configuration of the properties manager:
		self.matrixManipulationItem = self.variantManager.addProperty(\
            QtVariantPropertyManager.groupTypeId(), "Matrix manipulation")

		item = self.variantManager.addProperty(QVariant.Bool, "Rebinning 2x2")
		item.setValue(False) # default
		self.matrixManipulationItem.addSubProperty(item)        
		self.addProperty(item, "MatrixManipulation_Rebinning2x2")

		self.flatFieldingItem = self.variantManager.addProperty(\
		QtVariantPropertyManager.groupTypeId(), "Flat Fielding")
	
		item = self.variantManager.addProperty(QVariant.Int, "Window")
		item.setValue(5) # default for dead pixels
		item.setAttribute("minimum", 3)
		item.setAttribute("maximum", 11)
		item.setAttribute("singleStep", 2)
		item.setEnabled(True) # default
		self.flatFieldingItem.addSubProperty(item)        
		self.addProperty(item, "FlatFielding_Window")


		self.correctionItem = self.variantManager.addProperty(\
		QtVariantPropertyManager.groupTypeId(), "Image correction")
	
		item = self.variantManager.addProperty(QVariant.Double, "Despeckle")
		item.setValue(0.25) # default for dead pixels
		item.setAttribute("minimum", 0.0)
		item.setAttribute("maximum", 1.0)
		item.setAttribute("singleStep", 0.1)
		item.setEnabled(True) # default
		self.correctionItem.addSubProperty(item)        
		self.addProperty(item, "Despeckle_Threshold")

		#item = self.variantManager.addProperty(QVariant.Int, "Ring removal")
		#item.setValue(5) # default for dead pixels
		#item.setAttribute("minimum", 3)
		#item.setAttribute("maximum", 99)
		#item.setAttribute("singleStep", 2)
		#item.setEnabled(True) # default
		#self.correctionItem.addSubProperty(item)        
		#self.addProperty(item, "RingRemoval_Threshold")


		self.outputItem = self.variantManager.addProperty(\
		QtVariantPropertyManager.groupTypeId(), "Output")
	
		item = self.variantManager.addProperty(QVariant.Bool, "Low energy")
		item.setValue(False) # default
		self.outputItem.addSubProperty(item)        
		self.addProperty(item, "Output_LowEnergy")

		item = self.variantManager.addProperty(QVariant.Bool, "High energy")
		item.setValue(False) # default
		self.outputItem.addSubProperty(item)        
		self.addProperty(item, "Output_HighEnergy")

		item = self.variantManager.addProperty(QVariant.Bool, "Log subtraction")
		item.setValue(True) # default
		self.outputItem.addSubProperty(item)        
		self.addProperty(item, "Output_LogSubtraction")

		item = self.variantManager.addProperty(QVariant.Bool, "Energy integration")
		item.setValue(True) # default
		self.outputItem.addSubProperty(item)        
		self.addProperty(item, "Output_EnergyIntegration")

		
		self.variantEditor.addProperty(self.cropItem)	
		self.variantEditor.addProperty(self.projectionAveragingItem)
		self.variantEditor.addProperty(self.flatFieldingItem)
		self.variantEditor.addProperty(self.matrixManipulationItem)		
		self.variantEditor.addProperty(self.correctionItem)
		self.variantEditor.addProperty(self.outputItem)


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
		if (not self.idToProperty.contains(id)):
			return

		p = self.idToProperty[id]
		val = self.variantManager.value(p)

		# Return a string for the combo boxes:
		if (id == "ProjectionAveraging_Mode"):				
			val = kstPreprocessingPanel.projection_averaging_methods[val]

		return val


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


