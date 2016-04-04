# -*- coding: utf-8 -*-

# rpy2 (R) imports
import rpy2.robjects as robjects

#PyQt imports
from PyQt4.QtCore import (Qt, SIGNAL, SLOT, QStringList, QString, QDir, QSettings,
                          QModelIndex, QObject, QCoreApplication, QEventLoop, 
                          QRegExp, QVariant, QUrl, QAbstractListModel,
                          QAbstractItemModel)
from PyQt4.QtGui import (QTreeWidget, QAbstractItemView, QAction, QVBoxLayout,
                         QMenu, QWidget, QListView, QIcon, QLineEdit, QToolButton,
                         QHBoxLayout, QTreeWidgetItem, QFileSystemModel, QCheckBox,
                         QTextEdit, QFileDialog, QDialog, QSpinBox, QLabel,
                         QApplication, QCursor, QInputDialog, QTreeView,QMessageBox,
                         QSizePolicy, QFontMetrics, QSortFilterProxyModel, 
                         QDesktopServices,)
# local imports
import resources, os, sys
from environment import TreeModel, SortFilterProxyModel
#from manageR_updated import MyHistory

class RWidget(QWidget):

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        # initialise standard settings
        self.setMinimumSize(30,30)
        self.parent = parent

    def emitCommands(self, commands):
        if not len(commands) < 1:
            self.emit(SIGNAL("emitCommands(QString)"), commands)

class WorkingDirectoryWidget(RWidget):

    def __init__(self, parent=None, base="."):
        RWidget.__init__(self, parent)
        # initialise standard settings
        self.base = base

        self.currentEdit = QLineEdit(self)
        self.currentEdit.setToolTip("Current working directory")
        self.currentEdit.setWhatsThis("Current working directory")
        self.currentEdit.setText(self.base)
        self.currentEdit.setMinimumHeight(QFontMetrics(self.font()).height()*1.5)

        self.setwdButton = QToolButton(self)
        self.setwdButton.setToolTip("Set working directory")
        self.setwdButton.setWhatsThis("Set working directory")
        self.setwdButton.setIcon(QIcon(":folder-home"))
        self.setwdButton.setText("setwd")
        self.setwdButton.setAutoRaise(True)

        horiz = QHBoxLayout(self)
        horiz.addWidget(self.currentEdit)
        horiz.addWidget(self.setwdButton)
        self.connect(self.setwdButton, SIGNAL("clicked()"), self.browseToFolder)

    def getWorkingDir(self):
        command = unicode("getwd()")
        directory = robjects.r(command)[0]
        self.currentEdit.setText(directory)
        #self.emitCommands(command)

    def browseToFolder(self):
        directory = QFileDialog.getExistingDirectory(
        self, "Choose working directory",self.currentEdit.text(),
        (QFileDialog.ShowDirsOnly|QFileDialog.DontResolveSymlinks))
        if not directory.isEmpty():
            self.setWorkingDir(directory)
            self.currentEdit.setText(directory)

    def setWorkingDir(self, directory):
        command = unicode("setwd('%s')" % (directory))
        robjects.r(command)
        #self.emitCommands(command)

class ScratchPadWidget(RWidget):

    def __init__(self, parent):
        RWidget.__init__(self, parent)
        textEdit = QTextEdit(self)
        textEdit.setToolTip("Random text goes here")
        hbox = QHBoxLayout(self)
        hbox.addWidget(textEdit)
        self.setFocusProxy(textEdit)
        
class FileSystemProxyModel(QSortFilterProxyModel):
    def __init__(self):
        QSortFilterProxyModel.__init__(self)
        
    def filterAcceptsRow(self, row, parent):
        if self.sourceModel().isDir(parent.child(row,0)):
            return True
        else:
            return QSortFilterProxyModel.filterAcceptsRow(self, row, parent)


class DirectoryWidget(RWidget):

    # If possible, the QGIS version should also alow
    # users to load OGR/GDAL supported files from here using rgdal
    # NOTE: Add a filter line edit at the bottom of the widget
    # Buttons: Up, Forward, Back, New folder, Synch with R
    # Right click: New folder, Delete, Load data, Load script
    # NOTE: Also show file size, and date if possible

    def __init__(self, parent, base="."):
        RWidget.__init__(self, parent)
        self.base = base
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.proxyModel = FileSystemProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.proxyModel.setFilterKeyColumn(0)
        self.proxyModel.setSourceModel(self.model)
        
        self.listView = QListView(self)
        self.listView.setModel(self.proxyModel)
        index = self.model.index(QDir.currentPath())
        self.listView.setRootIndex(self.proxyModel.mapFromSource(index))
        self.listView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.lineEdit = QLineEdit(self)
        
        filterLineEdit = QLineEdit()
        filterLabel = QLabel("Filter:")
        self.connect(filterLineEdit, SIGNAL("textChanged(QString)"), 
            self.proxyModel.setFilterWildcard)
        self.actions = []

        self.upAction = QAction("&Up", self)
        self.upAction.setStatusTip("Move to parent directory")
        self.upAction.setToolTip("Move to parent directory")
        self.upAction.setIcon(QIcon(":go-up"))
        self.upAction.setEnabled(True)
        self.actions.append(self.upAction)
        self.newAction = QAction("&New Directory", self)
        self.newAction.setStatusTip("Create new directory")
        self.newAction.setToolTip("Create new directory")
        self.newAction.setIcon(QIcon(":folder-new"))
        self.newAction.setEnabled(True)
        self.actions.append(self.newAction)
        self.synchAction = QAction("&Synch", self)
        self.synchAction.setStatusTip("Synch with current working directory")
        self.synchAction.setToolTip("Synch with current working directory")
        self.synchAction.setIcon(QIcon(":view-refresh"))
        self.synchAction.setEnabled(True)
        self.actions.append(self.synchAction)
        self.rmAction = QAction("&Delete", self)
        self.rmAction.setStatusTip("Delete selected item")
        self.rmAction.setToolTip("delete selected item")
        self.rmAction.setIcon(QIcon(":edit-delete"))
        self.rmAction.setEnabled(True)
        self.actions.append(self.rmAction)
        self.openAction = QAction("&Open", self)
        self.openAction.setStatusTip("Open selected R script")
        self.openAction.setToolTip("Open selected R script")
        self.openAction.setIcon(QIcon(":document-open"))
        self.openAction.setEnabled(True)
        self.actions.append(self.openAction)
        self.loadAction = QAction("&Load", self)
        self.loadAction.setStatusTip("Load selected R data")
        self.loadAction.setToolTip("Load selected R data")
        self.loadAction.setIcon(QIcon(":document-open"))
        self.loadAction.setEnabled(True)
        self.actions.append(self.loadAction)
        self.setAction = QAction("Set as &current", self)
        self.setAction.setStatusTip("Set folder as R working directory")
        self.setAction.setToolTip("Set folder as R working directory")
        self.setAction.setIcon(QIcon(":folder-home"))
        self.setAction.setEnabled(True)
        self.actions.append(self.setAction)
        self.loadExternal = QAction("Open &Externally", self)
        self.loadExternal.setStatusTip("Load file in external application")
        self.loadExternal.setToolTip("Load file in external application")
        self.loadExternal.setIcon(QIcon(":folder-system"))
        self.loadExternal.setEnabled(True)
        self.actions.append(self.loadExternal)
        self.rootChanged()
        
        hiddenAction = QAction("Toggle hidden files", self)
        hiddenAction.setStatusTip("Show/hide hidden files and folders")
        hiddenAction.setToolTip("Show/hide hidden files and folders")
        hiddenAction.setIcon(QIcon(":stock_keyring"))
        hiddenAction.setCheckable(True)

        self.connect(self.newAction, SIGNAL("triggered()"), self.newFolder)
        self.connect(self.upAction, SIGNAL("triggered()"), self.upFolder)
        self.connect(self.synchAction, SIGNAL("triggered()"), self.synchFolder)
        self.connect(self.rmAction, SIGNAL("triggered()"), self.rmItem)
        self.connect(self.openAction, SIGNAL("triggered()"), self.openItem)
        self.connect(self.loadAction, SIGNAL("triggered()"), self.loadItem)
        self.connect(self.loadExternal, SIGNAL("triggered()"), self.externalItem)
        self.connect(self.setAction, SIGNAL("triggered()"), self.setFolder)
        self.connect(hiddenAction, SIGNAL("toggled(bool)"), self.toggleHidden)
        self.connect(self.listView, SIGNAL("activated(QModelIndex)"), self.cdFolder)
        self.connect(self.listView, SIGNAL("customContextMenuRequested(QPoint)"), self.customContext)
        self.connect(self.lineEdit, SIGNAL("returnPressed()"), self.gotoFolder)

        upButton = QToolButton()
        upButton.setDefaultAction(self.upAction)
        upButton.setAutoRaise(True)
        newButton = QToolButton()
        newButton.setDefaultAction(self.newAction)
        newButton.setAutoRaise(True)
        synchButton = QToolButton()
        synchButton.setDefaultAction(self.synchAction)
        synchButton.setAutoRaise(True)
        setButton = QToolButton()
        setButton.setDefaultAction(self.setAction)
        setButton.setAutoRaise(True)
        hiddenButton = QToolButton()
        hiddenButton.setDefaultAction(hiddenAction)
        hiddenButton.setAutoRaise(True)

        hbox = QHBoxLayout()
        hbox.addWidget(upButton)
        hbox.addWidget(synchButton)
        hbox.addWidget(newButton)
        hbox.addWidget(setButton)
        hbox.addWidget(hiddenButton)
        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox)
        vbox.addWidget(self.lineEdit)
        vbox.addWidget(self.listView)
        vbox.addWidget(filterLabel)
        vbox.addWidget(filterLineEdit)

    def toggleHidden(self, toggled):
        base = QDir.AllDirs|QDir.AllEntries|QDir.NoDotAndDotDot
        if toggled:
            self.model.setFilter(base|QDir.Hidden)
        else:
            self.model.setFilter(base)

    def gotoFolder(self):
        text = self.lineEdit.text()
        self.listView.setRootIndex(self.proxyModel.mapFromSource(self.model.index(text, 0)))

    def rootChanged(self):
        index1 = self.listView.rootIndex()
        index2 = self.proxyModel.mapToSource(index1)
        self.lineEdit.setText(self.model.filePath(index2))
        self.listView.setCurrentIndex(index1)

    def customContext(self, pos):
        index = self.listView.indexAt(pos)
        index = self.proxyModel.mapToSource(index)
        if not index.isValid():
            self.rmAction.setEnabled(False)
            self.openAction.setEnabled(False)
            self.loadAction.setEnabled(False)
        elif not self.model.isDir(index):
            info = self.model.fileInfo(index)
            suffix = info.suffix()
            if suffix in ("Rd","Rdata","RData"):
                self.loadAction.setEnabled(True)
                self.openAction.setEnabled(False)
                self.loadExternal.setEnabled(False)
            elif suffix in ("txt","csv","R","r"):
                self.openAction.setEnabled(True)
                self.loadAction.setEnabled(False)
                self.loadExternal.setEnabled(True)
            else:
                self.loadAction.setEnabled(False)
                self.openAction.setEnabled(False)
                self.loadExternal.setEnabled(True)
        menu = QMenu(self)
        for action in self.actions:
            menu.addAction(action)
        menu.exec_(self.listView.mapToGlobal(pos))

    def openItem(self):
        index = self.listView.currentIndex()
        index = self.proxyModel.mapToSource(index)
        self.emit(SIGNAL("openFileRequest(QString)"),
        self.model.filePath(index))

    def loadItem(self):
        index = self.listView.currentIndex()
        index = self.proxyModel.mapToSource(index)
        self.emit(SIGNAL("loadFileRequest(QString)"),
        self.model.filePath(index))
        
    def externalItem(self):
        index = self.listView.currentIndex()
        index = self.proxyModel.mapToSource(index)
        QDesktopServices.openUrl(QUrl(self.model.filePath(index)))

    def newFolder(self):
        text, ok = QInputDialog.getText(self,
            "New Folder", "Folder name:", QLineEdit.Normal,
            "new_folder")
        if ok:
            index = self.listView.rootIndex()
            index = self.proxyModel.mapToSource(index)
            self.model.mkdir(index, text)

    def setFolder(self):
        index = self.listView.currentIndex()
        index = self.proxyModel.mapToSource(index)
        commands = "setwd('%s')" % self.model.filePath(index)
        self.emitCommands(commands)

    def rmItem(self):
        index = self.listView.currentIndex()
        if index == self.listView.rootIndex():
            return
        yes = QMessageBox.question(self, "manageR Warning",
            "Are you sure you want to delete '%s'?" % self.model.fileName(index),
            QMessageBox.Yes|QMessageBox.Cancel)
        if not yes == QMessageBox.Yes:
            return
        index = self.proxyModel.mapToSource(index)
        if self.model.isDir(index):
            result = self.model.rmdir(index)
        else:
            result = self.model.remove(index)
        if not result:
            QMessageBox.warning(self, "manageR Error",
            "Unable to delete %s!" % self.model.fileName(index))

    def upFolder(self):
        index = self.listView.rootIndex()
        index = self.proxyModel.parent(index)
        self.listView.setRootIndex(index)
        self.rootChanged()

    def cdFolder(self):
        indexes = self.listView.selectedIndexes()
        if len(indexes) < 1:
            return
        index = indexes[0]
        if self.model.isDir(self.proxyModel.mapToSource(index)):
            self.listView.setRootIndex(index)
        self.rootChanged()
        self.listView.clearSelection()

    def synchFolder(self):
        text = robjects.r.getwd()[0]
        index = self.model.index(text, 0)
        index = self.proxyModel.mapFromSource(index)
        self.listView.setRootIndex(index)
        self.rootChanged()

class HistoryWidget(RWidget):

    class ListView(QListView):
        def __init__(self, parent):
            QListView.__init__(self, parent)
            self.setAlternatingRowColors(True)
            self.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.setSelectionMode(QAbstractItemView.ExtendedSelection)

        def mousePressEvent(self, event):
            item = self.indexAt(event.globalPos())
            if not item and event.button() == Qt.LeftButton:
                self.setSelection(QRect(), QItemSelectionModel.Clear)
            QListView.mousePressEvent(self, event)

        def selectionChanged(self, new, old):
            self.emit(SIGNAL("selectionChanged()"))
            QListView.selectionChanged(self, new, old)

    def __init__(self, parent):
        RWidget.__init__(self, parent)
        self.parent = parent
        self.commandList = self.ListView(self)
        self.commandList.setToolTip("Right click item to view options")
        self.commandList.setWhatsThis("List of previous commands")

        self.copyAction = QAction("&Copy command(s)", self)
        self.copyAction.setStatusTip("Copy the selected command(s) to the clipboard")
        self.copyAction.setToolTip("Copy the selected command(s) to the clipboard")
        self.copyAction.setIcon(QIcon(":edit-copy"))
        self.copyAction.setEnabled(False)

        self.selectAction = QAction("Select &all", self)
        self.selectAction.setStatusTip("Select all commands")
        self.selectAction.setToolTip("Select all commands")
        self.selectAction.setIcon(QIcon(":edit-select-all"))

        self.runAction = QAction("&Run command(s)", self)
        self.runAction.setStatusTip("Run the selected command(s) in the console")
        self.runAction.setToolTip("Run the selected command(s) in the console")
        self.runAction.setIcon(QIcon(":utilities-terminal"))
        self.runAction.setEnabled(False)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.commandList)

        self.connect(self.copyAction, SIGNAL("triggered()"), self.copy)
        #self.connect(self.insertAction, SIGNAL("triggered()"), self.insert)
        self.connect(self.runAction, SIGNAL("triggered()"), self.run)
        #self.connect(self.clearAction, SIGNAL("triggered()"), self.clear)
        self.connect(self.selectAction, SIGNAL("triggered()"), self.selectAll)
        self.connect(self.commandList, SIGNAL("doubleClicked(QModelIndex)"),
        self.doubleClicked)
        self.connect(self.commandList, SIGNAL("selectionChanged()"), self.selectionChanged)

    def setModel(self, model):
        self.commandList.setModel(model)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.runAction)
        menu.addAction(self.copyAction)
        menu.addAction(self.selectAction)
        menu.exec_(event.globalPos())

    def selectionChanged(self):
        count = len(self.commandList.selectedIndexes())
        if count > 0:
            self.runAction.setEnabled(True)
            self.copyAction.setEnabled(True)
        else:
            self.runAction.setEnabled(False)
            self.copyAction.setEnabled(False)

    def copy(self):
        commands = QString()
        selected = self.commandList.selectedIndexes()
        count = 1
        for index in selected:
            if count == len(selected):
                commands.append(self.commandList.model().data(index,
                    Qt.DisplayRole).toString())
            else:
                commands.append(self.commandList.model().data(index, 
                    Qt.DisplayRole).toString()+"\n")
            count += 1
        clipboard = QApplication.clipboard()
        clipboard.setText(commands, QClipboard.Clipboard)

    def run(self):
        commands = QString()
        selected = self.commandList.selectedIndexes()
        count = 1
        for index in selected:
            if count == len(selected):
                commands.append(self.commandList.model().data(index, 
                    Qt.DisplayRole).toString())
            else:
                commands.append(self.commandList.model().data(index, 
                    Qt.DisplayRole).toString()+"\n")
            count += 1
        self.runCommands(commands)

    def selectAll(self):
        self.commandList.selectAll()

    def runCommands(self, commands):
        if not commands.isEmpty():
            self.emitCommands(commands)

    def doubleClicked(self, index):
        commands = self.commandList.model().data(
        index, Qt.DisplayRole)
        self.runCommands(commands.toString())
        self.parent.setFocus(Qt.MouseFocusReason)
        
class GraphicsWidget(RWidget):         

    def __init__(self, parent):
        RWidget.__init__(self, parent)
        self.parent = parent
        self._hist = History(items=[])
        self._currentPlot = QVariant(QString())
        
        self.callLineEdit = QLineEdit()
        self.callLineEdit.setReadOnly(True)
        self.callLineEdit.setToolTip("Commands to reproduce plot")
        self.callLineEdit.setWhatsThis("Commands to reproduce plot")
        actions = []

#        playAction = QAction("Replay", self)
#        playAction.setStatusTip("Replay selected plot")
#        playAction.setToolTip("Replay selected plot")
#        playAction.setIcon(QIcon(":edit-copy"))
#        actions.append(playAction)
        
        firstAction = QAction("End", self)
        firstAction.setStatusTip("Move to end of history")
        firstAction.setToolTip("Move to end of history")
        firstAction.setIcon(QIcon(":go-first"))
        actions.append(firstAction)
        
        previousAction = QAction("Previous", self)
        previousAction.setStatusTip("Move to previous plot")
        previousAction.setToolTip("Move to previous plot")
        previousAction.setIcon(QIcon(":go-previous"))
        actions.append(previousAction)

        infoAction = QAction("Info", self)
        infoAction.setStatusTip("Show plot info")
        infoAction.setToolTip("Show plot info")
        infoAction.setIcon(QIcon(":gtk-info"))
        actions.append(infoAction)
        
        nextAction = QAction("Next", self)
        nextAction.setStatusTip("Move to next plot")
        nextAction.setToolTip("Move to next plot")
        nextAction.setIcon(QIcon(":go-next"))
        actions.append(nextAction)
        
        lastAction = QAction("Start", self)
        lastAction.setStatusTip("Move to latest plot")
        lastAction.setToolTip("Move to latest plot")
        lastAction.setIcon(QIcon(":go-last"))
        actions.append(lastAction)
        actions.append(None)
        
        clearAction = QAction("Clear", self)
        clearAction.setStatusTip("Clear plot history")
        clearAction.setToolTip("Clear plot history")
        clearAction.setIcon(QIcon(":edit-clear"))
        actions.append(clearAction)
        

        hbox = QHBoxLayout()
        for action in actions:
            if not action is None:
                button = QToolButton()
                button.setDefaultAction(action)
                button.setAutoRaise(True)
                hbox.addWidget(button)
            else:
                hbox.addWidget(self.callLineEdit)
        self.setLayout(hbox)

        self.connect(firstAction, SIGNAL("triggered()"), self.first)
        self.connect(previousAction, SIGNAL("triggered()"), self.previous)
        self.connect(infoAction, SIGNAL("triggered()"), self.info)
        self.connect(nextAction, SIGNAL("triggered()"), self.next)
        self.connect(lastAction, SIGNAL("triggered()"), self.last)
        self.connect(clearAction, SIGNAL("triggered()"), self.clear)
        
    def setHistory(self, history):
        self._hist = history

    def history(self):
        return self._hist

    def previous(self):
        return self.navigateHistory(True)

    def next(self):
        return self.navigateHistory(False)

    def navigateHistory(self, up=True):
        if up:
            self._currentPlot = self.history().previous()
        else:
            self._currentPlot = self.history().next()
        tmp = self._currentPlot.toPyObject()
        if not tmp == QString():
            self.callLineEdit.setText(tmp[2])
        else:
            self._currentPlot = self.history().previous()
        return self._currentPlot

    def first(self):
        temp = self.previous()
        item = self._currentPlot
        while not isinstance(temp,QVariant):
            item = temp
            temp = self.previous()
        self._currentPlot = item

    def last(self):
        temp = self.next()
        item = self._currentPlot
        while not isinstance(temp,QVariant):
            item = temp
            temp = self.next()
        self._currentPlot = item          

    def info(self):
        plot = self._currentPlot.toPyObject()
        if isinstance(plot,QString):
            return
        plot = self._currentPlot.toPyObject()
        msgBox = QMessageBox()
        msgBox.setText("Plot information:")
        msgBox.setInformativeText("Original device: %s" % str(plot[0])
                                  +"\nHistory position: %s" % str(self.history().currentIndex()+1)
                                  +"\nSize: %s bytes" % str(plot[1])
                                  +"\n\nWould you like to replay the plot now?")
        msgBox.setDetailedText("Original call:\n%s" % plot[2])
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Close)
        msgBox.setDefaultButton(QMessageBox.Ok)
        if msgBox.exec_() == QMessageBox.Ok:
            print plot[3]

    def clear(self):
        self.setHistory(History(items=[]))
        self.callLineEdit.setText(QString())
        
    def updateHistory(self, item):
        self.history().update([item])
        self.previous()        

class WorkspaceWidget(RWidget):

    class TreeView(QTreeView):
        def __init__(self, parent):
            QTreeView.__init__(self, parent)
            self.setAlternatingRowColors(True)
            self.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.setSelectionMode(QAbstractItemView.SingleSelection)
            self.connect(self, SIGNAL("expanded(QModelIndex)"), self.expanded)

        def expanded(self, index):
            self.model().updateEntry(index)

        def mousePressEvent(self, event):
            item = self.childAt(event.globalPos())
            if not item and event.button() == Qt.LeftButton:
                self.clearSelection()
            QTreeView.mousePressEvent(self, event)

        def selectionChanged(self, new, old):
            self.emit(SIGNAL("itemSelectionChanged()"))
            QTreeView.selectionChanged(self, new, old)

    def __init__(self, parent=None):
        RWidget.__init__(self, parent)
        self.workspaceTree = self.TreeView(self)
        self.workspaceTree.setSortingEnabled(True)
        self.proxyModel = SortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
#        self.proxyModel.setFilterKeyColumn(1)
        self.model = TreeModel()
        self.proxyModel.setSourceModel(self.model)
#        self.workspaceTree.setModel(self.model)
        self.workspaceTree.setModel(self.proxyModel)

        self.actions = []
        self.refreshAction = QAction("Re&fresh variables", self)
        self.refreshAction.setToolTip("Refresh environment browser")
        self.refreshAction.setWhatsThis("Refresh environment browser")
        self.refreshAction.setIcon(QIcon(":view-refresh"))
        self.refreshAction.setEnabled(True)
        self.actions.append(self.refreshAction)

        self.loadAction = QAction("&Load data", self)
        self.loadAction.setToolTip("Load R variable(s) from file")
        self.loadAction.setWhatsThis("Load R variable(s) from file")
        self.loadAction.setIcon(QIcon(":custom-open-data"))
        self.loadAction.setEnabled(True)
        self.actions.append(self.loadAction)

        self.exportAction = QAction("&Export to file", self)
        self.exportAction.setToolTip("Export data to file")
        self.exportAction.setWhatsThis("Export data to file")
        self.exportAction.setIcon(QIcon(":custom-document-export"))
        self.exportAction.setEnabled(False)
        self.actions.append(self.exportAction)

        self.saveAction = QAction("&Save variable", self)
        self.saveAction.setToolTip("Save R variable to file")
        self.saveAction.setWhatsThis("Save R variable to file")
        self.saveAction.setIcon(QIcon(":custom-save-data"))
        self.saveAction.setEnabled(False)
        self.actions.append(self.saveAction)

        self.methodAction = QAction("&Print available methods", self)
        self.methodAction.setToolTip("Print available methods for object class")
        self.methodAction.setWhatsThis("Print available methods for object class")
        self.methodAction.setIcon(QIcon(":document-properties"))
        self.methodAction.setEnabled(False)
        self.actions.append(self.methodAction)

        self.attributeAction = QAction("Print object &attributes", self)
        self.attributeAction.setToolTip("Print available attributes for object class")
        self.attributeAction.setWhatsThis("Print available attributes for object class")
        self.attributeAction.setIcon(QIcon(":custom-tag"))
        self.attributeAction.setEnabled(False)
        self.actions.append(self.attributeAction)

        self.summaryAction = QAction("Print object Su&mmary", self)
        self.summaryAction.setToolTip("Print summary of object")
        self.summaryAction.setWhatsThis("Print summary of object")
        self.summaryAction.setIcon(QIcon(":custom-summary"))
        self.summaryAction.setEnabled(False)
        self.actions.append(self.summaryAction)

        self.plotAction = QAction("&Quick plot", self)
        self.plotAction.setToolTip("Create minimal plot for visualisation")
        self.plotAction.setWhatsThis("Create minimal plot for visualisation")
        self.plotAction.setIcon(QIcon(":gnome-fs-bookmark-missing"))
        self.plotAction.setEnabled(False)
        self.actions.append(self.plotAction)

        self.rmAction = QAction("&Remove", self)
        self.rmAction.setToolTip("Remove selected variable")
        self.rmAction.setWhatsThis("Removed selected variable")
        self.rmAction.setIcon(QIcon(":edit-delete"))
        self.rmAction.setEnabled(False)
        self.actions.append(self.rmAction)

        vbox = QVBoxLayout(self)
        vbox.addWidget(self.workspaceTree)

        self.variables = dict()
        self.connect(self.plotAction, SIGNAL("triggered()"), self.plotVariable)
        self.connect(self.summaryAction, SIGNAL("triggered()"), self.summariseVariable)
        self.connect(self.rmAction, SIGNAL("triggered()"), self.removeVariable)
        self.connect(self.exportAction, SIGNAL("triggered()"), self.exportVariable)
        self.connect(self.saveAction, SIGNAL("triggered()"), self.saveVariable)
        self.connect(self.loadAction, SIGNAL("triggered()"), self.loadRVariable)
        self.connect(self.methodAction, SIGNAL("triggered()"), self.printMethods)
        self.connect(self.refreshAction, SIGNAL("triggered()"), self.updateEnvironment)
        self.connect(self.attributeAction, SIGNAL("triggered()"), self.printAttributes)
        self.connect(self.workspaceTree, SIGNAL("itemSelectionChanged()"), self.selectionChanged)
        self.updateEnvironment()

    def mousePressEvent(self, event):
        item = self.workspaceTree.indexAt(event.globalPos())
        if not item and event.button() == Qt.LeftButton:
            self.workspaceTree.clearSelection()
        RWidget.mousePressEvent(self, event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.addAction(self.refreshAction)
        menu.addSeparator()
        for action in self.actions[1:-1]:
            menu.addAction(action)
        menu.addSeparator()
        menu.addAction(self.rmAction)
        menu.exec_(event.globalPos())

    def selectionChanged(self):
        items = self.workspaceTree.selectedIndexes()
        if len(items) < 1:
            for action in self.actions[2:]:
                action.setEnabled(False)
        else:
            for action in self.actions[2:]:
                action.setEnabled(True)

    def printMethods(self):
        items = self.workspaceTree.selectedIndexes()
        if len(items) < 1:
            return False
        itemType = self.workspaceTree.model().getItem(items[0]).data(1)
        self.runCommand("methods(class='%s')" % (itemType,))

    def printAttributes(self):
        items = self.workspaceTree.selectedIndexes()
        if len(items) < 1:
            return False
        tree = self.workspaceTree.model().parentTree(items[0])
        self.runCommand('names(attributes(%s))' % tree)

    def summariseVariable(self):
        items = self.workspaceTree.selectedIndexes()
        if len(items) < 1:
            return False
        tree = self.workspaceTree.model().parentTree(items[0])
        self.runCommand('summary(%s)' % tree)

    def plotVariable(self):
        items = self.workspaceTree.selectedIndexes()
        if len(items) < 1:
            return False
        index = items[0]
        tree = self.workspaceTree.model().parentTree(index)
        self.runCommand('plot(%s)' % tree)

    def removeVariable(self):
        items = self.workspaceTree.selectedIndexes()
        if len(items) < 1:
            return False
        item = items[0]
        tree = self.workspaceTree.model().parentTree(item)
        command = "rm(%s)" % tree
        if not item.parent() == QModelIndex():
            command = "%s <- NULL" % tree
        waiter = SignalWaiter(self.parent, SIGNAL("errorOutput()"))
        self.runCommand(command)
        if not waiter.wait(50):
            self.workspaceTree.model().removeRows(item.row(),1, item.parent())

    def exportVariable(self):
        items = self.workspaceTree.selectedIndexes()
        if len(items) < 1:
            return False
        tree = self.workspaceTree.model().parentTree(items[0])
        fd = QFileDialog(self.parent, "Save data to file", str(robjects.r.getwd()),
        "Comma separated (*.csv);;Text file (*.txt);;All files (*.*)")
        fd.setAcceptMode(QFileDialog.AcceptSave)
        if not fd.exec_() == QDialog.Accepted:
            return False
        files = fd.selectedFiles()
        selectedFile = files.first()
        if selectedFile.length() == 0:
            return False
        suffix = QString(fd.selectedNameFilter())
        index1 = suffix.lastIndexOf("(")+2
        index2 = suffix.lastIndexOf(")")
        suffix = suffix.mid(index1, index2-index1)
        if not selectedFile.endsWith(suffix):
            selectedFile.append(suffix)
        command = QString('write.table(%s, file = "%s",' % (tree, selectedFile))
        command.append(QString('append = FALSE, quote = TRUE, sep = ",", eol = "\\n", na = "NA"'))
        command.append(QString(', dec = ".", row.names = FALSE, col.names = TRUE, qmethod = "escape")'))
        self.runCommand(command)

    def saveVariable(self):
        items = self.workspaceTree.selectedIndexes()
        if len(items) < 1:
            return False
        item = self.workspaceTree.model().getItem(items[0])
        name = item.data(0)
        parent = item.parent()
        names = [name]
        while not parent is None:
            names.append(QString(parent.data(0)))
            parent = parent.parent()
        if len(names) > 1:
            names.pop(-1)
        name = names[-1]
        fd = QFileDialog(self.parent, "Save data to file",
        os.path.join(str(robjects.r.getwd()[0]), unicode(name)+".Rdata"), "R data file (*.Rdata)")
        fd.setAcceptMode(QFileDialog.AcceptSave)
        if not fd.exec_() == QDialog.Accepted:
            return False
        files = fd.selectedFiles()
        selectedFile = files.first()
        if selectedFile.length() == 0:
            return False
        suffix = QString(fd.selectedNameFilter())
        index1 = suffix.lastIndexOf("(")+2
        index2 = suffix.lastIndexOf(")")
        suffix = suffix.mid(index1, index2-index1)
        if not selectedFile.endsWith(suffix):
            selectedFile.append(suffix)
        commands = QString('save(%s, file="%s")' % (name,selectedFile))
        self.runCommand(commands)

    def loadRVariable(self):
        fd = QFileDialog(self.parent, "Load R variable(s) from file",
        str(robjects.r.getwd()[0]), "R data (*.Rdata);;All files (*.*)")
        fd.setAcceptMode(QFileDialog.AcceptOpen)
        fd.setFileMode(QFileDialog.ExistingFile)
        if fd.exec_() == QDialog.Rejected:
            return False
        files = fd.selectedFiles()
        selectedFile = files.first()
        if selectedFile.length() == 0:
            return False
        self.runCommand(QString('load("%s")' % (selectedFile)))
        self.updateEnvironment()

    def runCommand(self, command):
        if not command == "":
            self.emitCommands(command)

    def updateEnvironment(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        self.model = TreeModel()
        self.proxyModel.setSourceModel(self.model)
#        self.workspaceTree.setModel(model)
        QApplication.restoreOverrideCursor()
        return True

# This class is based on the QxtSignalWaiter
# from http://qtnode.net/wiki/QxtSignalWaiter
# Released under the GPL/LGPL/QPL
class SignalWaiter(QObject):

    def __init__(self, sender, signal):
        QObject.__init__(self)
        self.connect(sender, signal, self.signalCaught)
        self.ready = False
        self.timeout = False

    #def wait(sender, signal, msec):
        ##Returns true if the signal was caught, returns false if the wait timed out
        #w = SignalWaiter(sender, signal)
        #return w.wait(msec)

    def wait(self, msec):
        # Returns true if the signal was caught, returns false if the wait timed out
        # Check input parameters
        if msec < -1:
            return False
        # activate the timeout
        if not msec == -1:
            self.timerID = self.startTimer(msec)

        # Begin waiting
        while not self.ready and not self.timeout:
            QCoreApplication.processEvents(QEventLoop.WaitForMoreEvents)

        # Return status
        self.killTimer(self.timerID)
        return self.ready or not self.timeout

    def signalCaught(self):
        self.ready = True

    def timerEvent(self, event):
        self.killTimer(self.timerID)
        self.timeout = True
        
class History(QAbstractListModel):

    def __init__(self, parent=None, items=[]):
        QAbstractListModel.__init__(self, None)
        self.__HIST = items
        self.__index = 0

    def update(self, items):
        if len(items) > 0:
            rows = len(items)#.count()
            position = self.rowCount()
            self.insertRows(position, rows, QModelIndex())
            good = 0
            for count, item in enumerate(items):
                inda = self.index(position+good-1, 0)
                indb = self.index(position+good, 0)
                if (not QVariant(item) == self.data(inda, Qt.DisplayRole)) \
                    or (self.rowCount()==0):
                    self.setData(indb, QVariant(item), Qt.EditRole)
                    good += 1
            if not good == count+1:
                self.removeRows(position+good, rows-good, QModelIndex())
            self.__index = self.rowCount()

    def history(self):
        return self.__HIST

    def rowCount(self, parent=QModelIndex()):
        return len(self.__HIST)

    def data(self, index, role):
        # index here is a QModelIndex
        if not index.isValid():
            return QVariant()
        if index.row() >= len(self.__HIST):#.count():
            return QVariant()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.__HIST[index.row()]
        else:
            return QVariant()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return QAbstractItemModel.flags(self, index) | Qt.ItemIsEditable

    def setData(self, index, value, role):
        if index.isValid() and role == Qt.EditRole:
            self.__HIST.pop(index.row())
            self.__HIST.insert(index.row(), value)#replace(index.row(), value)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
            return True
        return False

    def insertRows(self, position, rows, parent):
        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            self.__HIST.insert(position, "")
        self.endInsertRows()
        return True

    def removeRows(self, position, rows, parent):
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        for row in range(rows):
            self.__HIST.pop(position)#removeAt(position)
        self.endRemoveRows()
        return True

    def currentIndex(self):
        return self.__index

    def currentItem(self):
        return self.__HIST[self.__index]

    def next(self):
        if self.currentIndex() < self.rowCount() and self.rowCount() > 0:
            self.__index += 1
        if self.currentIndex() == self.rowCount():
            return QVariant(QString())
        else:
            return self.currentItem()

    def previous(self):
        if  self.currentIndex() > 0 and self.rowCount() > 0:
            self.__index -= 1
        if self.currentIndex() == self.rowCount():
            return QVariant(QString())
        else:
            return self.currentItem()

    def loadHistory(self):
        try:
            fileInfo = QFileInfo()
            fileInfo.setFile(QDir(robjects.r['getwd']()[0]), ".Rhistory")
            fh = QFile(fileInfo.absoluteFilePath())
            if not fh.open(QIODevice.ReadOnly):
                return False
            stream = QTextStream(fh)
            stream.setCodec("UTF-8")
            text = stream.readAll()
            self.update(text.split("\n"))
        except Exception, e:
            return False
        return True

    def saveHistory(self):
        try:
            fileInfo = QFileInfo()
            fileInfo.setFile(QDir(robjects.r['getwd']()[0]), ".Rhistory")
            outFile = open(fileInfo.filePath(), "w")
            for line in self.history():
                outFile.write(line+"\n")
            outFile.flush()
        except:
            return False
        return True
