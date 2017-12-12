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

class VoxRefocusingPanel(QWidget):

	# Available refocusing algorithms:
	available_methods = ('integration', 'Fourier', 'backprojection', 'iterative')

	# Event raised when the user wants to show dark, white, data as image:
	refocusingRequestedEvent = pyqtSignal()

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
	
		# Configuration:
		self.methodItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Method")
	

		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Method")
		enumNames = QList()
		enumNames.append(VoxRefocusingPanel.available_methods[0])
		enumNames.append(VoxRefocusingPanel.available_methods[1])
		enumNames.append(VoxRefocusingPanel.available_methods[2])
		enumNames.append(VoxRefocusingPanel.available_methods[3])
		item.setAttribute("enumNames", enumNames)
		item.setValue(2) # default: "backprojection"
		self.methodItem.addSubProperty(item)        
		self.addProperty(item, "RefocusingAlgorithm_Method")


		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(), "Beam Geometry")
		item.setValue(0) # default (for all the methods)
		self.geometryTypes = QList()
		self.geometryTypes.append("parallel")
		self.geometryTypes.append("cone")
		item.setAttribute("enumNames", self.geometryTypes)		
		self.methodItem.addSubProperty(item)
		self.addProperty(item, "RefocusingAlgorithm_BeamGeometry")


		item = self.variantManager.addProperty(QVariant.Int, "Iterations")
		item.setValue(10) # default for SIRT
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 1000)
		item.setAttribute("singleStep", 1)
		item.setEnabled(False) # default
		self.methodItem.addSubProperty(item)
		self.addProperty(item, "RefocusingAlgorithm_Iterations")


		self.paddingItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Padding / Scaling")

		item = self.variantManager.addProperty(QVariant.Int, "Upsampling")
		item.setValue(1) # default
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 16)
		item.setAttribute("singleStep", 1)
		self.paddingItem.addSubProperty(item)
		self.addProperty(item, "RefocusingAlgorithm_Upsampling")

		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Method")
		self.paddingTypes = QList()
		# method : string, 'constant' | ‘edge’ | ‘linear_ramp’ | ‘maximum’
		#    | ‘mean’ | ‘median’ | ‘minimum’ | ‘reflect’ | ‘symmetric’ | ‘wrap’
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
		self.addProperty(item, "RefocusingAlgorithm_PaddingMethod")

		item = self.variantManager.addProperty(QVariant.Int, "Width")
		item.setValue(5) # default
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 1000)
		item.setAttribute("singleStep", 1)
		self.paddingItem.addSubProperty(item)
		self.addProperty(item, "RefocusingAlgorithm_PaddingWidth")


		self.distancesItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Refocusing distances")
	
		item = self.variantManager.addProperty(QVariant.Double, "Minimum")
		item.setValue(0.9) # default
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		item.setAttribute("minimum", 0.1)
		item.setAttribute("maximum", 1.9)
		self.distancesItem.addSubProperty(item)
		self.addProperty(item, "RefocusingDistance_Minimum")
		

		item = self.variantManager.addProperty(QVariant.Double, "Maximum")
		item.setValue(1.1) # default
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		item.setAttribute("minimum", 0.1)
		item.setAttribute("maximum", 1.9)
		self.distancesItem.addSubProperty(item)
		self.addProperty(item, "RefocusingDistance_Maximum")

		
		item = self.variantManager.addProperty(QVariant.Double, "Step")
		item.setValue(0.005) # default
		item.setAttribute("singleStep", 0.010)
		item.setAttribute("decimals", 3)
		item.setAttribute("minimum", 0.001)
		item.setAttribute("maximum", 0.100)
		self.distancesItem.addSubProperty(item)
		self.addProperty(item, "RefocusingDistance_Step")	

		self.variantFactory = QtVariantEditorFactory()

		# Un/comment the following two lines for a different look & feel
		#self.variantEditor = QtGroupBoxPropertyBrowser()
		self.variantEditor = QtTreePropertyBrowser()

		self.variantEditor.setFactoryForManager(self.variantManager, self.variantFactory)
		self.variantEditor.addProperty(self.methodItem)
		self.variantEditor.addProperty(self.distancesItem)
		self.variantEditor.addProperty(self.paddingItem)

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
		if (id == "RefocusingAlgorithm_Method"):

			# Get the iterations property:
			p = self.idToProperty["RefocusingAlgorithm_Iterations"] 

            # Enable or disable it:
			if (value == 0) or (value == 1) or (value == 2): 
				p.setEnabled(False)
			else:
				p.setEnabled(True)



	def getValue(self, id):
		""" Get the value of the specified property.
		"""
		if (not self.idToProperty.contains(id)):
			return

        # Get the related property:
		p = self.idToProperty[id]
		val = self.variantManager.value(p)

		# Return a string for the combo boxes:
		if (id == "RefocusingAlgorithm_Method"):				
			return VoxRefocusingPanel.available_methods[val]
			
		elif (id == "RefocusingAlgorithm_PaddingMethod"):				
			return self.paddingTypes[val]
			
		elif (id == "RefocusingAlgorithm_BeamGeometry"):			
			return self.geometryTypes[val]

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
		self.refocusingRequestedEvent.emit()