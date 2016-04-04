from PyQt4.QtCore import *
from PyQt4.QtGui import *
import rpy2.robjects as robjects
import sys, os, time
import rpy2.rlike.container as container
from calculator import CalculatorDialog

def convert(old, value):
    if type(old) == int:
        temp, ok = value.toInt()
        if ok:
            return int(temp)
        return old
    elif type(old) == float:
        temp, ok = value.toDouble()
        if ok:
            return float(temp)
        return old
    elif type(old) == bool:
        return bool(value.toBool())
    if value.toString().isEmpty():
        return old
    return unicode(value.toString())
    
def convert2(L, typeof):
    if typeof == 'Float':
        vector = robjects.FloatVector(L)
    elif typeof == 'Integer':
        vector = robjects.IntVector(L)
    elif typeof == 'Factor':
        vector = robjects.FactorVector(L)
    elif typeof == 'Boolean':
        vector = robjects.BoolVector(L)
    else:
        vector = robjects.StrVector(L)
    return vector
    
class ColumnDialog(QDialog):
    def __init__(self, parent=None, title="Insert New Column", name=None, 
                 typeof=None, param1=(None, 1.00), param2=(None, 0.00)):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        nameLabel = QLabel("Name:")
        typeLabel = QLabel("Type:")
        param1Name = param1[0]
        param1Value = param1[1]
        param2Name = param2[0]
        param2Value = param2[1]
        if not param1Name is None:
            param1Label = QLabel(param1Name)
        if not param2Name is None:
            param2Label = QLabel(param2Name)
        self.nameEdit = QLineEdit()
        self.nameEdit.setText(name)
        self.typeCombobox = QComboBox()
        types = ['Float', 'Integer', 'String', 'Factor', 'Boolean']
        self.typeCombobox.addItems(types)
        try:
            index = types.index(typeof)
        except ValueError:
            index = 0
        self.typeCombobox.setCurrentIndex(index)
        self.param1Spinbox = QDoubleSpinBox()
        self.param1Spinbox.setRange(0.00, 9999.00)
        self.param1Spinbox.setSingleStep(5.00)
        self.param1Spinbox.setValue(param1Value)
        self.param2Spinbox = QDoubleSpinBox()
        self.param2Spinbox.setRange(0.00, 9999.00)
        self.param2Spinbox.setSingleStep(1.00)
        self.param2Spinbox.setValue(param2Value)
        okButton = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel, parent=self)
        grid = QGridLayout(self)
        if not name is None:
            grid.addWidget(nameLabel, 0, 0)
            grid.addWidget(self.nameEdit, 0, 1)
        if not typeof is None:
            grid.addWidget(typeLabel, 1, 0)
            grid.addWidget(self.typeCombobox, 1, 1)
        if not param1Name is None:
            grid.addWidget(param1Label, 2, 0)
            grid.addWidget(self.param1Spinbox, 2, 1)
        if not param2Name is None:
            grid.addWidget(param2Label, 3, 0)
            grid.addWidget(self.param2Spinbox, 3, 1)
        grid.addWidget(okButton, 4, 0, 1, 2)
        self.connect(okButton, SIGNAL("accepted()"), self.accept)
        self.connect(okButton, SIGNAL("rejected()"), self.reject)
    def name(self):
        return self.nameEdit.text()
    def typeof(self):
        return self.typeCombobox.currentText()
    def param1(self):
        return self.param1Spinbox.value()
    def param2(self):
        return self.param2Spinbox.value()

class DataFrameModel(QAbstractTableModel):
    def __init__(self, mobject, parent=None):
        QAbstractTableModel.__init__(self, parent)
        self._mobject = mobject
        # caching these is _significantly_ faster
        self._rownames = self._mobject.rownames
        self._colnames = self._mobject.colnames
        self._ncols = self._mobject.ncol
        self._nrows = self._mobject.nrow
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        if index.row() >= self._nrows or index.row() < 0:
            return QVariant()
        if role == Qt.DisplayRole:
            return self._mobject[index.column()][index.row()]
        elif role == Qt.TextAlignmentRole:
            if type(self._mobject[index.column()][index.row()]) in (int, float):
                return Qt.AlignRight            
        return QVariant()

    def setData(self, index, data, role=Qt.EditRole):
        if index.isValid() and role == Qt.EditRole:
            old = self._mobject[index.column()][index.row()]
            self._mobject[index.column()][index.row()] = convert(old, data)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), index, index)
            return True
        return False

    def headerData(self, section, orientation, role):
        if not role == Qt.DisplayRole:
            return QVariant()
        if orientation == Qt.Horizontal:
            return QVariant(self._colnames[section])
        elif orientation == Qt.Vertical:
            return QVariant(self._rownames[section])
        else:
            return QVariant()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0 # no child
        return self._nrows
        
    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0 # no child
        return self._ncols
        
    def sort(self, col, order=Qt.DescendingOrder):
        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        indexes = robjects.r.order(self._mobject.rx(col+1), 
            decreasing = order == Qt.DescendingOrder)
        self._mobject = self._mobject.rx(indexes, True)
        self._rownames = self._mobject.rownames
        self.emit(SIGNAL("layoutChanged()"))

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable
        
    def dataFrame(self):
        return self._mobject
        
    def removeColumns(self, position, cols, parent=QModelIndex()):
        if cols >= self._ncols:
            return False
        self.beginRemoveColumns(QModelIndex(), position, position+cols-1)
        i = robjects.IntVector([-1*(j+1) for j in range(position, position+cols)])
        self._mobject = self._mobject.rx(i)
        # since we are chaching these values, we need to update manually
        self._ncols -= cols
        self._colnames = self._mobject.colnames
        self.endRemoveColumns()
        return True

    def insertColumns(self, position, cols, parent=QModelIndex(), 
                      columns=[robjects.IntVector(())], names=["V1"]):
        self.beginInsertColumns(QModelIndex(), position, position+cols-1)
        ncols = self._ncols+cols
        temp = [(str(names[i]), columns[i]) for i in range(cols)]
        dframe = robjects.DataFrame(container.OrdDict(temp))
        self._mobject = self._mobject.cbind(dframe)
        if position < self.columnCount()-1: # if it's not going on to the end
            i = robjects.IntVector(range(1,(position+1)+1) +
                                   range((ncols-cols)+1, ncols+1) +
                                   range((position+1)+1,(ncols-cols)+1))
            self._mobject = self._mobject.rx(True, i) 
        self._colnames = self._mobject.colnames
        self._ncols = ncols
        self.endInsertColumns()
        return True
        
    def updateColumn(self, position, col):
        if issubclass(type(col), robjects.Vector):
            self._mobject[position] = col
            top = self.createIndex(0, position)
            bottom = self.createIndex(self._nrows-1, position)
            self.emit(SIGNAL("dataChanged(QModelIndex, QModelIndex)"), top, bottom)
            return True
        return False

    def removeRows(self, position, rows, parent=QModelIndex()):
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        i = robjects.IntVector([-1*(j+1) for j in range(position, position+rows)])
        self._mobject = self._mobject.rx(i, True, drop=False)
        # since we are caching these values, we need to update manually
        self._nrows -= rows
        self._rownames = self._mobject.rownames
        self.endRemoveRows()
        return True
        
    def setHeaderData(self, section, orientation=Qt.Horizontal, value=QVariant(), 
                      role=Qt.EditRole):
        if not section < self._ncols and not section >= 0:
            return False
        if orientation == Qt.Horizontal and role == Qt.EditRole:
            self._mobject.colnames[section] = unicode(value)
            self.emit(SIGNAL("headerDataChanged(Qt.Orientation, int, int)"), 
                      orientation, section, section)
            return True
        return False
        
#    def insertRows(position, rows, parent=QModelIndex(), typeof=float):
#        self.beginInsertRows(QModelIndex(), position, position+rows-1)
#        self.endInsertRows()
#        return True

#    def insertColumns(position, cols, parent=QModelIndex(), typeof=float):
#        self.beginInsertRows(QModelIndex(), position, position+rows-1)
#        self.endInsertRows()
#        return True

class DataFrameDialog(QDialog):

    def __init__(self, mobject, parent=None):
        QDialog.__init__(self, parent)
        self._dataFrame = DataFrameModel(mobject, self)
        self._tableView = QTableView(self)
        self.setupModels()
        extra = self._tableView.verticalHeader().width()
        width = (self._tableView.width()+extra) / self._tableView.horizontalHeader().count()
        for i in xrange(self._tableView.horizontalHeader().count()):
            self._tableView.setColumnWidth(i, width)
        layout = QVBoxLayout(self)
        layout.addWidget(self._tableView)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Cancel, parent=self)
        layout.addWidget(buttons)
        self.connect(buttons, SIGNAL("accepted()"), self.accept)
        self.connect(buttons, SIGNAL("rejected()"), self.reject)
        self.initActions()
        self.initContextMenus()

    def setupModels(self):
        self._tableView.setModel(self._dataFrame)
        self._tableView.horizontalHeader().setDefaultSectionSize(60)
        self._tableView.horizontalHeader().setResizeMode(QHeaderView.Interactive)
        self._tableView.verticalHeader().setResizeMode(QHeaderView.Fixed)
        self._tableView.setEditTriggers(QAbstractItemView.DoubleClicked)
        self._tableView.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self._tableView.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.connect(self._tableView.selectionModel(),
            SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),
            self, SIGNAL("selectionChanged(QItemSelection)"))

    def writeToFile(self, fileName):
        self._tableView.model().dataFrame().to_csvfile(fileName, quote=True, 
            sep=',', eol='\n', na='NA', dec='.', row_names=True, 
            col_names=True, qmethod='escape', append=False)
            
    def accept(self):
        if self._tableView.editTriggers() == QAbstractItemView.NoEditTriggers:
            return QDialog.accept(self)
        else:
            return None

    def gotoCell(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Goto cell")
        rowLabel = QLabel("Row:")
        colLabel = QLabel("Col:")
        rowSpinbox = QSpinBox(dialog)
        rowSpinbox.setRange(1, self._tableView.verticalHeader().count())
        colSpinbox = QSpinBox(dialog)
        colSpinbox.setRange(1, self._tableView.horizontalHeader().count())
        okButton = QDialogButtonBox(QDialogButtonBox.Ok, parent=dialog)
        grid = QGridLayout(dialog)
        grid.addWidget(rowLabel, 0, 0)
        grid.addWidget(rowSpinbox, 0, 1)
        grid.addWidget(colLabel, 1, 0)
        grid.addWidget(colSpinbox, 1, 1)
        grid.addWidget(okButton, 2, 0, 1, 2)
        dialog.connect(okButton, SIGNAL("accepted()"), dialog.close)
        dialog.exec_()
        index = self._tableView.model().index(rowSpinbox.value()-1, colSpinbox.value()-1)
        self._tableView.scrollTo(index)
        self._tableView.setCurrentIndex(index)

    def selectAll(self):
        self._tableView.selectAll()

    def clearSelection(self):
        self._tableView.clearSelection()
        
    def removeColumns(self):
        indexes = self._tableView.selectionModel().selectedColumns()
        if len(indexes) < 1:
            index = self._tableView.horizontalHeader().currentIndex()
            if not index.isValid():
                return False
            indexes = [index]
        first = indexes[0]
        self._tableView.model().removeColumns(first.column(), len(indexes), QModelIndex())
        return True
        
    def removeRows(self):
        indexes = self._tableView.selectionModel().selectedRows()
        if len(indexes) < 1:
            index = self._tableView.verticalHeader().currentIndex()
            if not index.isValid():
                return False
            indexes = [index]
        first = indexes[0]
        self._tableView.model().removeRows(first.row(), len(indexes), QModelIndex())
        return True
        
    def renameColumn(self):
        index = self._tableView.horizontalHeader().currentIndex()
        if not index.isValid():
            return False
        name, ok = QInputDialog.getText(self, "Rename column", "Column name:", 
                   text=self._tableView.model()._colnames[index.column()])
        if ok and not name.isEmpty():
            self._tableView.model().setHeaderData(index.column(), value=unicode(name))
        return True
        
    def sortAscending(self):
        index = self._tableView.horizontalHeader().currentIndex()
        if not index.isValid():
            return False        
        self._tableView.model().sort(index.column(), Qt.AscendingOrder)
        
    def sortDescending(self):
        index = self._tableView.horizontalHeader().currentIndex()
        if not index.isValid():
            return False        
        self._tableView.model().sort(index.column(), Qt.DescendingOrder)
        
    def insertColumn(self):
        index = self._tableView.horizontalHeader().currentIndex()
        name = "V%s" % self._tableView.horizontalHeader().count()
        dialog = ColumnDialog(self, name=name, typeof="Float", subset=False)
        result = dialog.exec_()
        if result:
            temp = [0]*self._tableView.model().rowCount()
            colClass = dialog.typeof()
            colName = dialog.name()
            vector = convert2(temp, colClass)
            self._tableView.model().insertColumns(index.column(), 1, QModelIndex(), [vector], [colName])
            return True
        return False
        
    def uniqueColumn(self):
        index = self._tableView.horizontalHeader().currentIndex()
        name = "UID%s" % self._tableView.horizontalHeader().count()
        dialog = ColumnDialog(self, title="Insert Unique Id Column", name=name)
        result = dialog.exec_()
        if result:
            colName = dialog.name()
            rowCount = self._tableView.model().rowCount()
            vector = robjects.IntVector(range(1, rowCount+1))
            self._tableView.model().insertColumns(index.column(), 1, QModelIndex(), [vector], [colName])
            return True
        return False
        
    def randomColumn(self):
        index = self._tableView.horizontalHeader().currentIndex()
        name = "R%s" % self._tableView.horizontalHeader().count()
        dialog = ColumnDialog(self, title="Insert Random Column", name=name, 
                              param1=("Min:", 0.0), param2=("Max:", 1.0))
        result = dialog.exec_()
        if result:
            colName = dialog.name()
            minVal = dialog.param1()
            maxVal = dialog.param2()
            rowCount = self._tableView.model().rowCount()
            vector = robjects.FloatVector(robjects.r.runif(rowCount, minVal, maxVal))
            self._tableView.model().insertColumns(index.column(), 1, 
                                                  QModelIndex(), [vector], [colName])
            return True
        return False
        
    def shuffleColumn(self):
        index = self._tableView.horizontalHeader().currentIndex()
        vector = robjects.r.sample(self._tableView.model().dataFrame()[index.column()])
        self._tableView.model().updateColumn(index.column(), vector)
        return True
        
    def fieldCalculator(self):
        calculator = CalculatorDialog(self._tableView.model().dataFrame(), self)
        if calculator.exec_():
            text = calculator.mExpressionTextEdit.toPlainText()
            expression = robjects.r.parse(text=unicode(text), n=1, encoding="UTF-8")
            vector = robjects.r['with'](self._tableView.model().dataFrame(), expression)
            if calculator.mUpdateExistingFieldCheckBox.checkState() == Qt.Checked:
                targetField = calculator.mExistingFieldComboBox.currentIndex()
                self._tableView.model().updateColumn(targetField, vector)
            else: # create new field
                targetField = calculator.mOutputFieldNameLineEdit.text()
                self._tableView.model().insertColumns(
                    self._tableView.model().columnCount(), 1, QModelIndex(),
                    columns=[vector], names=[targetField])

    def initActions(self):
        self.fieldCalculatorAction = QAction("Calculator",  self)
        self.addAction(self.fieldCalculatorAction)
        self.connect(self.fieldCalculatorAction, SIGNAL("triggered()"), self.fieldCalculator)

        self.renameColumnAction = QAction("Rename Column",  self)
        self.addAction(self.renameColumnAction)
        self.connect(self.renameColumnAction, SIGNAL("triggered()"), self.renameColumn)

        self.removeColumnAction = QAction("Delete Column(s)",  self)
        self.addAction(self.removeColumnAction)
        self.connect(self.removeColumnAction, SIGNAL("triggered()"), self.removeColumns)
        
        self.insertColumnAction = QAction("Empty Column",  self)
        self.addAction(self.insertColumnAction)
        self.connect(self.insertColumnAction, SIGNAL("triggered()"), self.insertColumn)
        
        self.uniqueColumnAction = QAction("Unique IDs",  self)
        self.addAction(self.uniqueColumnAction)
        self.connect(self.uniqueColumnAction, SIGNAL("triggered()"), self.uniqueColumn)
        
        self.randomColumnAction = QAction("Random Values",  self)
        self.addAction(self.randomColumnAction)
        self.connect(self.randomColumnAction, SIGNAL("triggered()"), self.randomColumn)
        
        self.shuffleColumnAction = QAction("Resample",  self)
        self.addAction(self.shuffleColumnAction)
        self.connect(self.shuffleColumnAction, SIGNAL("triggered()"), self.shuffleColumn)
        
        self.removeRowAction = QAction("Delete Row(s)",  self)
        self.addAction(self.removeRowAction)
        self.connect(self.removeRowAction, SIGNAL("triggered()"), self.removeRows)

        self.clearSelectionAction = QAction("Clear Selection",  self)
        self.addAction(self.clearSelectionAction)
        self.connect(self.clearSelectionAction, SIGNAL("triggered()"), self.clearSelection)

        self.selectAllAction = QAction("Select All",  self)
        self.addAction(self.selectAllAction)
        self.connect(self.selectAllAction, SIGNAL("triggered()"), self.selectAll)

        self.gotoCellAction = QAction("Go to cell",  self)
        self.addAction(self.gotoCellAction)
        self.connect(self.gotoCellAction, SIGNAL("triggered()"), self.gotoCell)
        
        self.sortDescendingAction = QAction("Descending",  self)
        self.addAction(self.sortDescendingAction)
        self.connect(self.sortDescendingAction, SIGNAL("triggered()"), self.sortDescending)
        
        self.sortAscendingAction = QAction("Ascending",  self)
        self.addAction(self.sortAscendingAction)
        self.connect(self.sortAscendingAction, SIGNAL("triggered()"), self.sortAscending)

    def initContextMenus(self):
        self._tableView.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self._tableView.verticalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.connect(self._tableView.horizontalHeader(), 
                     SIGNAL("customContextMenuRequested(QPoint)"),
                     self.horizontalHeaderContext)
        self.connect(self._tableView.verticalHeader(), 
                     SIGNAL("customContextMenuRequested(QPoint)"),
                     self.verticalHeaderContext)
                     
    def horizontalHeaderContext(self, point):
        col = self._tableView.horizontalHeader().logicalIndexAt(point)
        index = self._tableView.model().createIndex(0,col)
        self._tableView.horizontalHeader().selectionModel().setCurrentIndex(index, 
                                                   QItemSelectionModel.NoUpdate)
        menu = QMenu("Header Menu", self)
        menu.addAction(self.fieldCalculatorAction)
        insert = QMenu("Insert...", self)
        insert.addAction(self.insertColumnAction)
        insert.addAction(self.uniqueColumnAction)
        insert.addAction(self.randomColumnAction)
        menu.addMenu(insert)
        menu.addSeparator()
        menu.addAction(self.removeColumnAction)
        menu.addAction(self.renameColumnAction)
        menu.addSeparator()
        menu.addAction(self.clearSelectionAction)
        menu.addAction(self.selectAllAction)
        menu.addSeparator()
        menu.addAction(self.gotoCellAction)
        sort = QMenu("Sort...", self)
        sort.addAction(self.sortDescendingAction)
        sort.addAction(self.sortAscendingAction)
        menu.addMenu(sort)
        menu.addAction(self.shuffleColumnAction)
        menu.exec_(self.mapToGlobal(point))
        
    def verticalHeaderContext(self, point):
        row = self._tableView.verticalHeader().logicalIndexAt(point)
        index = self._tableView.model().createIndex(row, 0)
        self._tableView.verticalHeader().selectionModel().setCurrentIndex(index, 
                                                   QItemSelectionModel.NoUpdate)
        menu = QMenu("Row Menu", self)
        menu.addAction(self.removeRowAction)
        menu.addSeparator()
        menu.addAction(self.clearSelectionAction)
        menu.addAction(self.selectAllAction)
        menu.addSeparator()
        menu.addAction(self.gotoCellAction)
        menu.exec_(self.mapToGlobal(point))

             
def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    app.setApplicationName("test-table")
    app.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))
    robjects.r.load('test_large.Rdata')
    data = robjects.r['white.collar.data']
    table = DataFrameDialog(data, None)
    table.setWindowTitle("DataFrame Viewer")
#    table.connect(dialog, SIGNAL("accepted()"), table.saveDataFrame)
    table.show()
    app.exec_()
    
if __name__ == "__main__":
#    import profile
#    profile.run("main()")
    main()
