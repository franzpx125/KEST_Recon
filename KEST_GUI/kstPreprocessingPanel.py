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

    # Available flat-fielding algorithms:
	flatfielding_methods = ('conventional', 'dynamic')

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
		self.btnPreview = QPushButton('Preview', self)
		self.btnPreview.clicked.connect(self.handleCalibrate)

        # Apply button (right aligned):
		self.btnApply = QPushButton('Apply', self)
		self.btnApply.clicked.connect(self.handleApply)

        # Compose the layout with the buttons and the spacer:
		btnWidgetLayout.addWidget(self.btnPreview)
		btnWidgetLayout.addWidget(btnWidgetSpacer)  
		btnWidgetLayout.addWidget(self.btnApply)    
		btnWidgetLayout.setContentsMargins(0,0,0,0)	
		btnWidget.setLayout(btnWidgetLayout)

		# Extra vertical spacer to have all the properties top-aligned:
		spacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)   
		spacer.setSizePolicy(spacerSizePolicy)


	
        # Configuration of the properties manager:
		self.defectCorrectionItem = self.variantManager.addProperty(\
            QtVariantPropertyManager.groupTypeId(), "Defect correction")
	
		item = self.variantManager.addProperty(QVariant.Int, "Dark threshold")
		item.setValue(0) # default for dead pixels
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 65535)
		item.setAttribute("singleStep", 1)
		self.defectCorrectionItem.addSubProperty(item)        
		self.addProperty(item, "DefectCorrection_DarkPixels")

		item = self.variantManager.addProperty(QVariant.Int, "Hot threshold")
		item.setValue(65535) # default for hot pixels
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 65535)
		item.setAttribute("singleStep", 1)
		self.defectCorrectionItem.addSubProperty(item)        
		self.addProperty(item, "DefectCorrection_HotPixels")



        # Configuration of the properties manager:
		self.matrixManipulationItem = self.variantManager.addProperty(\
            QtVariantPropertyManager.groupTypeId(), "Matrix manipulation")

		item = self.variantManager.addProperty(QVariant.Bool, "Rebinning 2x2")
		item.setValue(False) # default
		self.matrixManipulationItem.addSubProperty(item)        
		self.addProperty(item, "MatrixManipulation_Rebinning2x2")

		self.flatFieldingItem = self.variantManager.addProperty(\
		QtVariantPropertyManager.groupTypeId(), "Flat Fielding")
	
		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Method")
		enumNames = QList()
		for method in kstPreprocessingPanel.flatfielding_methods:  
			enumNames.append(method)
		item.setAttribute("enumNames", enumNames)
		item.setValue(0) # default: "conventional"
		self.flatFieldingItem.addSubProperty(item)        
		self.addProperty(item, "FlatFielding_Method")

		item = self.variantManager.addProperty(QVariant.Bool, "Log transform")
		item.setValue(True) # default
		self.flatFieldingItem.addSubProperty(item)        
		self.addProperty(item, "FlatFielding_LogTransform")

			
		self.variantEditor.addProperty(self.defectCorrectionItem)
		self.variantEditor.addProperty(self.matrixManipulationItem)
		self.variantEditor.addProperty(self.flatFieldingItem)


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

