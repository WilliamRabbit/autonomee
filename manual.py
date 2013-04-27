"""
    manual.py - The view shown when controlling the car manually.
"""

from PySide.QtGui import *
from PySide.QtCore import *

import engine


class ManualView(QGraphicsView):

    def __init__(self, car, parent=None):
        super(ManualView, self).__init__(parent)

        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        scene = ManualScene(car=car, parent=self)
        self.setScene(scene)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)


    def showEvent(self, event):
        super(ManualView, self).showEvent(event)

    def paintEvent(self, event):
        super(ManualView, self).paintEvent(event)

class ManualScene(QGraphicsScene):
    def __init__(self, car, parent=None):
        super(ManualScene, self).__init__(parent)

        # Gradient background
        self.gradient = QLinearGradient(0, -200, 0, 600)
        lightGray = 0.1
        darkGray = 0.03
        self.gradient.setColorAt(0, QColor.fromRgbF(darkGray, darkGray, darkGray, 1))
        self.gradient.setColorAt(1, QColor.fromRgbF(lightGray, lightGray, lightGray, 1))
        self.setBackgroundBrush(self.gradient)

        # Rect
        self.rectItem = QGraphicsRectItem(0, 0, 700, 500)
        self.rectItem.setPen( QColor.fromRgbF(0., 0., 0., 0.) )
        self.rectItem.setFlags(QGraphicsItem.ItemClipsToShape)
        self.rectItem.setZValue(0)
        self.addItem(self.rectItem)


        # Compass
        self.car = car
        self.graphicCar = engine.GraphicsStaticCarItem( self.car )
        self.graphicCar.setCaption("")
        self.graphicCar.setPos(self.width()/2 , self.height()/2 + 100)
        self.addItem(self.graphicCar)


        #Text
        self.titleItem = QGraphicsTextItem("Manual mode")
        self.titleItem.setFont(QFont("Ubuntu-L.ttf", 35, QFont.Light))
        # 'Dirty' centering of the text
        self.titleItem.setPos(self.width()/2 - self.titleItem.boundingRect().width()/2, 5)
        self.titleItem.setDefaultTextColor(QColor(210, 220, 250))
        self.addItem(self.titleItem)



    def mousePressEvent(self, event):
        x, y = event.scenePos().x(), event.scenePos().y()

        super(ManualScene,self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        x, y = event.scenePos().x(), event.scenePos().y()
        super(ManualScene,self).mouseMoveEvent(event)