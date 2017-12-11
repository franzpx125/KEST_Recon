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

		# Property manager:
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
	
		self.__refocusingAlgorithm_Method = 2 # "integration"
		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Method")
		enumNames = QList()
		enumNames.append(VoxRefocusingPanel.available_methods[0])
		enumNames.append(VoxRefocusingPanel.available_methods[1])
		enumNames.append(VoxRefocusingPanel.available_methods[2])
		enumNames.append(VoxRefocusingPanel.available_methods[3])
		item.setAttribute("enumNames", enumNames)
		item.setValue(self.__refocusingAlgorithm_Method)
		self.methodItem.addSubProperty(item)        
		self.addProperty(item, "RefocusingAlgorithm_Method")

		self.__refocusingAlgorithm_BeamGeometry = 0 # default (for all the methods)
		self.itemBeamGeometry = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(), "Beam Geometry")
		self.itemBeamGeometry.setValue(self.__refocusingAlgorithm_BeamGeometry)
		enumNames = QList()
		enumNames.append("parallel")
		enumNames.append("cone")
		self.itemBeamGeometry.setAttribute("enumNames", enumNames)		
		self.methodItem.addSubProperty(self.itemBeamGeometry)
		self.addProperty(self.itemBeamGeometry, "RefocusingAlgorithm_BeamGeometry")

		self.__refocusingAlgorithm_Iterations = 10 # default for SIRT
		self.itemIterations = self.variantManager.addProperty(QVariant.Int, "Iterations")
		self.itemIterations.setValue(self.__refocusingAlgorithm_Iterations)
		self.itemIterations.setAttribute("minimum", 1)
		self.itemIterations.setAttribute("maximum", 1000)
		self.itemIterations.setAttribute("singleStep", 1)
		self.itemIterations.setEnabled(False) # default
		self.methodItem.addSubProperty(self.itemIterations)
		self.addProperty(self.itemIterations, "RefocusingAlgorithm_Iterations")


		self.paddingItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Padding / Scaling")

		self.__refocusingAlgorithm_Upsampling = 1 # default
		item = self.variantManager.addProperty(QVariant.Int, "Upsampling")
		item.setValue(self.__refocusingAlgorithm_Upsampling)
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 16)
		item.setAttribute("singleStep", 1)
		self.paddingItem.addSubProperty(item)
		self.addProperty(item, "RefocusingAlgorithm_Upsampling")

		self.__refocusingAlgorithm_PaddingMethod = 'edge' # default
		item = self.variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),"Method")
		enumNames = QList()
		# method : string, 'constant' | ‘edge’ | ‘linear_ramp’ | ‘maximum’
		#    | ‘mean’ | ‘median’ | ‘minimum’ | ‘reflect’ | ‘symmetric’ | ‘wrap’
		enumNames.append("edge")
		enumNames.append("constant")
		enumNames.append("reflect")
		enumNames.append("symmetric")
		enumNames.append("linear_ramp")
		enumNames.append("maximum")
		enumNames.append("mean")
		enumNames.append("median")
		enumNames.append("minimum")
		enumNames.append("wrap")
		item.setAttribute("enumNames", enumNames)
		item.setValue(0)
		self.paddingItem.addSubProperty(item)
		self.addProperty(item, "RefocusingAlgorithm_PaddingMethod")

		self.__refocusingAlgorithm_PaddingWidth = 5 # default
		item = self.variantManager.addProperty(QVariant.Int, "Width")
		item.setValue(self.__refocusingAlgorithm_PaddingWidth)
		item.setAttribute("minimum", 1)
		item.setAttribute("maximum", 1000)
		item.setAttribute("singleStep", 1)
		self.paddingItem.addSubProperty(item)
		self.addProperty(item, "RefocusingAlgorithm_PaddingWidth")


		self.distancesItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Refocusing distances")
	
		self.__refocusingDistance_Minimum = 0.9 # default
		item = self.variantManager.addProperty(QVariant.Double, "Minimum")
		item.setValue(self.__refocusingDistance_Minimum)
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		item.setAttribute("minimum", 0.1)
		item.setAttribute("maximum", 1.9)
		self.distancesItem.addSubProperty(item)
		self.addProperty(item, "RefocusingDistance_Minimum")
		

		self.__refocusingDistance_Maximum = 1.1 # default
		item = self.variantManager.addProperty(QVariant.Double, "Maximum")
		item.setValue(self.__refocusingDistance_Maximum)
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		item.setAttribute("minimum", 0.1)
		item.setAttribute("maximum", 1.9)
		self.distancesItem.addSubProperty(item)
		self.addProperty(item, "RefocusingDistance_Maximum")

		
		self.__refocusingDistance_Step = 0.005 # default
		item = self.variantManager.addProperty(QVariant.Double, "Step")
		item.setValue(self.__refocusingDistance_Step)
		item.setAttribute("singleStep", 0.010)
		item.setAttribute("decimals", 3)
		item.setAttribute("minimum", 0.001)
		item.setAttribute("maximum", 0.100)
		self.distancesItem.addSubProperty(item)
		self.addProperty(item, "RefocusingDistance_Step")	

		self.variantFactory = QtVariantEditorFactory()

		# Comment/uncomment the following two lines for a different look &
		# feel:
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

	def handleButton(self):
		"""
		"""

		# Emit the event:
		self.refocusingRequestedEvent.emit()

	def addProperty(self, property, id):
		self.propertyToId[property] = id
		self.idToProperty[id] = property

		#item = self.propertyEditor.addProperty(property)
		#if (self.idToExpanded.contains(id)):
		#	self.propertyEditor.setExpanded(item, self.idToExpanded[id])

	def valueChanged(self, property, value):
		""" Updates the property when a value is changed in the UI.
		"""
		if (not self.propertyToId.contains(property)):
			return

		id = self.propertyToId[property]

		if (id == "RefocusingDistance_Minimum"):
			self.__refocusingDistance_Minimum = value
		elif (id == "RefocusingDistance_Maximum"):
			self.__refocusingDistance_Maximum = value
		elif (id == "RefocusingDistance_Step"):
			self.__refocusingDistance_Step = value				

		elif (id == "RefocusingAlgorithm_Upsampling"):
			self.__refocusingAlgorithm_Upsampling = value
		elif (id == "RefocusingAlgorithm_PaddingMethod"):
			self.__refocusingAlgorithm_PaddingMethod = value
		elif (id == "RefocusingAlgorithm_PaddingWidth"):
			self.__refocusingAlgorithm_PaddingWidth = value

		elif (id == "RefocusingAlgorithm_Method"):
			self.__refocusingAlgorithm_Method = value

            # Enable/disable iterations property:
			if (value == 0) or (value == 1) or (value == 2): 
				self.itemIterations.setEnabled(False)
			else:
				self.itemIterations.setEnabled(True)

		elif (id == "RefocusingAlgorithm_Iterations"):
			self.__refocusingAlgorithm_Iterations = value

		elif (id == "RefocusingAlgorithm_BeamGeometry"):
			self.__refocusingAlgorithm_BeamGeometry = value


	def getRefocusingAlgorithm_Method(self):

		return self.__refocusingAlgorithm_Method

	def getRefocusingAlgorithm_Iterations(self):

		return self.__refocusingAlgorithm_Iterations

	def getRefocusingAlgorithm_BeamGeometry(self):

		return self.__refocusingAlgorithm_BeamGeometry


	def getRefocusingAlgorithm_Upsampling(self):

		return self.__refocusingAlgorithm_Upsampling

	def getRefocusingAlgorithm_PaddingMethod(self):

		return self.__refocusingAlgorithm_PaddingMethod

	def getRefocusingAlgorithm_PaddingWidth(self):

		return self.__refocusingAlgorithm_PaddingWidth


	def getRefocusingDistance_Minimum(self):

		return self.__refocusingDistance_Minimum

	def getRefocusingDistance_Maximum(self):

		return self.__refocusingDistance_Maximum

	def getRefocusingDistance_Step(self):

		return self.__refocusingDistance_Step