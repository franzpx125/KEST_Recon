""" ImageViewer.py: PyQt image viewer widget for a QPixmap in a QGraphicsView scene with mouse zooming and panning.

"""

import numpy as np

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, Qt
from PyQt5.QtGui import QImage, QPixmap, QPainterPath, QWheelEvent
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QFrame


class _VoxImagePanel(QGraphicsView):
    """ PyQt image viewer widget

    Mouse interaction:
        Left mouse button (not default): zoom selection window
        Left mouse drag: pan image 
        Left mouse doubleclick: reset zoom
        Mouse Wheel: zoom in/out
        Right mouse button (not default): window selection for auto window / level
        Right mouse button drag: window/level
        Right mouse button doubleclick: reset window/level
    """

    # Mouse button signals emit image scene (x, y) coordinates.
    # !!!  For image (row, column) matrix indexing, row = y and column = x.
    leftMouseButtonPressed = pyqtSignal(float, float)
    rightMouseButtonPressed = pyqtSignal(float, float)
    leftMouseButtonReleased = pyqtSignal(float, float)
    rightMouseButtonReleased = pyqtSignal(float, float)
    leftMouseButtonDoubleClicked = pyqtSignal(float, float)
    rightMouseButtonDoubleClicked = pyqtSignal(float, float)
    mouseHoverEvent = pyqtSignal(int, int, float, 'QString')

    def __init__(self):
        QGraphicsView.__init__(self)

        # Remove frame and set background:
        self.setFrameStyle(QFrame.NoFrame)

        # QImage used to match the requirements of QGraphicsView:
        self.qImage = None 

        # Matrix of actual data in floating point format and as numpy array:
        self.npImage = None
        self.imageType = None

        # For window/level correction:
        self.winMin = None
        self.winMax = None
        # Starting mouse position for w/l settings:
        self.__WLDownPos = None

        # Zoom variables:
        self.zoomFactor = 1.0
        self.zoomSelectOn = True

        # Image is displayed as a QPixmap in a QGraphicsScene attached to this
        # QGraphicsView.
        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        # Store a local handle to the scene's current image pixmap.
        self._pixmapHandle = None

        # Image aspect ratio mode.
        self.aspectRatioMode = Qt.KeepAspectRatio

        # Track mouse movement (to get coords and value):
        self.setMouseTracking(True)       

        # Disable scroll bars (visible scroll bars give problems to the zoom):
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Stack of QRectF zoom boxes in scene coordinates:
        self.zoomStack = []

        # Left mouse button is False for pan - True for zoom:
        self.togglePanZoom = False 
        self.__rightMouseDown = True

    def hasImage(self):
        """ Returns whether or not the scene contains an image pixmap.
        """
        return self._pixmapHandle is not None

    def clearImage(self):
        """ Removes the current image pixmap from the scene if it exists.
        """
        if self.hasImage():
            self.scene.removeItem(self._pixmapHandle)
            self._pixmapHandle = None

    #def pixmap(self):
    #    """ Returns the scene's current image pixmap as a QPixmap, or else
    #    None if no image exists.
    #    :rtype: QPixmap | None
    #    """
    #    if self.hasImage():
    #        return self._pixmapHandle.pixmap()
    #    return None

    #def image(self):
    #    """ Returns the scene's current image pixmap as a QImage, or else None
    #    if no image exists.
    #    :rtype: QImage | None
    #    """
    #    if self.hasImage():
    #        return self._pixmapHandle.pixmap().toImage()
    #    return None

    def _updateImageLUT(self):
       
        # Create the image8 object casted to unsigned char:
        im8 = ((self.npImage.astype(np.float32) - self.winMin) / (self.winMax - self.winMin)) * 255.0
        im8[im8 > 255.0] = 255.0
        im8[im8 < 0.0] = 0.0
        im8 = im8.astype(np.uint8)

        self.qImage = QImage(im8, self.npImage.shape[1], self.npImage.shape[0], QImage.Format_Grayscale8)

        # Set the object to QPixmap:
        pixmap = QPixmap.fromImage(self.qImage)
        
        if self.hasImage():
            self._pixmapHandle.setPixmap(pixmap)
        else:
            self._pixmapHandle = self.scene.addPixmap(pixmap)
        self.setSceneRect(QRectF(pixmap.rect()))  # Set scene size to image size.        


    def setImage(self, npImage):
        """ Set the scene's current image pixmap to the input image as a numpy float 32 array.
        :type npImage: numpy array
        """

        # Set the new numpy image:
        self.npImage = npImage
        self.imageType = 'float' if (npImage.dtype == np.float32) else 'int'

        # Find min/max from input image as numpy array:
        self.winMin = np.amin(self.npImage.astype(np.float32))
        self.winMax = np.amax(self.npImage.astype(np.float32))
         
        # Update the UI with a resetted LUT:
        self._updateImageLUT()    
        self.updateViewer()   


    def updateViewer(self):
        """ Show current zoom (if showing entire image, apply current aspect ratio mode).
        """
        if not self.hasImage():
            return

        if len(self.zoomStack) and self.sceneRect().contains(self.zoomStack[-1]):
            # Show zoomed rect:
            self.fitInView(self.zoomStack[-1], self.aspectRatioMode)  
        else:
            # Clear the zoom stack (in case we got here because of an invalid
            # zoom):
            self.zoomStack = []  
            # Show entire image (use current aspect ratio mode):
            self.fitInView(self.sceneRect(), self.aspectRatioMode)  
   
               
    def performZoom(self, zoom_factor, event=None):

         # Set Anchors:
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)

        # Get the old position:
        if event is not None:
            oldPos = self.mapToScene(event.pos())
        else:
            oldPos = self.mapToScene(self.rect()).boundingRect().center()
        
        selectionBBox = self.sceneRect()
        
        self.zoomFactor = zoom_factor       
        
        selectionBBox.setWidth(selectionBBox.width() / zoom_factor)
        selectionBBox.setHeight(selectionBBox.height() / zoom_factor)
        
        if selectionBBox.isValid(): #and (selectionBBox != viewBBox):

            # Perform the zooming:
            self.zoomStack.append(selectionBBox)
            self.updateViewer()

            # Re-center the image:
            if event is not None:
                newPos = self.mapToScene(event.pos())
            else:
                newPos = self.mapToScene(self.rect()).boundingRect().center()
            delta = newPos - oldPos
            self.translate(delta.x(), delta.y())

            selectionBBox = self.mapToScene(self.rect()).boundingRect()
            if len(self.zoomStack):
                self.zoomStack.pop()
                self.zoomStack.append(selectionBBox)                

                # Set the correct zoom factor (which is not the input
                # parameter but it depends on the actual window size):
                widthRatio = self.sceneRect().width() / (selectionBBox.width() + 0.001)
                heightRatio = self.sceneRect().height() / (selectionBBox.height() + 0.001)
                self.zoomFactor = max(widthRatio,heightRatio)
              
                
                
    def resizeEvent(self, event):
        """ Current zoom is not maintained on resize.
        """       
        if self.npImage is not None:
            # Re-paint the scene:
            #self.performZoom(self.zoomFactor)
            self.updateViewer()

            # Set the correct new zoom factor (which is not the input
            # parameter but it depends on the actual window size):
            selectionBBox = self.mapToScene(self.rect()).boundingRect()
            widthRatio = self.sceneRect().width() / (selectionBBox.width() + 0.001)
            heightRatio = self.sceneRect().height() / (selectionBBox.height() + 0.001) 
            self.zoomFactor = max(widthRatio,heightRatio)

    def leaveEvent(self, event):
        """ Called when when the mouse goes out of the widget
        """
        # Emit a "out-of-border" signal. This is necessary when the image is 
        # zoomed and the mouse goes out of the widget:
        self.mouseHoverEvent.emit(-1, -1, -1, 'None')

    
    def mouseMoveEvent(self, event):
        """ Hover event to signal position and gray level.
        """
        if self.npImage is not None:
            
            # To fix a bug while pan:
            self.scene.update()
            
            # Get position in image space (watch what is x and what is y!):
            scenePos = self.mapToScene(event.pos())
            x = np.floor(scenePos.x()).astype(np.int32)
            y = np.floor(scenePos.y()).astype(np.int32)

            # Check boundaries:
            if ((x >= 0) and (x <= (self.npImage.shape[1] - 1)) and \
                (y >= 0) and (y <= (self.npImage.shape[0] - 1))):
        
                # Emit signal with coordinates and gray value:
                self.mouseHoverEvent.emit(x, y, self.npImage[y, x], self.imageType)
            else:
                # Emit a "out-of-border" signal:
                self.mouseHoverEvent.emit(-1, -1, -1, 'None')

            # This code is called also after a mouse wheel event:
            if not isinstance(event,QWheelEvent):
                QGraphicsView.mouseMoveEvent(self, event)

            if (self.__rightMouseDown) and (self.__WLDownPos is not None):
            
                # Apply window/level correction:
                winWidth = self.winMax - self.winMin
                winOffset = self.winMin + winWidth / 2

                # To be adapted:
                deltaX = (self.__WLDownPos.x() - event.pos().x()) * winWidth / 255.0
                deltaY = (self.__WLDownPos.y() - event.pos().y()) * winWidth / 255.0
               
                winOffset -= deltaY;
                winWidth -= deltaX;             
                                
                self.winMax = winOffset + winWidth / 2
                self.winMin = winOffset - winWidth / 2

                # Reset conditions:
                if (self.winMin >= self.winMax):
                    self.winMin = np.amin(self.npImage.astype(np.float32))
                if (self.winMax <= self.winMin):
                    self.winMax = np.amax(self.npImage.astype(np.float32))

                self._updateImageLUT()

                self.__WLDownPos = event.pos()


    def wheelEvent(self, event):
        """ Zoom in/out.
        """
        if self.npImage is not None:
            # Perform zoom in or zoom out according to wheel direction:
            if (event.angleDelta().y() > 0):
                self.performZoom(min(400, self.zoomFactor * 1.15), event)          
            else:
                self.performZoom(max(1.0, self.zoomFactor / 1.15), event)
        
            # We need to update mouse position as well:
            self.mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """ Start mouse pan or zoom mode.
        """
        if self.npImage is not None:        
            if event.button() == Qt.LeftButton:
                scenePos = self.mapToScene(event.pos())
                if self.togglePanZoom:
                    self.setDragMode(QGraphicsView.RubberBandDrag)
                else:
                    self.setDragMode(QGraphicsView.ScrollHandDrag)
                    #self.rightMouseButtonPressed.emit(scenePos.x(), scenePos.y())
                self.leftMouseButtonPressed.emit(scenePos.x(), scenePos.y())
            elif event.button() == Qt.RightButton:
                self.__rightMouseDown = True
                self.__WLDownPos = event.pos()
            
           
        QGraphicsView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """ Stop mouse pan or zoom mode (apply zoom if valid).
        """
        if self.npImage is not None:
            QGraphicsView.mouseReleaseEvent(self, event)
            scenePos = self.mapToScene(event.pos())
            if event.button() == Qt.LeftButton:
                self.setDragMode(QGraphicsView.NoDrag)
                if self.togglePanZoom:
                    viewBBox = self.zoomStack[-1] if len(self.zoomStack) else self.sceneRect()
                    selectionBBox = self.scene.selectionArea().boundingRect().intersected(viewBBox)                
                    self.scene.setSelectionArea(QPainterPath())  # Clear current selection area.
                    if selectionBBox.isValid() and (selectionBBox != viewBBox):
                        self.zoomStack.append(selectionBBox)
                        self.updateViewer()

                        viewBBox = self.mapToScene(self.rect()).boundingRect()

                        # Max or min?
                        widthRatio = self.sceneRect().width() / viewBBox.width() 
                        heightRatio = self.sceneRect().height() / viewBBox.height() 
                        self.zoomFactor = max(widthRatio,heightRatio,1.0)

                        if len(self.zoomStack):
                            self.zoomStack.pop()
                            self.zoomStack.append(viewBBox)

                else:                
                    self.leftMouseButtonReleased.emit(scenePos.x(), scenePos.y())
                    selectionBBox = self.mapToScene(self.rect()).boundingRect()
                    if len(self.zoomStack):
                        self.zoomStack.pop()
                        self.zoomStack.append(selectionBBox)

            elif event.button() == Qt.RightButton:
                self.__rightMouseDown = False
            
                  
            # Call re-paint to fix a bug when performing pan:
            self.scene.update()
            self.rightMouseButtonReleased.emit(scenePos.x(), scenePos.y())

    def mouseDoubleClickEvent(self, event):
        """ Show entire image.
        """
        if self.npImage is not None:
            scenePos = self.mapToScene(event.pos())
            if event.button() == Qt.LeftButton:
                # Reset zoom:            
                self.performZoom(1.0 / self.zoomFactor, event)   
                self.zoomStack = []  # Clear zoom stack.
                self.zoomFactor = 1.0
                #self.leftMouseButtonDoubleClicked.emit(scenePos.x(), scenePos.y())
        
            elif event.button() == Qt.RightButton:
                #if self.canZoom:
                #    self.zoomStack = []  # Clear zoom stack.
                #    self.updateViewer()
                #self.rightMouseButtonDoubleClicked.emit(scenePos.x(), scenePos.y())
            
                # Reset window/level:
                if self.npImage is not None:
                    self.winMin = np.amin(self.npImage.astype(np.float32))
                    self.winMax = np.amax(self.npImage.astype(np.float32))

                    self._updateImageLUT()
        
        QGraphicsView.mouseDoubleClickEvent(self, event)


