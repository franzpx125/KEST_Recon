from PyQt5.QtWidgets import QApplication, QLineEdit, QVBoxLayout
from PyQt5.QtCore import QVariant, QSize, pyqtSignal
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

from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QSizePolicy, QPushButton, QHBoxLayout

from QtProperty.pyqtcore import QList, QMap
from QtProperty.qtvariantproperty import QtVariantEditorFactory, QtVariantPropertyManager
from QtProperty.qttreepropertybrowser import QtTreePropertyBrowser
from QtProperty.qtgroupboxpropertybrowser import QtGroupBoxPropertyBrowser
from QtProperty.qtpropertymanager import (
    QtBoolPropertyManager, 
    QtIntPropertyManager, 
    QtStringPropertyManager, 
    QtSizePropertyManager, 
    QtRectPropertyManager, 
    QtSizePolicyPropertyManager, 
    QtEnumPropertyManager, 
    QtGroupPropertyManager
    )
from QtProperty.qteditorfactory import (
    QtCheckBoxFactory, 
    QtSpinBoxFactory, 
    QtSliderFactory, 
    QtScrollBarFactory, 
    QtLineEditFactory, 
    QtEnumEditorFactory
    )

class kstReconstructionPanel(QWidget):

    # Available flat-fielding algorithms:
	flatfielding_methods = ('conventional', 'dynamic')

	# Available reconstruction algorithms:
	reconstruction_methods = ('FDK', 'SIRT', 'CGLS')

    # Available reconstruction weighting methods:
	weighting_methods = ('cosine (full 360°)', 'Parker')

	# Event raised when the user wants to show dark, white, data as image:
	recostructionRequestedEvent = pyqtSignal()

	def __init__(self):

		QWidget.__init__(self)		

		# Property manager and related events:
		self.variantManager = QtVariantPropertyManager()
		self.propertyToId = QMap()
		self.idToProperty = QMap()
		self.variantManager.valueChangedSignal.connect(self.valueChanged)

		# Apply "button" (right aligned):
		btnWidget = QWidget()
		btnWidgetLayout = QHBoxLayout()
		btnWidgetSpacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum) 
		btnWidgetSpacer.setSizePolicy(spacerSizePolicy)

		self.button = QPushButton('Apply', self)
		self.button.clicked.connect(self.handleButton)

		btnWidgetLayout.addWidget(btnWidgetSpacer)  
		btnWidgetLayout.addWidget(self.button)    
		btnWidgetLayout.setContentsMargins(0,0,0,0)	
		btnWidget.setLayout(btnWidgetLayout)

		# Spacer:
		spacer = QWidget()
		spacerSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)   
		spacer.setSizePolicy(spacerSizePolicy)

		self.flatFieldingItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Flat fielding")
	

		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Method")
		enumNames = QList()
		for method in kstReconstructionPanel.flatfielding_methods:  
			enumNames.append(method)
		item.setAttribute("enumNames", enumNames)
		item.setValue(0) # default: "conventional"
		self.flatFieldingItem.addSubProperty(item)        
		self.addProperty(item, "FlatFielding_Method")
	
		# Configuration:
		self.methodItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Reconstruction Algorithm")
	

		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Algorithm")
		enumNames = QList()
		for method in kstReconstructionPanel.reconstruction_methods:  
			enumNames.append(method)
		item.setAttribute("enumNames", enumNames)
		item.setValue(0) # default: "FDK"
		self.methodItem.addSubProperty(item)        
		self.addProperty(item, "ReconstructionAlgorithm_Method")


		item = self.variantManager.addProperty(QVariant.Int, "Iterations")
		item.setValue(100) # default for SIRT
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 99999)
		item.setAttribute("singleStep", 1)
		item.setEnabled(False) # default
		self.methodItem.addSubProperty(item)
		self.addProperty(item, "ReconstructionAlgorithm_Iterations")

		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Weights")
		enumNames = QList()
		for method in kstReconstructionPanel.weighting_methods:  
			enumNames.append(method)
		item.setAttribute("enumNames", enumNames)
		item.setValue(0) # default: "cosine"
		item.setEnabled(True) # default
		self.methodItem.addSubProperty(item)        
		self.addProperty(item, "ReconstructionAlgorithm_Weights")


		self.anglesItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Angles / Projections")

		item = self.variantManager.addProperty(QVariant.Double, "Angles")
		item.setValue(360.0) # default
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 1)
		item.setAttribute("minimum", 0.1)
		item.setAttribute("maximum", 9999.9)
		self.anglesItem.addSubProperty(item)
		self.addProperty(item, "Reconstruction_Angles")


		item = self.variantManager.addProperty(QVariant.Int, "Actual projections")
		item.setValue(1000) # To be modified according to the open sample
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 99999)
		item.setAttribute("singleStep", 1)
		self.anglesItem.addSubProperty(item)
		self.addProperty(item, "Reconstruction_Projections")


		self.paddingItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Padding / Scaling")

		item = self.variantManager.addProperty(QVariant.Int, "Upsampling")
		item.setValue(1) # default
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 16)
		item.setAttribute("singleStep", 1)
		self.paddingItem.addSubProperty(item)
		self.addProperty(item, "ReconstructionAlgorithm_Upsampling")

		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Method")
		self.paddingTypes = QList()
		# method : string, 'constant' | ‘edge’ | ‘linear_ramp’ | ‘maximum’
		#    | ‘mean’ | ‘median’ | ‘minimum’ | ‘reflect’ | ‘symmetric’ | ‘wrap’
		self.paddingTypes.append("none")
		self.paddingTypes.append("edge")
		self.paddingTypes.append("constant")
		self.paddingTypes.append("reflect")
		self.paddingTypes.append("symmetric")
		self.paddingTypes.append("linear_ramp")
		self.paddingTypes.append("maximum")
		self.paddingTypes.append("mean")
		self.paddingTypes.append("median")
		self.paddingTypes.append("minimum")
		self.paddingTypes.append("wrap")
		item.setAttribute("enumNames", self.paddingTypes)
		item.setValue(0) # default: "edge"
		self.paddingItem.addSubProperty(item)
		self.addProperty(item, "ReconstructionAlgorithm_PaddingMethod")

		item = self.variantManager.addProperty(QVariant.Int, "Width")
		item.setValue(5) # default
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 1000)
		item.setAttribute("singleStep", 1)
		self.paddingItem.addSubProperty(item)
		self.addProperty(item, "ReconstructionAlgorithm_PaddingWidth")


		self.geometryItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Geometry")
	
		item = self.variantManager.addProperty(QVariant.Double, "Source-Sample [mm]")
		item.setValue(50) # default
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 1)
		item.setAttribute("minimum", 0.1)
		item.setAttribute("maximum", 9999.9)
		self.geometryItem.addSubProperty(item)
		self.addProperty(item, "Geometry_Source-Sample")
		

		item = self.variantManager.addProperty(QVariant.Double, "Source-Detector [mm]")
		item.setValue(55) # default
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 1)
		item.setAttribute("minimum", 0.1)
		item.setAttribute("maximum", 9999.9)
		self.geometryItem.addSubProperty(item)
		self.addProperty(item, "Geometry_Source-Detector")

		
		item = self.variantManager.addProperty(QVariant.Double, "Detector pixel size [mm]")
		item.setValue(0.062) # default
		item.setAttribute("singleStep", 0.010)
		item.setAttribute("decimals", 3)
		item.setAttribute("minimum", 0.001)
		item.setAttribute("maximum", 9.999)
		self.geometryItem.addSubProperty(item)
		self.addProperty(item, "Geometry_DetectorPixelSize")	


		self.offsetItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Detector Offsets")
	
		item = self.variantManager.addProperty(QVariant.Double, "Horizontal [pixel]")
		item.setValue(0.0) # default
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 1)
		item.setAttribute("minimum", -512.0)
		item.setAttribute("maximum", 512.0)
		self.offsetItem.addSubProperty(item)
		self.addProperty(item, "Offsets_Detector-u")
		

		item = self.variantManager.addProperty(QVariant.Double, "Vertical [pixel]")
		item.setValue(0.0) # default
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 1)
		item.setAttribute("minimum", -512.0)
		item.setAttribute("maximum", 512.0)
		self.offsetItem.addSubProperty(item)
		self.addProperty(item, "Offsets_Detector-v")

		self.variantFactory = QtVariantEditorFactory()

		# Un/comment the following two lines for a different look & feel
		#self.variantEditor = QtGroupBoxPropertyBrowser()
		self.variantEditor = QtTreePropertyBrowser()

		self.variantEditor.setFactoryForManager(self.variantManager, self.variantFactory)
		self.variantEditor.addProperty(self.flatFieldingItem)
		self.variantEditor.addProperty(self.methodItem)		
		self.variantEditor.addProperty(self.anglesItem)
		self.variantEditor.addProperty(self.geometryItem)
		self.variantEditor.addProperty(self.offsetItem)
		#self.variantEditor.addProperty(self.paddingItem)

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
		
        # Get the related property:
		id = self.propertyToId[property]

        # Enable/disable iterations property:
		if (id == "ReconstructionAlgorithm_Method"):

			# Get the iterations property:
			pIter = self.idToProperty["ReconstructionAlgorithm_Iterations"] 
			pWeig = self.idToProperty["ReconstructionAlgorithm_Weights"] 

			# Enable or disable it:
			if (value == 0): 
				pIter.setEnabled(False)
				pWeig.setEnabled(True)
			else:
				pIter.setEnabled(True)
				pWeig.setEnabled(False)


	def getValue(self, id):
		""" Get the value of the specified property.
		"""
		if (not self.idToProperty.contains(id)):
			return

        # Get the related property:
		p = self.idToProperty[id]
		val = self.variantManager.value(p)

		# Return a string for the combo boxes:
		if (id == "ReconstructionAlgorithm_Method"):				
			return kstReconstructionPanel.reconstruction_methods[val]
			
		elif (id == "ReconstructionAlgorithm_PaddingMethod"):				
			return self.paddingTypes[val]			

		# All the other cases:
		return val


	def setValue(self, id, val):
		""" Set the specified property with the specified value.
		"""
		if (self.idToProperty.contains(id)):

			p = self.idToProperty[id]
			self.variantManager.setValue(p, val)


	def handleButton(self):
		""" Raise an event when user wants to perform the refocusing.
		"""

		# Emit the event:
		self.recostructionRequestedEvent.emit()