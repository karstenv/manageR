#!/usr/bin/env python
# -*- coding: utf-8 -*-

# PyQt imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class TabWidget(QTabWidget):

    blockCountChanged = pyqtSignal()
    cursorPositionChanged = pyqtSignal()
    bookmarksUpdated = pyqtSignal(dict)
    showAvailable = pyqtSignal(bool)
    hideAvailable = pyqtSignal(bool)
    redoAvailable = pyqtSignal(bool)
    undoAvailable = pyqtSignal(bool)
    copyAvailable = pyqtSignal(bool)
    modificationChanged = pyqtSignal(bool)
    
    
    def __init__(self, parent=None):
        QTabWidget.__init__(self, parent)
        
    def addTab(self, widget, icon, label):
        widget.modificationChanged.connect(self.modificationChanged.emit)
        widget.copyAvailable.connect(self.copyAvailable.emit)
        widget.undoAvailable.connect(self.undoAvailable.emit)
        widget.redoAvailable.connect(self.redoAvailable.emit)
        widget.hideAvailable.connect(self.hideAvailable.emit)
        widget.showAvailable.connect(self.showAvailable.emit)
        widget.cursorPositionChanged.connect(self.cursorPositionChanged.emit)
        widget.blockCountChanged.connect(self.blockCountChanged.emit)
        widget.bookmarksUpdated.connect(self.bookmarksUpdated.emit)
        return QTabWidget.addTab(self, widget, icon, label)



