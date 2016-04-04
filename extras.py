# -*- coding: utf-8 -*-
class TreeItem(QObject):

    def __init__(self, data=[], parent=None):
        QObject.__init__(self)
        self.parentItem = parent
        self.itemData = data
        self.childItems = []

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def childNumber(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

    def columnCount(self):
        return len(self.itemData)

    def data(self, column):
        return self.itemData[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > len(self.childItems):
            return False
        for i in range(count):
            item = TreeItem(self.data(columns), self)
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
            self.childItems.remove(position)
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

    def __init__(self, headers, data, parent):
        QAbstractItemModel.__init__(self, parent)
        self.rootData = headers
        self.rootItem = TreeItem(self.rootData)
        self.setupModelData(data.split(QString("\n")), self.rootItem)

    def columnCount(self, index):
        return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        if not role in (Qt.DisplayRole, Qt.EditRole):
            return QVariant()
        item = self.getItem(index)
        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return False
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def getItem(self, index):
        if index.isValid():
            item = TreeItem(index.internalPointer())
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
        success = parentItem.insertChildren(position, rows, rootItem.columnCount())
        self.endInsertRows()
        return success

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        childItem = self.getItem(index)
        parentItem = childItem.parent()
        if parentItem == rootItem:
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
        return success

    def rowCount(self, parent):
        parentItem = self.getItem(parent)
        return parentItem.childCount()

    def setData(self, index, value, role):
        if not role == Qt.EditRole:
            return False
        item = self.getItem(index)
        result = item.setData(index.column(), value)
        if result:
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
        return result

    def setHeaderData(self, section, orientation, value, role):
        if not role == Qt.EditRole or not orientation == Qt.Horizontal:
            return False
        result = self.rootItem.setData(section, value)
        if result:
            self.emit(SIGNAL("headerDataChanged(Qt.Orientation, int, int)"), orientation, section, section)
        return result

    def setupModelData(self, lines, parent):
