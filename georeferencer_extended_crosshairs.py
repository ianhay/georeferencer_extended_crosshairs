# -*- coding: utf-8 -*-
# This code was generated or refactored by prompting Google Gemini.
# Licensed under the GNU GPL v2

import os
from qgis.PyQt.QtCore import Qt, QRectF, QObject, QPointF
from qgis.PyQt.QtGui import QColor, QPen, QKeySequence, QIcon, QPainter, QPixmap
from qgis.PyQt.QtWidgets import QAction, QShortcut, QApplication
from qgis.gui import QgsMapCanvasItem, QgsMapCanvas
from qgis.core import QgsPointXY, QgsSettings
from qgis.utils import iface

class GeorefCrosshairItem(QgsMapCanvasItem):
    def __init__(self, canvas):
        super().__init__(canvas)
        self._canvas = canvas
        self.setZValue(9999)
        self.pen = QPen(QColor(255, 0, 0, 255))
        self.pen.setWidth(1)
        self.pen.setCosmetic(True)
        self.center = None
        self.setVisible(False)

    def paint(self, painter, option, widget=None):
        if not self.center: return
        painter.setPen(self.pen)
        rect = self._canvas.viewport().rect()
        painter.drawLine(0, int(self.center.y()), rect.width(), int(self.center.y()))
        painter.drawLine(int(self.center.x()), 0, int(self.center.x()), rect.height())

    def update_position(self, pos):
        self.center = pos
        self.update()

    def boundingRect(self):
        return QRectF(self._canvas.viewport().rect()) if self._canvas else QRectF()

class GeorefExtendedCrosshairsPlugin(QObject):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.active = False
        self.crosshair_items = {}
        self.action = None
        self.shortcut = None

    def initGui(self):
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)
        painter.drawLine(0, 16, 32, 16)
        painter.drawLine(16, 0, 16, 32)
        painter.drawEllipse(10, 10, 12, 12)
        painter.end()
        icon = QIcon(pixmap)

        self.action = QAction(icon, "Toggle Georeferencer Crosshairs", self.iface.mainWindow())
        self.action.setCheckable(True)
        self.action.triggered.connect(self.toggle_state)
        
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Georeferencer Extended Crosshairs", self.action)
        
        settings = QgsSettings()
        hotkey = settings.value("GeorefExtendedCrosshairs/hotkey", "Ctrl+Alt+X")
        self.shortcut = QShortcut(QKeySequence(hotkey), self.iface.mainWindow())
        self.shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut.activated.connect(self.action.trigger)

    def unload(self):
        # Remove UI elements
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu("&Georeferencer Extended Crosshairs", self.action)
        
        # Disconnect and delete canvas items properly
        for canvas, item in list(self.crosshair_items.items()):
            try:
                canvas.xyCoordinates.disconnect(self.mouse_moved)
            except:
                pass
            # QgsMapCanvasItem cleanup
            if item:
                canvas.scene().removeItem(item)
        
        self.crosshair_items.clear()

        if self.shortcut:
            self.shortcut.setParent(None)

    def find_canvases(self):
        canvases = []
        for widget in QApplication.allWidgets():
            if "Georeferencer" in widget.windowTitle():
                found = widget.findChildren(QgsMapCanvas)
                canvases.extend(found)
        return list(set(canvases))

    def mouse_moved(self, point):
        canvas = self.sender()
        if canvas in self.crosshair_items:
            m2p = canvas.getCoordinateTransform()
            pixel_pos = m2p.transform(QgsPointXY(point))
            self.crosshair_items[canvas].update_position(pixel_pos)

    def toggle_state(self):
        self.active = self.action.isChecked()
        canvases = self.find_canvases()
        
        if self.active:
            if not canvases:
                self.iface.messageBar().pushMessage("Crosshairs", "Georeferencer not found. Open it first!", level=1)
                self.action.setChecked(False)
                return
            for canvas in canvases:
                if canvas not in self.crosshair_items:
                    item = GeorefCrosshairItem(canvas)
                    self.crosshair_items[canvas] = item
                    canvas.xyCoordinates.connect(self.mouse_moved)
                self.crosshair_items[canvas].setVisible(True)
        else:
            for item in self.crosshair_items.values():
                item.setVisible(False)