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

from QtProperty.qtvariantproperty import QtVariantEditorFactory, QtVariantPropertyManager
from QtProperty.qttreepropertybrowser import QtTreePropertyBrowser
from QtProperty.qtgroupboxpropertybrowser import QtGroupBoxPropertyBrowser

class VoxPreprocessingPanel(QWidget):

    # Event raised when the user wants to show dark, white, data as image:
	preprocessingRequestedEvent = pyqtSignal()

	def __init__(self):

		QWidget.__init__(self)		

        # Property manager:
		self.variantManager = QtVariantPropertyManager()

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
		self.inputLensletItem = self.variantManager.addProperty(\
            QtVariantPropertyManager.groupTypeId(), "Input lenslet")
	
		item = self.variantManager.addProperty(QVariant.Double, "Width")
		item.setValue(1.2345)
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		self.inputLensletItem.addSubProperty(item)

		item = self.variantManager.addProperty(QVariant.Double, "Height")
		item.setValue(1.2345)
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		self.inputLensletItem.addSubProperty(item)

		item = self.variantManager.addProperty(QVariant.Double, "Offset Top")
		item.setValue(1.2345)
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		self.inputLensletItem.addSubProperty(item)

		
		item = self.variantManager.addProperty(QVariant.Double, "Offset Left")
		item.setValue(1.2345)
		item.setAttribute("singleStep", 0.1)
		item.setAttribute("decimals", 3)
		self.inputLensletItem.addSubProperty(item)

		self.outputLensletItem = self.variantManager.addProperty(\
			QtVariantPropertyManager.groupTypeId(), "Output lenslet")
	
		item = self.variantManager.addProperty(QVariant.Int, "Width")
		item.setValue(16)
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 1024)
		item.setAttribute("singleStep", 1)
		self.outputLensletItem.addSubProperty(item)

		item = self.variantManager.addProperty(QVariant.Int, "Height")
		item.setValue(16)
		item.setAttribute("minimum", 0)
		item.setAttribute("maximum", 1024)
		item.setAttribute("singleStep", 1)
		self.outputLensletItem.addSubProperty(item)

		#item = self.variantManager.addProperty(QVariant.Size, "Output Lenslet")
		#item.setValue(QSize(20, 20))
		#item.setAttribute("minimum", QSize(10, 10))
		#item.setAttribute("maximum", QSize(30, 30))
		#self.outputLensletItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Bool, " Bool Property")
		#item.setValue(True)
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Int, " Int Property")
		#item.setValue(20)
		#item.setAttribute("minimum", 0)
		#item.setAttribute("maximum", 100)
		#item.setAttribute("singleStep", 10)
		#topItem.addSubProperty(item)

		#i = 0
		#item = variantManager.addProperty(QVariant.Int, str(i) + " Int Property
		#(ReadOnly)")
		#i += 1
		#item.setValue(20)
		#item.setAttribute("minimum", 0)
		#item.setAttribute("maximum", 100)
		#item.setAttribute("singleStep", 10)
		#item.setAttribute("readOnly", True)
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Double, str(i) + " Double
		#Property")
		#i += 1
		#item.setValue(1.2345)
		#item.setAttribute("singleStep", 0.1)
		#item.setAttribute("decimals", 3)
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Double, str(i) + " Double
		#Property (ReadOnly)")
		#i += 1
		#item.setValue(1.23456)
		#item.setAttribute("singleStep", 0.1)
		#item.setAttribute("decimals", 5)
		#item.setAttribute("readOnly", True)
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.String, str(i) + " String
		#Property")
		#i += 1
		#item.setValue("Value")
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.String, str(i) + " String
		#Property (Password)")
		#i += 1
		#item.setAttribute("echoMode", QLineEdit.Password)
		#item.setValue("Password")
		#topItem.addSubProperty(item)

		## Readonly String Property
		#item = variantManager.addProperty(QVariant.String, str(i) + " String
		#Property (ReadOnly)")
		#i += 1
		#item.setAttribute("readOnly", True)
		#item.setValue("readonly text")
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Date, str(i) + " Date Property")
		#i += 1
		#item.setValue(QDate.currentDate().addDays(2))
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Time, str(i) + " Time Property")
		#i += 1
		#item.setValue(QTime.currentTime())
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.DateTime, str(i) + " DateTime
		#Property")
		#i += 1
		#item.setValue(QDateTime.currentDateTime())
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.KeySequence, str(i) + "
		#KeySequence Property")
		#i += 1
		#item.setValue(QKeySequence(Qt.ControlModifier | Qt.Key_Q))
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Char, str(i) + " Char Property")
		#i += 1
		#item.setValue(chr(386))
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Locale, str(i) + " Locale
		#Property")
		#i += 1
		#item.setValue(QLocale(QLocale.Polish, QLocale.Poland))
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Point, str(i) + " PoProperty")
		#i += 1
		#item.setValue(QPoint(10, 10))
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.PointF, str(i) + " PointF
		#Property")
		#i += 1
		#item.setValue(QPointF(1.2345, -1.23451))
		#item.setAttribute("decimals", 3)
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Size, str(i) + " Size Property")
		#i += 1
		#item.setValue(QSize(20, 20))
		#item.setAttribute("minimum", QSize(10, 10))
		#item.setAttribute("maximum", QSize(30, 30))
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.SizeF, str(i) + " SizeF
		#Property")
		#i += 1
		#item.setValue(QSizeF(1.2345, 1.2345))
		#item.setAttribute("decimals", 3)
		#item.setAttribute("minimum", QSizeF(0.12, 0.34))
		#item.setAttribute("maximum", QSizeF(20.56, 20.78))
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Rect, str(i) + " Rect Property")
		#i += 1
		#item.setValue(QRect(10, 10, 20, 20))
		#topItem.addSubProperty(item)
		#item.setAttribute("constraint", QRect(0, 0, 50, 50))

		#item = variantManager.addProperty(QVariant.RectF, str(i) + " RectF
		#Property")
		#i += 1
		#item.setValue(QRectF(1.2345, 1.2345, 1.2345, 1.2345))
		#topItem.addSubProperty(item)
		#item.setAttribute("constraint", QRectF(0, 0, 50, 50))
		#item.setAttribute("decimals", 3)

		#item = variantManager.addProperty(QtVariantPropertyManager.enumTypeId(),
		#str(i) + " Enum Property")
		#i += 1
		#enumNames = QList()
		#enumNames.append("Enum0")
		#enumNames.append("Enum1")
		#enumNames.append("Enum2")
		#item.setAttribute("enumNames", enumNames)
		#item.setValue(1)
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QtVariantPropertyManager.flagTypeId(),
		#str(i) + " Flag Property")
		#i += 1
		#flagNames = QList()
		#flagNames.append("Flag0")
		#flagNames.append("Flag1")
		#flagNames.append("Flag2")
		#item.setAttribute("flagNames", flagNames)
		#item.setValue(5)
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.SizePolicy, str(i) + " SizePolicy
		#Property")
		#i += 1
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Font, str(i) + " Font Property")
		#i += 1
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Cursor, str(i) + " Cursor
		#Property")
		#i += 1
		#topItem.addSubProperty(item)

		#item = variantManager.addProperty(QVariant.Color, str(i) + " Color
		#Property")
		#i += 1
		#topItem.addSubProperty(item)

		self.variantFactory = QtVariantEditorFactory()

		#self.variantEditor = QtGroupBoxPropertyBrowser()
		self.variantEditor = QtTreePropertyBrowser()
		self.variantEditor.setFactoryForManager(self.variantManager, self.variantFactory)
		self.variantEditor.addProperty(self.inputLensletItem)
		self.variantEditor.addProperty(self.outputLensletItem)
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
		self.preprocessingRequestedEvent.emit()

