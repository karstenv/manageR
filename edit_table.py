from PyQt4.QtCore import *
from PyQt4.QtGui import *
# Filippo check the import please we need the following got the icons
from PyQt4 import QtCore, QtGui
import sys
import time
import Icons_rc

class CustomTable(QTableWidget):
    def __init__(self, parent = None):
        QTableWidget.__init__(self, parent)
        if parent:
            self.parent = parent
        self.__initActions__()
        self.__initContextMenus__()
        

    def __initContextMenus__(self):
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self, SIGNAL("customContextMenuRequested(QPoint)"), self.tableWidgetContext)

    def tableWidgetContext(self, point):
        '''Create a menu for the tableWidget and associated actions'''
        tw_menu = QMenu("Menu", self)
        
        tw_menu.addAction(self.Undo)
        tw_menu.addAction(self.Redo)
        tw_menu.addSeparator()
        tw_menu.addAction(self.pasteAction)
        tw_menu.addAction(self.copyAction)
        tw_menu.addSeparator()
        tw_menu.addAction(self.insRowAction)
        tw_menu.addAction(self.insColAction)
        tw_menu.addAction(self.delColAction)
        tw_menu.addAction(self.delRowAction)
        tw_menu.addSeparator()
        tw_menu.addAction(self.clearAction)
        tw_menu.addAction(self.clearAllRowAction)
        tw_menu.addSeparator()
        tw_menu.addAction(self.SetLabelsAction)
        tw_menu.addAction(self.SetClassAction)
        tw_menu.addAction(self.SetLabelsAction)
        tw_menu.addAction(self.SetHeaderAction)
        tw_menu.addSeparator()
        tw_menu.addAction(self.GoToCell)
        tw_menu.addSeparator()
        tw_menu.addAction(self.CreateSubset)
        tw_menu.exec_(self.mapToGlobal(point))
        
        
        # Icons for the menu
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/icons/32x32/edit-undo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.Undo.setIcon(icon1)
        
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/icons/32x32/edit-redo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.Redo.setIcon(icon2)
        
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(":/icons/32x32/edit-copy.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.copyAction.setIcon(icon3)
        
        icon4 = QtGui.QIcon()
        icon4.addPixmap(QtGui.QPixmap(":/icons/32x32/edit-paste.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.pasteAction.setIcon(icon4)
        
        icon5 = QtGui.QIcon()
        icon5.addPixmap(QtGui.QPixmap(":/icons/32x32/insert_column.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.insColAction.setIcon(icon5)
        
        icon6 = QtGui.QIcon()
        icon6.addPixmap(QtGui.QPixmap(":/icons/32x32/insert_row.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.insRowAction.setIcon(icon6)
        
        icon7 = QtGui.QIcon()
        icon7.addPixmap(QtGui.QPixmap(":/icons/32x32/remove_column.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.delColAction.setIcon(icon7)
        
        icon8 = QtGui.QIcon()        
        icon8.addPixmap(QtGui.QPixmap(":/icons/32x32/remove_row.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.delRowAction.setIcon(icon8)
        
      
        
        
        
    def addData(self, data, startrow=None,  startcol = None):
        if startcol:
            sc = startcol#start column
        else:
            sc = 0 # n is for columns
        if startrow:
            sr = startrow
        else:
            sr = 0
        
        m = sr
        #print "Row, Col Commit:", sr, n
        for row in data:
            n = sc
            for item in row:
                #print repr(str(item))
                newitem = QTableWidgetItem(item)
                self.setItem(m,  n,  newitem)
                n+=1
            m+=1
            
            

    def __initActions__(self):
            
        self.copyAction = QAction("Copy",  self)
        #self.copyAction.setShortcut("Ctrl+C")shortcut MUST be set in main (openchem) to avoid conflicts
        self.addAction(self.copyAction)
        self.connect(self.copyAction, SIGNAL("triggered()"), self.copyCells)

        self.pasteAction = QAction("Paste",  self)
        #self.pasteAction.setShortcut("Ctrl+V") shortcut MUST be set in main (openchem) to avoid conflicts
        self.addAction(self.pasteAction)
        self.connect(self.pasteAction, SIGNAL("triggered()"), self.pasteClip)   

        self.insColAction = QAction("Insert Column",  self)
        self.addAction(self.insColAction)
        self.connect(self.insColAction, SIGNAL("triggered()"), self.addColumns)
        
        self.insRowAction = QAction("Insert Row",  self)
        self.addAction(self.insRowAction)
        self.connect(self.insRowAction, SIGNAL("triggered()"), self.addRows)
        
        self.delColAction = QAction("Delete Column(s)",  self)
        self.addAction(self.delColAction)
        self.connect(self.delColAction, SIGNAL("triggered()"), self.deleteColumns)
        
        self.delRowAction = QAction("Delete Row(s)",  self)
        self.addAction(self.delRowAction)
        self.connect(self.delRowAction, SIGNAL("triggered()"), self.deleteRows)
        
        #still to implement
        
        self.Undo = QAction("Undo",  self)
        self.addAction(self.Undo)
        #self.connect(
        
        self.Redo = QAction("Redo",  self)
        self.addAction(self.Redo)
        #self.connect(
        
        
        self.clearAction = QAction("Clear",  self)
        self.addAction(self.clearAction)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        
        
        self.clearAllRowAction = QAction("Clear All",  self)
        self.addAction(self.clearAllRowAction)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        
        self.SelectAll = QAction("Select All",  self)
        self.addAction(self.SelectAll)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        
        self.SetLabelsAction = QAction("Set as labels",  self)
        self.addAction(self.SetLabelsAction)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        
        self.SetClassAction = QAction("Set as class",  self)
        self.addAction(self.SetClassAction)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        
        self.SetHeaderAction = QAction("Set as header",  self)
        self.addAction(self.SetHeaderAction)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        #still to implement

        self.FillRowNumbers = QAction("Fill Selection with Row Numbers",  self)
        self.addAction(self.FillRowNumbers)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        
        self.FillRandomNumbers = QAction("Fill Selection with Random Numbers",  self)
        self.addAction(self.FillRandomNumbers)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        #still to implement
        
        self.GoToCell = QAction("Go to cell",  self)
        self.addAction(self.GoToCell)
        #self.connect(self.insRowAction, SIGNAL("triggered()"), self.deleteRows)
        
        self.CreateSubset = QAction("Create subset",  self)
        self.addAction(self.CreateSubset)
    
    ###############################
    
    
    def addRows(self):
        selRange  = self.selectedRanges()[0]
        topRow = selRange.topRow()
        bottomRow = selRange.bottomRow()
        for i in xrange(topRow, (bottomRow+1)):
            self.insRow(i)
        #print topRow,  bottomRow
        #print selRange
    
    def addColumns(self):
        selRange  = self.selectedRanges()[0]
        rightColumn = selRange.rightColumn()
        leftColumn = selRange.leftColumn()
        for i in xrange(leftColumn, (rightColumn+1)):
            self.insCol(i)
        #print topRow,  bottomRow
        #print selRange
    
    
    def deleteRows(self):
        selRange  = self.selectedRanges()[0]
        topRow = selRange.topRow()
        bottomRow = selRange.bottomRow()
        for i in xrange(topRow, (bottomRow+1)):
            self.delRow(i)
        #print topRow,  bottomRow
        #print selRange
    
    def deleteColumns(self):
        selRange  = self.selectedRanges()[0]
        rightColumn = selRange.rightColumn()
        leftColumn = selRange.leftColumn()
        for i in xrange(leftColumn, (rightColumn+1)):
            self.delCol(i)
        #print topRow,  bottomRow
        #print selRange
    
    def insCol(self,  col = None):
        if type(col) is int:
            self.insertColumn(col)
        else:
            self.insertColumn(self.currentColumn())
    
    def insRow(self,  row = None):
        if type(row) is int:
            self.insertRow(row)
        else:
            self.insertRow(self.currentRow())
            
            
    def delCol(self,  col = None):
        if type(col) is int:
            self.removeColumn(col)
        else:
            self.removeColumn(self.currentColumn())
        print ("fatto remove Variables c")    
            
    def delRow(self,  row = None):
        if type(row) is int:
            self.removeRow(row)
        else:
            self.removeRow(self.currentRow())
        print ("fatto remove Samples c")
    
    ####################################
        
        
    def pasteClip(self):
        
        cb = QApplication.clipboard()
        clipText = cb.text()
        t0 = time.time()
        clip2paste = self.splitClipboard(clipText)
        
        selRange  = self.selectedRanges()[0]#just take the first range
        topRow = selRange.topRow()
        bottomRow = selRange.bottomRow()
        rightColumn = selRange.rightColumn()
        leftColumn = selRange.leftColumn()

        #test to ensure pasted area fits in table 
        t1 = time.time()
        print "Clipboard split time:",  (t1-t0)
        if (len(clip2paste)+topRow) >= self.rowCount():
            self.setRowCount(len(clip2paste)+topRow)
        t2 = time.time()
        print "Row set time:",  (t2-t1)
        
        if (len(clip2paste[0])+rightColumn) >= self.columnCount():
            self.setColumnCount(len(clip2paste[0])+rightColumn)
        t3 = time.time()
        print "Column set time:", (t3-t2)
        self.addData(clip2paste, topRow,  leftColumn)
        print "Data Add Time:", (time.time()-t3)
    
    def splitClipboard(self,  clipText):
        #create list to be returned
        returnClip = []
        #split by carriage return which makes the rows
        clipList = clipText.split("\r\n")
        #split each item by tab (aka columns)
        for item in clipList:
            returnClip.append(item.split("\t"))
        
        return returnClip
            
 ######################################
 
    def copyCells(self):
        selRange  = self.selectedRanges()[0]#just take the first range
        topRow = selRange.topRow()
        bottomRow = selRange.bottomRow()
        rightColumn = selRange.rightColumn()
        leftColumn = selRange.leftColumn()
        #item = self.tableWidget.item(topRow, leftColumn)
        clipStr = QString()
        for row in xrange(topRow, bottomRow+1):
            for col in xrange(leftColumn, rightColumn+1):
                cell = self.item(row, col)
                if cell:
                    clipStr.append(cell.text())
                else:
                    clipStr.append(QString(""))
                clipStr.append(QString("\t"))
            clipStr.chop(1)
            clipStr.append(QString("\r\n"))
        
        cb = QApplication.clipboard()
        cb.setText(clipStr)
