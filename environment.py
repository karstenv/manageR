# -*- coding: utf-8 -*-

# rpy2 (R) imports
import rpy2.robjects as robjects
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import sys, resources

# -*- coding: utf-8 -*-
class Node(QObject):

    def __init__(self, data=[], parent=None):
        QObject.__init__(self)
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        try:
            return self.childItems[row]
        except:
            return None

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

    def children(self):
        return [self.child(row) for row in range(self.childCount())]

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        return self.itemData[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False
        for i in range(count):
            item = Node([self.data(i) for i in range(self.columnCount())], self)
            self.childItems.insert(position, item)

    def insertColumns(self, position, columns):
        if position < 0 or position > len(self.itemData):
            return False
        for column in range(columns):
            self.itemData.insert(position, QVariant())
        for child in self.childItems:
            child.insertColumns(position, columns)
        return True

    def parent(self):
        return self.parentItem

    def removeChildren(self, position, count):
        if position < 0 or position+count > len(self.childItems):
            return False
        for row in range(count):
            self.childItems.pop(position)
        return True

    def removeColumns(self, position, columns):
        if position < 0 or position+columns > len(self.itemData):
            return False
        for column in range(columns):
            self.itemData.remove(position)
        for item in self.childItems:
            item.removeColumns(position, columns)
        return True

    def setData(self, column, value):
        if column < 0 or column >= len(self.itemData):
            return False
        self.itemData[column] = value
        return True

class TreeModel(QAbstractItemModel):

    def __init__(self, headers=["Name", "Type", "Size", "Memory"], parent=None):
        QAbstractItemModel.__init__(self, parent)
        self.rootData = headers
        self.rootItem = Node(self.rootData)
        self.browseEnv(self.rootItem)

    def columnCount(self, index):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        item = self.getItem(index)
        if role == Qt.DecorationRole:
            if index.column() == 0:
                return self.getIcon(item.data(1))
        if not role in (Qt.DisplayRole, Qt.EditRole):
            return QVariant()
        return item.data(index.column())
        
    def getIcon(self, type):
        if type in ("data.frame", "table"):
            return QIcon(":custom-data-frame")
        elif type in ("vector", "numeric", "double", 
                      "interger", "complex", "real"):
            return QIcon(":custom-numeric")
        elif type in ("SpatialGridDataFrame", "SpatialPixelsDataFrame"):
            return QIcon(":custom-raster")
        elif QString(type).startsWith("Spatial"):
            return QIcon(":custom-vector")
        elif type in ("factor", "ordered"):
            return QIcon(":custom-factor")
        elif type in ("character"):
            return QIcon(":custom-character")
        elif type in ("matrix"):
            return QIcon(":custom-matrix")
        elif type in ("list"):
            return QIcon(":custom-list")
        elif type in ("function"):
            return QIcon(":custom-function")
        elif type in ("logical"):
            return QIcon(":custom-logical")
        else:
            return QIcon(":application-default-icon")

    def flags(self, index):
        if not index.isValid():
            return False
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item
        return self.rootItem

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(section)
        return QVariant()

    def index(self, row, column, parent):
        if parent.isValid() and not parent.column() == 0:
            return QModelIndex()
        parentItem = self.getItem(parent)
        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def insertColumns(self, position, columns, parent):
        success = False
        self.beginInsertColumns(parent, position, position+columns-1)
        success = self.rootItem.insertColumns(position, columns)
        self.endInsertColumns()
        return success

    def insertRows(self, position, rows, parent):
        parentItem = self.getItem(parent)
        success = False
        self.beginInsertRows(parent, position, position+rows-1)
        success = parentItem.insertChildren(position, rows, self.rootItem.columnCount())
        self.endInsertRows()
        return success

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = self.getItem(index)
        parentItem = childItem.parent()
        if parentItem == self.rootItem or parentItem is None:
            return QModelIndex()
        return self.createIndex(parentItem.childNumber(), 0, parentItem)

    def removeColumns(self, position, columns, parent):
        success = False
        self.beginRemoveColumns(parent, position, position+columns-1)
        success = self.rootItem.removeColumns(position, columns)
        self.endRemoveColumns()
        if self.rootItem.columnCount() == 0:
            self.removeRows(0, self.rowCount())
        return success

    def removeRows(self, position, rows, parent):
        parentItem = self.getItem(parent)
        success = True
        self.beginRemoveRows(parent, position, position+rows-1)
        success = parentItem.removeChildren(position, rows)
        self.endRemoveRows()
        self.updateData(parentItem, rows)
        return success

    def rowCount(self, parent):
        parentItem = self.getItem(parent)
        return parentItem.childCount()

    def setData(self, index, value):
        item = self.getItem(index)
        result = item.setData(index.column(), value)
        if result:
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        return result

    def setHeaderData(self, section, orientation, value):
        if not orientation == Qt.Horizontal:
            return False
        result = self.rootItem.setData(section, value)
        if result:
            self.emit(SIGNAL("headerDataChanged(Qt.Orientation, int, int)"), orientation, section, section)
        return result

    def updateEntry(self, index):
        item = self.getItem(index)
        for row in range(item.childCount()):
            idx = self.index(row, 0, index)
            objName = self.parentTree(idx)
            obj = robjects.r(objName)
            tmp = self.getItem(idx)
            if tmp.childCount() < 1 and \
               not QString(objName).endsWith("[['call']]"):
                self.browseObject(obj, idx)

    def updateData(self, item, count):
        if item == self.rootItem:
            return
        dim = QString(item.data(2))
        regexp = QRegExp(r"\s\d+")
        index = dim.lastIndexOf(regexp)
        prefix = dim[0:index]
        suffix = int(dim[index:])-count
        item.setData(2, "%s %s" % (prefix, suffix))

    def parentTree(self, index):
        item = self.getItem(index)
        name = QString(item.data(0))
        #name.remove("[[").remove("]]")
        parent = item.parent()
        names = []
        
        while not parent is None:
            tmp = QString(parent.data(0))
            #tmp.remove("[[").remove("]]")
            names.insert(0,tmp)
            parent = parent.parent()
        names.append(name)
        names.pop(0)
#        path = ["[['%s']]" % name if not name.contains(QRegExp(r"\[\[.*\]\]")) 
#            else unicode(name) for name in names[1:]]
        path = [unicode(name) if name.contains(QRegExp(r"\[\[.*\]\]")) \
            or name=="@data" else "[['%s']]" % name for name in names[1:]]
        if len(names) < 1:
            return ""
        return unicode(names[0])+str.join("", path)

    def properties(self, obj, name):
        md = robjects.r.mode(obj)[0]
        lg = robjects.r.length(obj)[0]
        try:
            objdim = list(robjects.r.dim(obj))
            dim = "dim: %s x %s" % (str(objdim[0]),str(objdim[1]))
            if robjects.r["is.matrix"](obj)[0]:
                md = "matrix"
        except TypeError, e:
            dim = "length: %s" % str(lg)
        cls = robjects.r.oldClass(obj)
        if not robjects.r['is.null'](cls)[0]:
            md = cls[0]
            if robjects.r.inherits(obj, "factor")[0]:
                dim = "levels: %s" % robjects.r.length(robjects.r.levels(obj))[0]
        memory = robjects.r.get("object.size", mode="function")
        mem = memory(obj)
        return [name, md, dim, str(mem)]

    def browseObject(self, obj, index):
        lg = robjects.r.length(obj)[0]
        nm = robjects.r.names(obj)
        item = self.getItem(index)
        if item.childCount() > 0:
            return
        if not robjects.r['is.recursive'](obj)[0] or \
            lg < 1 or \
            robjects.r['is.function'](obj)[0] or \
            robjects.r['is.environment'](obj)[0]:
            return
        if robjects.r['is.null'](nm)[0]:
            nm = ["[[%s]]" % str(j+1) for j in range(lg)]
        self.insertRows(0, len(nm), index)
        for i in range(lg):
            dub = robjects.r['[[']
            props = self.properties(dub(obj, i+1), nm[i])
            [self.setData(self.index(i, col, index), val) for col, val in enumerate(props)]

    def browseEnv(self, parent):
        objlist = list(robjects.r.ls())
        ix = objlist.count("last.warning")
        if ix > 0:
            objlist.remove("last.warning")
        n = len(objlist)
        if n == 0: # do nothing!
            return list()
        nodes = []
        for row, objName in enumerate(objlist):
            spatial = False
            obj = robjects.r.get(objName)
            if not robjects.r['is.null'](robjects.r['class'](obj))[0] \
                and robjects.r.inherits(obj, "Spatial")[0]:
                spatClass = robjects.r.oldClass(obj)[0]
                memory = robjects.r.get("object.size", mode="function")
                spatMem = memory(obj)
                obj = robjects.r['@'](obj, 'data')
                objdim = robjects.r.dim(obj)
                spatDim = "features: %s" % (objdim[0])
                props = [objName, spatClass, spatDim, str(spatMem)]
                objName = "@data"
                spatNode = Node(props, parent)
                props = self.properties(obj, objName)
                node = Node(props, spatNode)
                spatNode.appendChild(node)
                parent.appendChild(spatNode)
            else:
                props = self.properties(obj, objName)
                node = Node(props, parent)
                parent.appendChild(node)
            if robjects.r['is.recursive'](obj)[0] \
                and not robjects.r['is.function'](obj)[0] \
                and not robjects.r['is.environment'](obj)[0]:
                lg = robjects.r.length(obj)[0]
                nm = robjects.r.names(obj)
                if robjects.r['is.null'](nm)[0]:
                    nm = ["[[%s]]" % str(j+1) for j in range(lg)]
                for i in range(lg):
                    dub = robjects.r['[[']
                    props = self.properties(dub(obj, i+1), nm[i])
                    node.appendChild(Node(props, node))
            elif not robjects.r['is.null'](robjects.r['class'](obj))[0]:
                if robjects.r.inherits(obj, "table")[0]:
                    nms = robjects.r.attr(obj, "dimnames")
                    lg = robjects.r.length(nms)
                    props = self.properties(obj, objName)
                    node = Node(props, parent)
                    if len(robjects.r.names(nms)) > 0:
                        nm <- robjects.r.names(nms)
                    else:
                        nm = ["" for k in range(lg)]
                    for i in range(lg):
                        dub = robjects.r['[[']
                        node.appendChild(Node(self.properties(dub(obj, i+1), nm[i]), node))
                        parent.appendChild(node)
                elif robjects.r.inherits(obj, "mts")[0]:
                    props = self.properties(obj, objName)
                    node = Node(props, parent)
                    nm = robjects.r.dimnames(obj)[1]
                    lg = len(nm)
                    for k in range(lg):
                        dim = "length: %s" % robjects.r.dim(obj)[0]
                        md = "ts"
                        memory = robjects.r.get("object.size", mode="function")
                        mem = memory(obj)
                        props = [nm[k], md, dim, str(mem)]
                        node.appendChild(Node(props, node))
                        parent.appendChild(node)
                        
class SortFilterProxyModel(QSortFilterProxyModel):
    def __init__(self):
        QSortFilterProxyModel.__init__(self)
        
    def updateEntry(self, index):
        index = self.mapToSource(index)
        return self.sourceModel().updateEntry(index)

    def parentTree(self, index):
        index = self.mapToSource(index)
        return self.sourceModel().parentTree(index)
        
    def getItem(self, index):
        index = self.mapToSource(index)
        return self.sourceModel().getItem(index)
                        
class Widget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        view = QTreeView()
        view.setSortingEnabled(True)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setDynamicSortFilter(True)
        self.proxy.setFilterKeyColumn(1)
        view.setModel(self.proxy)
        hbox = QHBoxLayout()
        hbox.addWidget(view)
        self.setLayout(hbox)
        self.model = TreeModel()
        self.proxy.setSourceModel(self.model)
        
class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        widget = Widget()
        self.setCentralWidget(widget)
        self.model = TreeModel()
        self.centralWidget().proxy.setSourceModel(self.model)
        
def main3():
    robjects.r.load("/home/cfarmer/working/test.RData")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Simple Tree Model")
    window.show()
    app.exec_()
        
def main2():
    robjects.r.load("/home/cfarmer/working/test.RData")
    app = QApplication(sys.argv)
    widget = Widget()
    widget.setWindowTitle("Simple Tree Model")
#    model = TreeModel()
#    widget.proxy.setSourceModel(model)
    widget.show()
    app.exec_()

def main():
    robjects.r.load("/home/cfarmer/working/test.RData")
    app = QApplication(sys.argv)
    view = QTreeView()
    view.setSortingEnabled(True)
    proxy = QSortFilterProxyModel()
    proxy.setDynamicSortFilter(True)
    proxy.setFilterKeyColumn(1)
    view.setModel(proxy)
    view.setWindowTitle("Simple Tree Model")
    model = TreeModel()
    proxy.setSourceModel(model)
#    regexp = QRegExp(r"Spatial.*")
#    proxy.setFilterRegExp(regexp)
    
#    proxy.setSourceModel(model)
    view.show()
    app.exec_()

if __name__ == '__main__':
    main2()
