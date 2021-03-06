# -*- coding: utf8 -*-

"""
    widgets.py - Many custom graphic items (Qt) used -mainly- to visualize the car
"""
from PySide.QtCore import *
from PySide.QtGui import *

from math import sin, cos, pi, degrees, radians
from engine import Car
from probability import ParticleFilter

class Waypoint(QGraphicsEllipseItem):

    """
    A point symbolizing a 'waypoint' for the car
    """

    def_radius = 10

    def __init__(self, x, y, radius=def_radius):
        super(Waypoint, self).__init__(x - radius, y - radius, 2*radius, 2*radius)

        self.setBrush(QColor(250, 250, 250))
        self.setPen(QColor(30, 30, 50))

        self.setOpacity(0.9)
        self.setZValue(-1)

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(10)
        self.shadow.setColor(QColor(0, 0, 0))
        self.shadow.setOffset(0, 0)
        #self.setGraphicsEffect(self.shadow)

class InfoBox(QGraphicsObject):

    """
    A (rounded border, and translucide) rectangle containg some information
    """

    padding = 10

    def __init__(self, text="No text", fontsize=20, capitalize=True):
        super(InfoBox, self).__init__()

        if capitalize:
            text = text.upper()

        # Setting up text
        self.text = QGraphicsTextItem(text, self)
        self.font = QFont("Ubuntu", fontsize)
        self.text.setFont(self.font)
        self.text.setDefaultTextColor(QColor(255, 255, 255))

        self.text.setPos(self.padding, self.padding)

        self.textShadow = QGraphicsDropShadowEffect()
        self.textShadow.setBlurRadius(3)
        self.textShadow.setColor(QColor(0, 0, 0))
        self.textShadow.setOffset(1, 1)
        self.text.setGraphicsEffect(self.textShadow)

        # Background
        boxW = self.text.boundingRect().width() + 2*self.padding
        boxH = self.text.boundingRect().height() + 2*self.padding
        self.background = QGraphicsRectItem(0, 0, boxW, boxH, parent=self)
        self.background.setOpacity(0.5)
        self.background.setBrush(QColor(255, 255, 255))
        self.background.setZValue(-1)

        # Shadow effect on the background
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(30)
        self.shadow.setColor(QColor(60, 60, 90))
        self.shadow.setOffset(0, 0)
        self.background.setGraphicsEffect(self.shadow)

        # Caching
        self.setCacheMode(QGraphicsItem.ItemCoordinateCache)

    def paint(self, painter=None, style=None, widget=None):
        pass

    def setCaption(self, text):
        self.text.setPlainText(text)
        w = self.text.boundingRect().width() + 2 * self.padding
        h = self.text.boundingRect().height() + 2 * self.padding
        self.background.setRect(QRect(0, 0, w, h, parent=self))

    def setColor(self, color):
        self.background.setBrush(color)
        self.background.setPen(color)

    def setBackgroundOpacity(self, opacity):
        self.background.setOpacity(opacity)

    def boundingRect(self):
        return self.background.boundingRect()

class ObstacleWarning(InfoBox):
    def __init__(self, car):

        self.car = car
        car.addView(self)

        super(ObstacleWarning, self).__init__(fontsize=25)
        self.setBackgroundOpacity(0.8)

        self.update()

    def update(self):

        if self.car.distance is None:
            self.setCaption("No obstacle ahead")
            self.setColor(QColor(255, 255, 255))
        else:
            self.setCaption("Obstacle at : {0:.2f}cm".format(self.car.distance/10.0))
            hue = max(0., min(1., (float(self.car.distance - self.car.width)/Car.danger_distance))) * 0.33
            self.setColor( QColor.fromHsvF(hue, 0.5, 0.8, 0.5) )


class NotificationTooltip(InfoBox):

    # Visual parameters
    padding = 5
    def_fontsize = 13
    dy = 30

    # Animation parameters
    def_fade = 600
    def_duration = 2000

    # Types
    normal, error, information, ok = range(4)

    def __init__(self, text, duration=def_duration, type=normal):
        super(NotificationTooltip, self).__init__(text, fontsize=self.def_fontsize, capitalize=False)

        # Setting the correct color
        if type==self.normal:
            color = QColor(10, 10, 10)
        elif type==self.error:
            color = QColor(200, 40, 40)
        elif type==self.information:
            color = QColor(40, 70, 210)
        elif type == self.ok:
            color = QColor(45, 200, 70)
        else:
            raise Exception("Unknown notification type")

        self.setColor(color)

        self.setBackgroundOpacity(0.9)
        self.update()

        self.duration = duration

        self.animation = QParallelAnimationGroup()

    def itemChange(self, change, value):

        if change == QGraphicsItem.ItemSceneChange:
            self.animate()

        return super(NotificationTooltip, self).itemChange(change, value)

    def animate(self):

        # Opacity animation
        self.opacityAnim = QPropertyAnimation(self, "opacity")

        duration = self.def_fade * 2 + self.duration
        self.opacityAnim.setDuration(duration)

        t = 0.0
        self.opacityAnim.setStartValue(0.0)
        self.opacityAnim.setEndValue(0.0)

        t += self.def_fade
        self.opacityAnim.setKeyValueAt(t/duration, 1.0)

        t += self.duration
        self.opacityAnim.setKeyValueAt(t/duration, 1.0)

        # Position animation
        x, y = self.pos().x(), self.pos().y()

        self.posAnim = QPropertyAnimation(self, "pos")

        duration = self.def_fade * 2 + self.duration
        self.posAnim.setDuration(duration)

        t = 0.0
        self.posAnim.setStartValue(QPointF(x, y - self.dy))
        self.posAnim.setEndValue(QPointF(x, y - self.dy))

        t += self.def_fade
        self.posAnim.setKeyValueAt(t/duration, QPointF(x, y))

        t += self.duration
        self.posAnim.setKeyValueAt(t/duration, QPointF(x, y))


        # Animation container for the two animations
        self.animation.addAnimation(self.opacityAnim)
        self.animation.addAnimation(self.posAnim)

        self.animation.finished.connect(self.removeFromScene)
        self.animation.start(QAbstractAnimation.DeleteWhenStopped)

    def removeFromScene(self):
        if self.scene():
            self.scene().removeItem(self)
        else:
            print "HAS"


class GraphicsCarItem(QGraphicsObject):

    """
    A dynamic graphical representation of a car.
    Received an update signal (update() method) when the model is modified
    """

    # TODO : scaling should be dynamic (according to the car's width )
    default_image = QImage("img/car.png")

    # In the view, everything should be expressed in px (converted from the
    # model where mm should be used)
    default_width = 200
    default_length = 200
    scale_factor = 0.5

    def __init__(self, car, width=default_width, shadow=True):
        super(GraphicsCarItem, self).__init__()

        pen = QPen()

        self.car = car
        self.car.addView(self)

        self.l = self.car.pxLength()

        # Initializing image
        self.img = GraphicsCarItem.default_image
        self.image = QGraphicsPixmapItem(QPixmap(GraphicsCarItem.default_image), self)
        self.updateSize()

        # Shadow effect on the car's image
        if shadow:
            self.shadow = QGraphicsDropShadowEffect()
            self.shadow.setBlurRadius(80)
            self.shadow.setColor(QColor(80, 90, 220))
            self.shadow.setOffset(0, 0)
            self.image.setGraphicsEffect(self.shadow)


        # Setting up the caption
        self.text = QGraphicsTextItem("", self)
        self.text.setFont(QFont("Ubuntu"))
        self.text.setPos(-140, -140)

        self.textShadow = QGraphicsDropShadowEffect()
        self.textShadow.setBlurRadius(3)
        self.textShadow.setColor(QColor(0, 0, 0))
        self.textShadow.setOffset(1, 1)
        self.text.setGraphicsEffect(self.textShadow)

        self.text.setDefaultTextColor(QColor(210, 220, 250))
        self.text.font().setBold(True)

        # Initializing the "view ray"
        self.line = QLine(self.car.x, self.car.y, 0, 0)
        self.ray = QGraphicsLineItem(self.line, self)
        self.ray.setZValue(-1)

        pen.setColor(QColor(180, 200, 200))
        pen.setWidth(2)
        self.ray.setPen(pen)

        # Caching
        self.setCacheMode(QGraphicsItem.ItemCoordinateCache)
        # Antialiasing
        self.image.setTransformationMode(Qt.SmoothTransformation)

        self.update()

    def __del__(self):
        self.car.removeView(self)

    def setCaption(self, text):
        self.text.setPlainText(text)

    def paint(self, painter=None, style=None, widget=None):
        pass

    def updateSize(self):
        self.image.setScale(self.l / self.img.height())
        xOff, yOff = - self.image.boundingRect().width() / 2, - self.image.boundingRect().height() /2
        self.image.setOffset(xOff, yOff)

    def update(self):
        super(GraphicsCarItem, self).update()

        # Rotating the car around its center
        if self.image.rotation() != self.car.angle:
            self.image.setRotation( self.car.map.north_angle - 90 - degrees(self.car.angle) )

        if self.l != self.car.pxLength():
            self.l = self.car.pxLength()
            self.updateSize()

        self.setPos(self.car.x, self.car.y)

        # Updating the caption
        distance = 0
        if self.car.moving:
            self.setCaption("[{0:.1f}°] Car moving... ".format(degrees(self.car.angle)))
        elif self.car.distance:
            self.setCaption("[{0:.1f}°] Closest object at: {1}mm".format(degrees(self.car.angle), int(self.car.distance)))
            distance = self.car.distance*self.car.map.pixel_per_mm
        else:
            self.setCaption("No object ahead")

        # Updating the "ray"
        rayAngle = self.car.angle + pi/2 - radians(self.car.map.north_angle)
        line = QLine(0, 0, distance*cos(rayAngle), - distance*sin(rayAngle))
        self.ray.setLine(line)

    def boundingRect(self):
        return QRectF(self.x(), self.y(), self.image.boundingRect().width(), self.image.boundingRect().height())

    def x(self):
        return self.pos().x()

    def y(self):
        return self.pos().y()

    def topLeftX(self):
        return self.x() - (self.image.boundingRect().width() / 2)

    def topLeftY(self):
        return self.y() - (self.image.boundingRect().height() / 2)

    # def mousePressEvent(self, event):
    #   super(Car, self).mousePressEvent(event)
    # print "Car mouse event at ({} , {})".format(event.pos().x(),
    # event.pos().y())

    #   event.accept()

class MapCompass(QGraphicsObject):

    arrow_image = QImage('img/compass-mini.png')

    def __init__(self, angle=0):
        super(MapCompass, self).__init__()

        self.img = MapCompass.arrow_image
        self.arrow = QGraphicsPixmapItem(QPixmap(self.img))
        self.arrow.setTransformationMode(Qt.SmoothTransformation)
        self.arrow.setOffset(-self.img.width() / 2, -self.img.height() / 2)

        self.setAngle(angle)

        self.update()

    def setAngle(self, angle):
        self.angle = angle
        self.arrow.setRotation(-angle)

    def paint(self, painter=None, style=None, widget=None):
        pass

    def boundingRect(self):
        return self.arrow.boundingRect()

class CarCompass(QGraphicsObject):

    background = QImage("img/dashboard/compass.png")
    arrow = QImage("img/dashboard/compassArrow.png")

    orientations = ["NE", "SE", "SW", "NW"]

    """ A compass showing the car's current orientation """

    def __init__(self, car):
        super(CarCompass, self).__init__()

        self.car = car
        self.car.addView(self)

        # Compass's background
        self.background = QGraphicsPixmapItem(QPixmap(CarCompass.background), self)

        # Shadow effect on the compass
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(100)
        self.shadow.setColor(QColor(80, 80, 80))
        self.shadow.setOffset(0, 0)
        self.background.setGraphicsEffect(self.shadow)

        # Compass's needle
        self.needle = QGraphicsPixmapItem(QPixmap(CarCompass.arrow), self)
        self.needle.setOffset(-CarCompass.arrow.width()/2, -CarCompass.arrow.height()/2)
        self.needle.setPos(CarCompass.background.width()/2, CarCompass.background.height()/2)

        # Info box
        self.infobox = InfoBox(fontsize=15)
        self.infobox.setParentItem(self)

        # Caching
        self.setCacheMode(QGraphicsItem.ItemCoordinateCache)

        self.update()



    def paint(self, painter=None, style=None, widget=None):
        pass

    def update(self):
        super(CarCompass, self).update()

        # Rotating the NEEDLE around its center
        if self.needle.rotation() != self.car.angle:
            self.needle.setRotation(degrees(self.car.angle))

        # Updating the info box
        orientation = int(degrees(self.car.angle) / 90)
        self.infobox.setCaption("{0} | {1:.2f}°".format(CarCompass.orientations[orientation], degrees(self.car.angle)))
        x = (self.boundingRect().width() - self.infobox.boundingRect().width()) / 2
        y = self.boundingRect().height() + 20
        self.infobox.setPos(x, y)

        # #DEBUG RECT
        # self.rect = QGraphicsRectItem(self.infobox.boundingRect(), parent=self)
        # self.rect.setPen(QColor(255, 0, 0))

    def boundingRect(self):
        return self.background.boundingRect().united(self.infobox.boundingRect())


class CarThermometer(QGraphicsObject):

    """ A thermometer showing the car's current temperature """

    background_empty = QImage("img/dashboard/thermometer-empty.png")
    background_full = QImage("img/dashboard/thermometer-full.png")

    MsPerDegree = 50

    def __init__(self, car):
        super(CarThermometer, self).__init__()

        self.car = car
        self.car.addView(self)

        self.lastTemp = self.car.temperature

        # Initializing image

        # Background: an empty thermometer
        self.empty = QGraphicsPixmapItem(QPixmap(CarThermometer.background_empty), self)

        # Foreground: a full thermometer (that we'll crop according to the temperature)
        self.full = QGraphicsPixmapItem(QPixmap(CarThermometer.background_full), self)

        # Shadow effect on the thermometer
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(100)
        self.shadow.setColor(QColor(80, 80, 80))
        self.shadow.setOffset(0, 0)
        self.empty.setGraphicsEffect(self.shadow)

        # Info box
        self.infobox = InfoBox()
        self.infobox.setParentItem(self)

        # Caching
        self.setCacheMode(QGraphicsItem.ItemCoordinateCache)

        self.update()

    def paint(self, painter=None, style=None, widget=None):
        pass

    def setThermometer(self, temperature):
        y = max(0,  CarThermometer.background_full.height()*(1 - temperature / Car.max_temperature) - 130)
        y = min(y, CarThermometer.background_full.height())

        # Updating the 'full' thermometer's height
        newImage = CarThermometer.background_full.copy(
            0, y, CarThermometer.background_full.width(), CarThermometer.background_full.height())

        self.full.setPixmap(QPixmap(newImage))
        self.full.setPos(0, y)

        # Updating the info box
        self.infobox.setCaption("{0:.2f}°".format(temperature))
        self.infobox.setPos(self.empty.boundingRect().width() + 10, y)

        self.lastTemp = temperature

    def readThermometer(self):
        return self.car.temperature

    thermometer = Property(float, readThermometer, setThermometer)

    def update(self):
        super(CarThermometer, self).update()

        # Animation to make the shown temperature progress
        self.anim = QPropertyAnimation(self, "thermometer")

        duration = abs(self.lastTemp - self.car.temperature) * CarThermometer.MsPerDegree
        self.anim.setDuration(duration)

        self.anim.setStartValue(self.lastTemp)
        self.anim.setEndValue(self.car.temperature)

        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start(QAbstractAnimation.DeleteWhenStopped)

    def boundingRect(self):
        return self.empty.boundingRect().united(self.infobox.boundingRect())


class CarSpeedMeter(QGraphicsObject):

    background = QImage("img/dashboard/speedmeter.png")
    centerwheel = QImage("img/dashboard/centerwheel.png")
    arrow = QImage("img/dashboard/speed-arrow.png")

    zeroAngle = -34.7
    anglePerCmS = 1.22
    maxSpeed = 220

    # Speed of the arrow (when animated) in ms / (cm/s)
    MsPerAngle = 7

    """ A compass showing the car's current orientation """

    def __init__(self, car):
        super(CarSpeedMeter, self).__init__()

        self.car = car
        self.car.addView(self)

        self.lastSpeed = self.car.speed

        # Speed meter's background
        self.background = QGraphicsPixmapItem(QPixmap(CarSpeedMeter.background), self)

        # Shadow effect on the speedmeter
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(100)
        self.shadow.setColor(QColor(80, 80, 80))
        self.shadow.setOffset(0, 0)
        self.background.setGraphicsEffect(self.shadow)

        # Speed meter's arrow
        self.arrow = QGraphicsPixmapItem(QPixmap(CarSpeedMeter.arrow), self)
        self.arrow.setOffset(-CarSpeedMeter.arrow.width(), -CarSpeedMeter.arrow.height()/2)
        self.arrow.setPos(CarSpeedMeter.background.width()/2, CarSpeedMeter.background.height()/2)

        # Speed meter's arrow
        self.centerwheel = QGraphicsPixmapItem(QPixmap(CarSpeedMeter.centerwheel), self)
        self.centerwheel.setOffset(-CarSpeedMeter.centerwheel.width()/2, -CarSpeedMeter.centerwheel.height()/2)
        self.centerwheel.setPos(CarSpeedMeter.background.width()/2, CarSpeedMeter.background.height()/2)

        # Info box
        self.infobox = InfoBox(fontsize=22)
        self.infobox.setParentItem(self)

        # Caching the graphics
        self.setCacheMode(QGraphicsItem.ItemCoordinateCache)

        self.update()

    def paint(self, painter=None, style=None, widget=None):
        pass

    def setArrowRotation(self, rotation):
        self.arrow.setRotation(rotation)
    def getArrowRotation(self):
        return self.arrow.rotation()

    arrowRotation = Property(float, getArrowRotation, setArrowRotation)

    def update(self):
        super(CarSpeedMeter, self).update()

        # Rotating the SPEED ARROW around its center
        self.anim = QPropertyAnimation(self, "arrowRotation")

        curAngle = self.arrow.rotation()
        angleToReach = CarSpeedMeter.zeroAngle + self.car.speed * CarSpeedMeter.anglePerCmS

        duration = abs(angleToReach - curAngle) * CarSpeedMeter.MsPerAngle
        self.anim.setDuration(duration)

        self.anim.setStartValue(curAngle)
        self.anim.setEndValue(angleToReach)

        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.start(QAbstractAnimation.DeleteWhenStopped)

        # Updating the info box
        self.infobox.setCaption("{0:03d} cm/s".format(int(self.car.speed)))
        x = (self.boundingRect().width() - self.infobox.boundingRect().width()) / 2
        y = 330
        self.infobox.setPos(x, y)

    def boundingRect(self):
        return self.background.boundingRect().united(self.infobox.boundingRect())

class GraphicalParticleFilter(QGraphicsObject):

    checkmark = QImage('img/check.png')

    def __init__(self, partFilter):
        super(GraphicalParticleFilter, self).__init__()
        self.setCacheMode( QGraphicsItem.ItemCoordinateCache )
        self.particleFilter = partFilter

    def move(self, distance, angle = 0.):
        self.particleFilter.move(distance, angle)

    def sense(self, measuredDistance, angle):
        self.particleFilter.sense(measuredDistance, angle)

    def resample(self):
        self.particleFilter.resample()

    def normalize(self):
        self.particleFilter.normalize()

    def setMap(self, map):
        self.particleFilter.setMap(map)

    def paint(self, painter=None, style=None, widget=None):

        pen = QPen()
        pen.setColor(QColor(0, 200, 0))
        pen.setWidth(10)
        painter.setPen(pen)

        # Barycenter
        bX, bY = 0., 0.
        maxProba = max(particle.p for particle in self.particleFilter.particles)

        bX, bY = self.particleFilter.barycenter.x, self.particleFilter.barycenter.y

        # Drawing the particles
        for particle in self.particleFilter.particles:
            # Importance of the particle ranges from 0.0 to 1.0
            if maxProba == 0.:
                importance = 0.
            else:
                importance = particle.p / maxProba
            color = QColor.fromHsvF(importance * (0.30), 0.5, 0.8, 0.3)
            painter.setPen( color )
            painter.setBrush( color.lighter(0.2) )
            radius = 3 + importance*8
            painter.drawEllipse(QPointF(particle.x, particle.y), radius, radius)
            # painter.drawLine(particle.x, particle.y, bX, bY)

        color = QColor.fromHsvF(0.5*self.particleFilter.relevance, 0.5, 0.8, 0.8)
        painter.setPen( color.darker(10) )
        painter.setBrush( color )
        painter.drawEllipse(QPointF(bX, bY), 15, 15)

        # Drawing the checkmark (if the barycenter is relevant)
        if self.particleFilter.relevance >= ParticleFilter.DecentRelevance:
            painter.drawImage(bX - 8, bY - 8, self.checkmark)

    def boundingRect(self):
        return QRectF(0, 0, self.particleFilter.width, self.particleFilter.height )
