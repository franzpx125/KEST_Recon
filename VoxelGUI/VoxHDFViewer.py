import os.path 
import h5py

from PyQt5.QtWidgets import QWidget,  QAction, QVBoxLayout, QToolBar, QSizePolicy
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QGroupBox, QSplitter, QMenu
from PyQt5.QtWidgets import QApplication, QTreeWidgetItemIterator, QFrame, QLabel
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt, pyqtSignal

from VoxUtils import eprint

HDFVIEW_METADATA_LABEL = "Metadata"

class VoxHDFViewer(QWidget):
    
	# Event raised when the user wants to show dark, white, data as image:
	openImageDataEvent = pyqtSignal('QString', 'QString')

	def __init__(self):

		QWidget.__init__(self)

		self.HDF5File = None
						
		# Add a tree view control and a description panel (resizable):
		self.treeWidget = QTreeWidget()		
		self.root = QTreeWidgetItem() 
		self.showMetadata = QGroupBox()
		self.showMetadataLayout = QVBoxLayout()
		self.splitter = QSplitter(Qt.Vertical)

		# Configure the tree view:
		self.treeWidget.setHeaderHidden(True)
		self.treeWidget.setContextMenuPolicy(Qt.CustomContextMenu)
		self.treeWidget.itemSelectionChanged.connect(self.handleChanged)
		self.treeWidget.customContextMenuRequested.connect(self.prepareContextMenu)

		# Configure the splitter:
		self.splitter.addWidget(self.treeWidget)
		self.splitter.addWidget(self.showMetadata)

		# Configure the groupbox:
		self.showMetadata.setTitle(HDFVIEW_METADATA_LABEL)
		self.showMetadata.setMinimumHeight = 80
		self.showMetadata.setLayout(self.showMetadataLayout)

		# Compose layout of the whole widget:
		layout = QVBoxLayout()
		layout.addWidget(self.splitter)        
		layout.setContentsMargins(0,0,0,0)	
		self.setLayout(layout)


	def _initTreeElements(self, h5Item, treeItem):
		""" Recursive call: 
		"""		
		dir = os.path.dirname(os.path.realpath(__file__))

		# Create an element for the tree widget:
		elem = QTreeWidgetItem() 
		treeItem.addChild(elem)		      
		elem.setData(0, Qt.UserRole, h5Item.name)
		elem.setText(0, os.path.basename(h5Item.name))  

		try:
			# Set the right icon:
			if isinstance(h5Item, h5py.Dataset):								
				t = h5Item.dtype				
				if t.names is None:
					if t.name == 'object':
						elem.setIcon(0, QIcon(dir + "/resources/text.png"))	
					else:
						elem.setIcon(0, QIcon(dir + "/resources/dataset.png"))	
				else:
					elem.setIcon(0, QIcon(dir + "/resources/compound.png"))	

			elif isinstance(h5Item, h5py.ExternalLink):			  			
				elem.setIcon(0, QIcon(dir + "/resources/link.png"))			
		
			elif isinstance(h5Item, h5py.Group):			
				elem.setIcon(0, QIcon(dir + "/resources/folder.png"))
				
				# Recursive call only for a group:
				for key in h5Item.keys():				
					self._initTreeElements(h5Item[key], elem)
		
		except:
			elem.setIcon(0, QIcon(dir + "/resources/warning.png"))		


	def initTreeElements(self):
		"""Populate the tree view with the groups and datasets of the 
		   HDF5 file specified with setHDF5File(). A context menu is
           added for the image data.
		"""
		# Get application path:
		dir = os.path.dirname(os.path.realpath(__file__))

		try:
			# Remove all widgets from the metadata layout:
			for i in reversed(range(self.showMetadataLayout.count())): 
				widgetToRemove = self.showMetadataLayout.itemAt(i).widget()
				self.showMetadataLayout.removeWidget(widgetToRemove)
				widgetToRemove.setParent(None)
		
			# Remove first all items in the tree view (there's a bug in Qt):
			self.treeWidget.collapseAll()
			self.treeWidget.setCurrentItem(self.root)
			self.root.takeChildren()
			self.treeWidget.removeItemWidget(self.root,0)
			
			# Add root element as the name of the file:
			  
			self.treeWidget.addTopLevelItem(self.root)            
			self.root.setIcon(0, QIcon(dir + "/resources/home.png"))
			self.root.setData(0, Qt.UserRole, self.HDF5File.name)
			self.root.setText(0, os.path.basename(self.HDF5File.filename))	
			self.root.setExpanded(True)

			# Get all the groups:
			for key in self.HDF5File.keys():
				self._initTreeElements(self.HDF5File[key], self.root)

		except IOError as e:             
			 eprint("Unable to open file: " + self.HDF5File + ".")   



	def setHDF5File(self, filename):
		""" Set the HDF5 file to be explored with the tree view.
		"""
		try:

			self.HDF5File = h5py.File(filename, 'r')			
			self.initTreeElements()
		
		except IOError as e:         
				
			eprint("Unable to open file: " + filename + ".")   
			raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filename)

	def prepareContextMenu(self, position):
		""" Open a context menu for the image data.
		"""
        # Get the selected item (only one, no multiple selection allowed):
		curr = self.treeWidget.selectedItems()[0]

		# Get the corresponding name in the HDF5 file:
		h5Item = self.HDF5File[str(curr.data(0, Qt.UserRole))]
		key = str(h5Item.name)

		# Create the menu:		
		menu = QMenu()
		if ((key == "/data/dark") or (key == "/data/white") or (key == "/data/image")):
			openAction = QAction("Open image in new tab", self)
			openAction.triggered.connect(self.openImage)
			menu.addAction(openAction)			
		
		# Show the menu:
		menu.exec_(self.treeWidget.viewport().mapToGlobal(position))

	def openImage(self):

		 # Get the selected item (only one, no multiple selection allowed):
		curr = self.treeWidget.selectedItems()[0]

		# Get the corresponding name in the HDF5 file:
		h5Item = self.HDF5File[str(curr.data(0, Qt.UserRole))]
		key = str(h5Item.name)

        # Emit the event:
		self.openImageDataEvent.emit(self.HDF5File.filename, key)

	def handleChanged(self):
		""" Populate panel with the HDF5 content (data and attributes) when the 
			selection in the tree view is modified.
		"""
		# Get the selected item (only one, no multiple selection allowed):
		curr = self.treeWidget.selectedItems()[0]

		try:
			# Set mouse wait cursor:
			QApplication.setOverrideCursor(Qt.WaitCursor)

			# Remove all widgets from the metadata layout:
			for i in reversed(range(self.showMetadataLayout.count())): 
				widgetToRemove = self.showMetadataLayout.itemAt(i).widget()
				self.showMetadataLayout.removeWidget(widgetToRemove)
				widgetToRemove.setParent(None)
			
			# Add a label for the data:
			dataLabel = QLabel()
			h5Item = self.HDF5File[str(curr.data(0, Qt.UserRole))]
			key = str(os.path.basename(h5Item.name))

			# If not root element:
			if key is not "":

				# If scalar value:
				if isinstance(h5Item, h5py.Dataset):								
					t = h5Item.dtype				
					if t.names is None:
						if t.name == 'object':
							# Scalar value:
							text = key + " = " + str(h5Item.value)
						else:
							# Dataset:
							if len(h5Item.value.shape) == 0:
								text = key + " = " + str(h5Item.value) + " (" + t.name + ")"
							elif (len(h5Item.value.shape) == 1) and (h5Item.value.shape[0] == 1):
								text = key + " = " + str(h5Item.value[0]) #+ " (" + t.name + ")"
							elif (h5Item.value.shape == (2,) ):
								text = key + " = [" + str(h5Item.value[0]) + ", " \
											+ str(h5Item.value[1]) + "]" #+ " (" + t.name + ")"
							elif (h5Item.value.shape == (3,) ):
								text = key + " = [" + str(h5Item.value[0]) + ", " \
											+ str(h5Item.value[1]) + ", "  \
											+ str(h5Item.value[2]) + "]" #+ " (" + t.name + ")"
							elif (len(h5Item.value.shape) == 2):
								if (h5Item.value.shape[0] == 1):
									if (h5Item.value.shape[1] == 1):
										text = key + " = " + str(h5Item.value[0,0]) #+ " (" + t.name + ")"
									elif (h5Item.value.shape[1] == 2):
										text = key + " = [" + str(h5Item.value[0,0]) + ", " \
											+ str(h5Item.value[0,1]) + "]" #+ " (" + t.name + ")"
									elif (h5Item.value.shape[1] == 3):
										text = key + " = [" + str(h5Item.value[0,0]) + ", " \
											+ str(h5Item.value[0,1]) + ", "  \
											+ str(h5Item.value[0,2]) + "]" #+ " (" + t.name + ")"
									else:
										text = key + " = Dataset of size " + str(h5Item.shape) + " (" + t.name + ")"
								else:
									if (h5Item.value.shape[0] == 1):
										text = key + " = " + str(h5Item.value[0,0]) #+ " (" + t.name + ")"
									elif (h5Item.value.shape[0] == 2):
										text = key + " = [" + str(h5Item.value[0,0]) + ", " \
											+ str(h5Item.value[1,0]) + "]" #+ " (" + t.name + ")"
									elif (h5Item.value.shape[0] == 3):
										text = key + " = [" + str(h5Item.value[0,0]) + ", " \
											+ str(h5Item.value[1,0]) + ", "  \
											+ str(h5Item.value[2,0]) + "]" #+ " (" + t.name + ")"
									else:
										text = key + " = Dataset of size " + str(h5Item.shape) + " (" + t.name + ")"
							else:
								text = key + " = Dataset of size " + str(h5Item.shape) + " (" + t.name + ")"
					else:
						# Compound:
						text = key + " = Compound of size " + str(h5Item.shape) + " (" + t.name + ")"

				elif isinstance(h5Item, h5py.ExternalLink):			  			
					# Show the link:
					text = key + " = " + str(h5Item.value)
		
				elif isinstance(h5Item, h5py.Group):			
					# Show the number of sub-items:
					text = key + " = Group with " + str(len(list(h5Item.keys()))) + " sub-element(s)"

				# Compose the string taking care of excessive length:
				metrics = QFontMetrics(dataLabel.font())
				elidedText = metrics.elidedText(text, Qt.ElideRight, dataLabel.width())
				
				dataLabel.setText(elidedText)
				self.showMetadataLayout.addWidget(dataLabel)
				
			try:	

				# Add as many labels as attributes found:
				if len(h5Item.attrs) > 0:
					headerLabel = QLabel()
					headerLabel.setText("Attributes:")
					self.showMetadataLayout.addWidget(headerLabel)

					labelsList = []
					for attr in h5Item.attrs.keys():					
						attrLabel = QLabel()
						#attrLabel.setText("    " + str(attr) + " = " + str(h5Item.attrs[attr].decode('utf-8')))
						attrLabel.setText("    " + str(attr) + " = " + str(h5Item.attrs[attr]))
						labelsList.append(attrLabel)
						self.showMetadataLayout.addWidget(attrLabel)

			except:
				eprint("Error while reading attributes from " + self.HDF5File.filename + ".")   
				
			# Add a foo spacer for a vertical top alignment:
			spacer = QWidget()
			spacerSizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)   
			spacer.setSizePolicy(spacerSizePolicy)
			self.showMetadataLayout.addWidget(spacer)			

		except:
				
			eprint("Error while reading element from " + self.HDF5File.filename + ".")   

		finally:
			# Restore mouse cursor:
			QApplication.restoreOverrideCursor()

