# -*- coding: utf-8 -*-

from PyQt4.QtCore import (QString, QStringList, SIGNAL, SLOT, QFileInfo,
                          Qt, QVariant, QObject, QModelIndex, QEvent, QSize,
                          QRegExp, )
from PyQt4.QtGui import (QPixmap, QDialog, QLabel, QIcon, QTabWidget,
                         QToolButton, QAction, QWidget, QShortcut, QKeySequence,
                         QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
                         QAbstractItemView, QLineEdit, QGroupBox, QApplication,
                         QTableWidgetItem, QStyleOptionComboBox, QStyle, QPainter,
                         QDialogButtonBox, QTextEdit, QListView,QStackedWidget,
                         QComboBox,QListWidgetItem, QFileDialog, QItemDelegate, 
                         QGridLayout, QButtonGroup, QPen, QLayout, QPalette,
                         QStylePainter, QTreeView, QListWidget, QMessageBox,
                         QSpinBox, QDoubleSpinBox, QRadioButton, QSizePolicy, )

import rpy2.robjects as robjects
import sys, os, resources
from environment import TreeModel,SortFilterProxyModel

class PluginDialog(QDialog):

    def __init__(self, parent=None, name="Plugin"):
        QDialog.__init__(self, parent)
        buttonBox = QDialogButtonBox(QDialogButtonBox.Help|QDialogButtonBox.Apply|QDialogButtonBox.Close)
        applyButton = buttonBox.button(QDialogButtonBox.Apply)
        helpButton = buttonBox.button(QDialogButtonBox.Help)
        self.connect(applyButton, SIGNAL("clicked()"), self.apply)
        self.connect(helpButton, SIGNAL("clicked()"), self.help)
        self.connect(buttonBox, SIGNAL("rejected()"), self.reject)
        self.params = {}
        self.treeView = None
        self.currentPage = None
        self.currentGroup = None
        self.currentColumn = None

        self.contentsWidget = ListWidget()
        self.setWindowIcon(QIcon(":icon"))
        self.contentsWidget.setViewMode(QListView.IconMode)
        self.contentsWidget.setIconSize(QSize(76, 66))
        self.contentsWidget.setMovement(QListView.Static)
        self.contentsWidget.setFixedWidth(106)
        self.contentsWidget.setSpacing(12)
        self.contentsWidget.setVisible(False)

        self.connect(self.contentsWidget,
            SIGNAL("currentItemChanged(QListWidgetItem*, QListWidgetItem*)"),
            self.changePage)

        self.pagesWidget = StackedWidget()
        self.contentsWidget.setCurrentRow(0)

        horizontalLayout = HBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget, 1)

        mainLayout = VBoxLayout()
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addStretch(1)
        mainLayout.addSpacing(12)
        mainLayout.addWidget(buttonBox)

        self.setLayout(mainLayout)
        self.setWindowIcon(QIcon(":icon"))
        self.setWindowTitle("manageR - %s" % name)
        
    def help(self):
        self.emit(SIGNAL("helpRequested()"))

    def parameters(self):
        return self.params

    def show(self):
        self.widgets = self.widgetsList()
        QDialog.show(self)

    def widgetsList(self):
        widgets = []
        pages = self.pagesWidget.children()
        for child in pages:
            for widget in child.children():
                if issubclass(type(widget), QWidget):
                    try:
                        widgets.append(widget)
                    except Exception, err:
                        pass
        return widgets
        
    def addPage(self, name="Main"):
        if name == QString("__default__"):
            name = QString("Main")
        items = self.contentsWidget.findItems(name,Qt.MatchExactly)
        if len(items) > 0:
            item = self.contentsWidget.row(items[0])
            page = self.pagesWidget.widget(item)
        else:
            page = Widget()
            page.setLayout(VBoxLayout())
            self.pagesWidget.addWidget(page)
            self.addIcon(name)
        self.currentPage = page
        if self.pagesWidget.count() > 1:
            self.contentsWidget.setVisible(True)

    def addItem(self, widget):
        try:
            self.currentPage.layout().addWidget(widget)
        except TypeError:
            self.currentPage.layout().addLayout(widget)

    def addIcon(self, page="Main"):
        button = QListWidgetItem()
        if page == "Main":
            button.setIcon(QIcon(":gconf-editor"))
            button.setText("Main")
        elif page == "Configure":
            button.setIcon(QIcon(":preferences-system"))
            button.setText("Configure")
        elif page == "Plot Options":
            button.setIcon(QIcon(":applications-graphics"))
            button.setText("Plot Options")
        else:
            button.setIcon(QIcon(":applications-debugging"))
            button.setText(page)
        button.setTextAlignment(Qt.AlignHCenter)
        button.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.contentsWidget.addItem(button)

    def changePage(self, current, previous):
        if not current:
            current = previous
        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))

    def apply(self):
        params = {}
        for widget in self.widgets:
                try:
                    tmp = widget.parameterValues()
                    params.update(tmp)
                except Exception, err:
                    QMessageBox.warning(self, "manageR Plugin Error", str(err))
                    return
        self.params = params
        self.emit(SIGNAL("pluginOutput(PyQt_PyObject)"), self.params)

class LineStyleDelegate(QItemDelegate):

    def __init__(self, parent = None):
        QItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        data = index.model().data(index, Qt.UserRole)
        if data.isValid() and data.toPyObject() is not None:
            data = data.toPyObject()
            painter.save()
            rect = option.rect
            rect.adjust(+5, 0, -5, 0)
            pen = data
            painter.setPen(pen)
            middle = (rect.bottom() + rect.top()) / 2
            painter.drawLine(rect.left(), middle, rect.right(), middle)
            painter.restore()
        else:
            QItemDelegate.paint(self, painter, option, index)
            painter.drawLine(rect.left(), middle, rect.right(), middle)
            painter.restore()

class LineStyleComboBox(QComboBox):
    def __init__(self, parent = None):
        QComboBox.__init__(self, parent)

    def paintEvent(self, e):
        data = self.itemData(self.currentIndex(), Qt.UserRole)
        if data.isValid() and data.toPyObject() is not None:
            data = data.toPyObject()
            p = QStylePainter(self)
            p.setPen(self.palette().color(QPalette.Text))
            opt = QStyleOptionComboBox()
            self.initStyleOption(opt)
            p.drawComplexControl(QStyle.CC_ComboBox, opt)
            painter = QPainter(self)
            painter.save()
            rect = p.style().subElementRect(QStyle.SE_ComboBoxFocusRect, opt, self)
            rect.adjust(+5, 0, -5, 0)
            pen = data
            painter.setPen(pen)
            middle = (rect.bottom() + rect.top()) / 2
            painter.drawLine(rect.left(), middle, rect.right(), middle)
            painter.restore()
        else:
            QComboBox.paintEvent(self, e)

#class TreeComboBox(QComboBox):
#    def __init__(self, parent=None):
#        QComboBox.__init__(self, parent)
#        self.skipNextHide = False
#        self.setView(QTreeView(self))
#        self.view().viewport().installEventFilter(self)

#    def eventFilter(self, object, event):
#        if (event.type() == QEvent.MouseButtonPress and \
#           object == self.view().viewport()):
#            index = self.view().indexAt(event.pos())
#            if not self.view().visualRect(index).contains(event.pos()):
#                self.skipNextHide = True
#        return False

#    def hidePopup(self):
#        self.setCurrentIndex(self.view().currentIndex().row())
#        if self.skipNextHide:
#            self.skipNextHide = False
#        else:
#            QComboBox.hidePopup(self)
#            
#    def showPopup(self):
#        self.view().setMinimumHeight(200)
#        QComboBox.showPopup(self)

class ComboBox(QWidget):
    def __init__(self, id, text, **kwargs):
        QWidget.__init__(self)
        self.id = id
        self.widget = QComboBox(**kwargs)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.widget, alignment=Qt.AlignRight)
        self.setLayout(hbox)

    def parameterValues(self):
        index = self.widget.currentIndex()
        data = self.widget.itemData(index).toString()
        if not data.isEmpty():
            text = data
        else:
            text = self.widget.currentText()
        return {self.id:text}

class SpinBox(QWidget):
    def __init__(self, id, text, **kwargs):
        QWidget.__init__(self)
        self.id = id
        self.widget = QSpinBox(**kwargs)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.widget)
        self.setLayout(hbox)

    def parameterValues(self):
        return {self.id:self.widget.value()}

class CheckBox(QCheckBox):
    def __init__(self, id, text, **kwargs):
        QCheckBox.__init__(self)
        self.id = id
        self.setText(text)

    def parameterValues(self):
        if self.isChecked():
            value = "TRUE"
        else:
            value = "FALSE"
        return {self.id:value}

class DoubleSpinBox(QWidget):
    def __init__(self, id, text, **kwargs):
        QWidget.__init__(self)
        self.id = id
        self.widget = QDoubleSpinBox(**kwargs)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.widget)
        self.setLayout(hbox)
        self.widget.setMaximum(999999999)
        self.widget.setMinimum(-999999999)

    def parameterValues(self):
        return {self.id:self.widget.value()}

class LineEdit(QWidget):
    def __init__(self, id, text, **kwargs):
        QWidget.__init__(self, **kwargs)
        self.id = id
        self.widget = QLineEdit(**kwargs)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.widget)
        self.setLayout(hbox)

    def parameterValues(self):
        return {self.id:self.widget.text()}

class HBoxLayout(QHBoxLayout):
    def __init__(self, *args, **kwargs):
        QHBoxLayout.__init__(self, *args, **kwargs)
        
    def addItem(self, item):
        try:
            self.addWidget(item)
        except TypeError:
            self.addLayout(item)

    def parameterValues(self):
        return None

class VBoxLayout(QVBoxLayout):
    def __init__(self, *args, **kwargs):
        QVBoxLayout.__init__(self, *args, **kwargs)
        
    def addItem(self, item):
        try:
            self.addWidget(item)
        except TypeError:
            self.addLayout(item)

    def parameterValues(self):
        return None

class GridLayout(QGridLayout):
    def __init__(self, *args, **kwargs):
        QGridLayout.__init__(self, *args, **kwargs)
        
    def addItem(self, item):
        try:
            self.addWidget(item)
        except TypeError:
            self.addLayout(item)

    def parameterValues(self):
        return None

class ListWidget(QListWidget):
    def __init__(self, *args, **kwargs):
        QListWidget.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None

class StackedWidget(QStackedWidget):
    def __init__(self, *args, **kwargs):
        QStackedWidget.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None
    
class Widget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

    def parameterValues(self):
        return None

class VariableTreeBox(QGroupBox):

    class VariableTreeButton(QToolButton):
        def __init__(self, *args, **kwargs):
            QToolButton.__init__(self, *args, **kwargs)
            baseIcon = QIcon(":go-next.svg")
            secondIcon = QIcon(":go-previous.svg")
            self.__icons__ = [baseIcon, secondIcon]
            self.setIcon(baseIcon)
            
        def switchIcon(self):
            self.__icons__.reverse()
            self.setIcon(self.__icons__[0])
            
    def __init__(self, id, name="Choose Variables", model=None):
        QGroupBox.__init__(self)
        if model is None:
            model = TreeModel()
        self.setTitle(name)
        self.setToolTip("<p>Select variables for analysis</p>")
        self.id = id
        self.pairs = {}

        layout = HBoxLayout()
        self.variableTreeView = QTreeView()
        self.variableTreeView.setModel(model)
        self.variableTreeView.setToolTip("Select variables from here")
        self.variableTreeView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.variableTreeView.installEventFilter(self)
        layout.addWidget(self.variableTreeView)
        self.widgetsLayout = VBoxLayout()
        layout.addLayout(self.widgetsLayout)
        self.setLayout(layout)
        
    def addItem(self, widget):
        hbox = HBoxLayout()
        button = self.VariableTreeButton()
        button.setToolTip("Specify variable")
        self.connect(button, SIGNAL("clicked()"), self.move)
        widget.widget.installEventFilter(self)
        hbox.addWidget(button)
        hbox.addWidget(widget)
        self.widgetsLayout.addLayout(hbox)
        self.widgetsLayout.addStretch()
        self.pairs[button] = widget

    def eventFilter(self, object, event):
        if event.type() == QEvent.FocusIn:
            self.switchButton(object)
        return False

    def move(self):
        sender = self.sender()
        receiver = self.pairs[sender]
        path = QString()
        if isinstance(receiver, VariableLineEdit):
            if receiver.widget.text().isEmpty():
                indexes = self.variableTreeView.selectedIndexes()
                if len(indexes) < 1:
                    return
                path = self.variableTreeView.model().parentTree(indexes[0])
            sender.switchIcon()
            receiver.widget.setText(path)
        elif isinstance(receiver, VariableListBox):
            add = self.variableTreeView.hasFocus()
            if add:
                indexes = self.variableTreeView.selectedIndexes()
                paths = [self.variableTreeView.model().parentTree(index) for index in indexes if index.column() == 0]
                receiver.widget.addItems(paths)
            else:
                indexes = receiver.widget.selectedItems()
                for index in indexes:
                    item = receiver.widget.takeItem(receiver.widget.row(index))
                    del item

    def switchButton(self, sender):
        if not isinstance(sender, QLineEdit):
            for key, value in self.pairs.iteritems():
                if value.widget == sender:
                    key.setIcon(QIcon(":go-previous.svg"))
                else:
                    key.setIcon(QIcon(":go-next.svg"))

    def parameterValues(self):
        params = {}
        for button, widget in self.pairs.iteritems():
            params.update(widget.parameterValues())
        return params

class VariableLineEdit(QWidget):
    def __init__(self, id, text):
        QWidget.__init__(self)
        self.widget = QLineEdit()
        self.widget.setToolTip(text)
        self.widget.setReadOnly(True)
        label = QLabel(text)
        label.setBuddy(self.widget)
        vbox = VBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.widget)
        self.setLayout(vbox)
        self.id = id
        
    def parameterValues(self):
        var = self.widget.text()
        if var.isEmpty():
            raise Exception("Error: Missing input variable")
        params = {self.id:var}
        return params

class VariableListBox(QWidget):
    def __init__(self, id, text, sep=","):
        QWidget.__init__(self)
        self.widget = QListWidget()
        self.widget.setToolTip(text)
        self.widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        label = QLabel(text)
        label.setBuddy(self.widget)
        vbox = VBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.widget)
        self.setLayout(vbox)
        self.id = id
        self.sep = sep
        
    def parameterValues(self):
        self.widget.selectAll()
        items = self.widget.selectedItems()
        first = True
        var = QString()
        for item in items:
            if first:
                var.append(item.text())
                first = False
            else:
                var.append("%s%s" % (self.sep, item.text()))
        if var.isEmpty():
            raise Exception("Error: Insufficient number of input variables")
        params = {self.id:var}
        return params

class AxesBox(QGroupBox):

    def __init__(self, id, logscale=False, style=True):
        QGroupBox.__init__(self)
        self.setTitle("Control Axes")
        self.setToolTip("<p>Control if/how axes are drawn</p>")
        self.xAxisCheckBox = QCheckBox("Show X axis")
        self.xAxisCheckBox.setChecked(True)
        self.yAxisCheckBox = QCheckBox("Show Y axis")
        self.yAxisCheckBox.setChecked(True)
        self.id = id
        hbox = HBoxLayout()
        hbox.addWidget(self.xAxisCheckBox)
        hbox.addWidget(self.yAxisCheckBox)
        vbox = VBoxLayout()
        vbox.addLayout(hbox)
        if logscale:
            self.xLogCheckBox = QCheckBox("Logarithmic X axis")
            self.yLogCheckBox = QCheckBox("Logarithmic Y axis")
            hbox = HBoxLayout()
            hbox.addWidget(self.xLogCheckBox)
            hbox.addWidget(self.yLogCheckBox)
            vbox.addLayout(hbox)
        if style:
            self.directionComboBox = QComboBox()
            self.directionComboBox.addItems(["Parallel to axis",
                                             "Horizontal",
                                             "Perpendicualr to axis",
                                             "Vertical"])
            directionLabel = QLabel("Axis label style:")
            directionLabel.setBuddy(self.directionComboBox)
            hbox = HBoxLayout()
            hbox.addWidget(directionLabel)
            hbox.addWidget(self.directionComboBox)
            vbox.addLayout(hbox)
        self.setLayout(vbox)

    def parameterValues(self):
        params = QString()
        try:
            if not self.xAxisCheckBox.isChecked():
                params.append(", xaxt='n'")
            if not self.yAxisCheckBox.isChecked():
                params.append(", yaxt='n'")
        except:
            pass
        try:
            logx = self.xLogCheckBox.isChecked()
            logy = self.yLogCheckBox.isChecked()
            if logx or logy:
                tmp = QString()
                if logx:
                    tmp.append("x")
                if logy:
                    tmp.append("y")
                params.append(", log='%s'" % tmp)
        except:
            pass
        try:
            direction = self.directionComboBox.currentIndex()
            if direction > 0:
                params.append(", las=%s" % str(direction))
        except:
            pass
        return {self.id:params}

class MinMaxBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
        self.setTitle("Adjust scale (min and max)")
        self.setToolTip("<p>Adjust scale (range) of axes "
                            "(leave unchecked to use defaults)</p>")
        self.setCheckable(True)
        self.setChecked(False)
        self.xMinLineEdit = QLineEdit()
        self.xMinLineEdit.setToolTip("<p>Specify minimum X value "
                                "(leave blank to use default)</p>")
        xMinLabel = QLabel("X Min:")
        xMinLabel.setBuddy(self.xMinLineEdit)
        self.xMaxLineEdit = QLineEdit()
        self.xMaxLineEdit.setToolTip("<p>Specify maximum X value "
                                "(leave blank to use default)</p>")
        xMaxLabel = QLabel("X Max:")
        xMaxLabel.setBuddy(self.xMaxLineEdit)
        self.yMinLineEdit = QLineEdit()
        self.yMinLineEdit.setToolTip("<p>Specify minimum Y value "
                                "(leave blank to use default)</p>")
        yMinLabel = QLabel("Y Min:")
        yMinLabel.setBuddy(self.yMinLineEdit)
        self.yMaxLineEdit = QLineEdit()
        self.yMaxLineEdit.setToolTip("<p>Specify maximum Y value "
                                "(leave blank to use default)</p>")
        yMaxLabel = QLabel("Y Max:")
        yMaxLabel.setBuddy(self.yMaxLineEdit)
        vbox = VBoxLayout()
        hbox = HBoxLayout()
        hbox.addWidget(xMinLabel)
        hbox.addWidget(self.xMinLineEdit)
        vbox.addLayout(hbox)
        hbox = HBoxLayout()
        hbox.addWidget(xMaxLabel)
        hbox.addWidget(self.xMaxLineEdit)
        vbox.addLayout(hbox)
        box = HBoxLayout()
        box.addLayout(vbox)
        vbox = VBoxLayout()
        hbox = HBoxLayout()
        hbox.addWidget(yMinLabel)
        hbox.addWidget(self.yMinLineEdit)
        vbox.addLayout(hbox)
        hbox = HBoxLayout()
        hbox.addWidget(yMaxLabel)
        hbox.addWidget(self.yMaxLineEdit)
        vbox.addLayout(hbox)
        box.addLayout(vbox)
        self.setLayout(box)

    def parameterValues(self):
        params = QString()
        if self.isChecked():
            xlim1 = self.xMinLineEdit.text()
            xlim2 = self.xMaxLineEdit.text()
            ylim1 = self.yMinLineEdit.text()
            ylim2 = self.yMaxLineEdit.text()
            if (not xlim1.isEmpty() == xlim2.isEmpty()) or \
               (not ylim1.isEmpty() == ylim2.isEmpty()):
                raise Exception("Error: Both min and max values must be specified")
            if not xlim1.isEmpty(): # if one isn't empty, then neither are
                params.append(", xlim=c(%s,%s)" % (xlim1, xlim2))
            if not ylim1.isEmpty(): # if one isn't empty, then neither are
                params.append(", ylim=c(%s,%s)" % (ylim1, ylim2))
        return {self.id:params}

class GridCheckBox(QCheckBox):

    def __init__(self, id):
        QCheckBox.__init__(self)
        self.setText("Add grid to plot")
        self.setToolTip("<p>Check to add grid to plot</p>")
        self.id = id

    def parameterValues(self):
        text = QString()
        if self.isChecked():
            text = "grid()"
        return {self.id:text}

class VariableComboBox(QWidget):

    def __init__(self, id, text="Input data", default=[], model=None):
        QWidget.__init__(self)
        self.setToolTip("<p>Select input dataset</p>")
        self.id = id
        if model is None:
            self.model = TreeModel()
        else:
            self.model = model
        self.comboBox = QComboBox()
        self.treeView = QListView(self.comboBox)
        self.connect(self.comboBox, SIGNAL("currentIndexChanged(int)"), 
            self.changeSelectedText)
        self.proxyModel = SortFilterProxyModel()
        self.proxyModel.setDynamicSortFilter(True)
        self.proxyModel.setFilterKeyColumn(1)
        self.proxyModel.setSourceModel(self.model)
        regexp = QRegExp("|".join([r"%s" % i for i in default]))
        self.proxyModel.setFilterRegExp(regexp)
#        self.treeView.header().hide()
        self.currentText = QString()
        self.treeView.setModel(self.proxyModel)

        self.comboBox.setModel(self.proxyModel)
        self.comboBox.setView(self.treeView)
#        self.treeView.hideColumn(1)
#        self.treeView.hideColumn(2)
#        self.treeView.hideColumn(3)
        self.treeView.viewport().installEventFilter(self.comboBox)
        label = QLabel(text)
        hbox = HBoxLayout()
        hbox.addWidget(label)
        hbox.addWidget(self.comboBox)
        self.setLayout(hbox)
        self.changeSelectedText(None)

    def changeSelectedText(self, index):
        item = self.treeView.currentIndex()
        if not item.isValid():
            item = self.proxyModel.index(0,0, QModelIndex())
        tree = self.treeView.model().parentTree(item)
        self.currentText = tree

    def parameterValues(self):
        return {self.id:self.currentText}

class PlotOptionsWidget(QWidget):

    def __init__(self, id, box=True, titles=True, axes=False,
                 log=False, style=True, minmax=False):
        QWidget.__init__(self)
        button = QToolButton(self)
        button.setText("Additional plot options")
        button.setCheckable(True)
        button.setChecked(False)
        button.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self.widget = Widget()
        vbox = VBoxLayout()
        self.id = id
        if titles:
            vbox.addWidget(TitlesBox(self.id))
        if box:
            vbox.addWidget(BoundingBoxBox(self.id))
        if axes:
            vbox.addWidget(AxesBox(self.id, log, style))
        if minmax:
            vbox.addWidget(MinMaxBox(self.id))
        vbox.setMargin(0)
        self.widget.setLayout(vbox)
        vbox = VBoxLayout()
        vbox.addWidget(button)
        vbox.addWidget(self.widget)
        self.setLayout(vbox)
        self.connect(button, SIGNAL("toggled(bool)"), self.widget.setVisible)
        self.widget.hide()

    def parameterValues(self):
        params = QString()
        for widget in self.widget.children():
            vals = widget.parameterValues()
            if not vals is None:
                params.append(QStringList(vals.values()).join(""))
        return {self.id:params}
        
class RadioGroupBox(QGroupBox):

    class RadioButton(QRadioButton):
        def __init__(self, text, *args, **kwargs):
            QRadioButton.__init__(self, *args, **kwargs)
            self.setText(text)

        def parameterValues(self):
            if self.isChecked():
                return self.text()
            else:
                return None

    def __init__(self, id, *args, **kwargs):
        QGroupBox.__init__(self, *args, **kwargs)
        self.id = id
        vbox = VBoxLayout()
        self.setLayout(vbox)
        self.alternates = []
        
    def addButton(self, name, alternate=None):
        if alternate is None:
            alternate = name
        self.alternates.append(name)
        button = self.RadioButton(alternate)
        if len(self.children()) == 1:
            button.setChecked(True)
        self.layout().addWidget(button)
        
    def parameterValues(self):
        params = QString()
        count = 0
        for widget in self.findChildren(self.RadioButton):
            if widget.isChecked():
                return {self.id:self.alternates[count]}
            count += 1
        
class GroupCheckBox(QGroupBox):

    def __init__(self, id, default=False, *args, **kwargs):
        QGroupBox.__init__(self, *args, **kwargs)
        self.id = id
        vbox = VBoxLayout()
        self.setLayout(vbox)
        self.setCheckable(True)
        self.setChecked(default)
        
    def addItem(self, item):
        try:
            self.addWidget(item)
        except TypeError:
            self.layout().addLayout(item)
        
    def addWidget(self, widget):
        self.layout().addWidget(widget)
        
    def parameterValues(self):
        val = "FALSE"
        if self.isChecked():
            val = "TRUE"
        params = {self.id:val}
        for widget in self.children():
            dic = widget.parameterValues()
            if isinstance(dic, dict):
                params.update(dic)
        return params
        
class GroupBox(QGroupBox):

    def __init__(self, id, *args, **kwargs):
        QGroupBox.__init__(self, *args, **kwargs)
        self.id = id
        vbox = VBoxLayout()
        self.setLayout(vbox)

    def addItem(self, item):
        try:
            self.addWidget(item)
        except TypeError:
            self.layout().addLayout(item)
        
    def addWidget(self, widget):
        self.layout().addWidget(widget)
        
    def parameterValues(self):
        params = {}
        for widget in self.children():
            dic = widget.parameterValues()
            if isinstance(dic, dict):
                params.update(dic)
        return params

class LineStyleBox(QWidget):

    def __init__(self, id, text=None):
        QWidget.__init__(self)
        self.id = id
        self.setToolTip("<p>Adjust line style (leave "
                            "unchecked to use default)</p>")
        hbox = HBoxLayout()
        self.penStyleComboBox = LineStyleComboBox()
        self.penStyleComboBox.setToolTip("Choose line style")
        self.penStyleComboBox.addItem("solid", QPen(Qt.black, 2, Qt.SolidLine))
        self.penStyleComboBox.addItem("dashed", QPen(Qt.black, 2, Qt.DashLine))
        self.penStyleComboBox.addItem("dotted", QPen(Qt.black, 2, Qt.DotLine))
        self.penStyleComboBox.addItem("dotdash", QPen(Qt.black, 2, Qt.DashDotLine))
        pen = QPen(Qt.black, 2, Qt.SolidLine)
        pen.setStyle(Qt.CustomDashLine)
        pen.setDashPattern([5, 2, 5, 2])
        self.penStyleComboBox.addItem("twodash", pen)
        pen.setDashPattern([3, 2, 5, 2])
        self.penStyleComboBox.addItem("twodash", pen)
        self.penStyleComboBox.addItem("blank", QPen(Qt.black, 2, Qt.NoPen))
        delegate = LineStyleDelegate(self)
        self.penStyleComboBox.setItemDelegate(delegate)
        label = QLabel()
        if text is None:
            label.setText("Adjust line style")
        else:
            label.setText(text)
        hbox.addWidget(label)
        hbox.addWidget(self.penStyleComboBox)
        self.setLayout(hbox)

    def parameterValues(self):
        params = QString()
#        if self.isChecked():
        params = "%s" % str(self.penStyleComboBox.currentText())
        return {self.id:params}

class BoundingBoxBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
        self.setTitle("Adjust bounding box")
        self.setToolTip("<p>Adjust plot bounding box (leave "
                            "unchecked to use default)</p>")
        self.setCheckable(True)
        self.setChecked(False)
        self.buttonGroup = QButtonGroup(self)
        self.buttonNames = []
        hbox = HBoxLayout()
        id = 0
        button = QToolButton()
        button.setToolTip("Outline")
        self.buttonNames.append("o")
        button.setIcon(QIcon(":custom-chart-outline.svg"))
        button.setCheckable(True)
        button.setChecked(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("L shape")
        self.buttonNames.append("l")
        button.setIcon(QIcon(":custom-chart-l-shape.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("7 shape")
        self.buttonNames.append("7")
        button.setIcon(QIcon(":custom-chart-7-shape.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("C shape")
        self.buttonNames.append("c")
        button.setIcon(QIcon(":custom-chart-c-shape.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("U shape")
        self.buttonNames.append("u")
        button.setCheckable(True)
        button.setIcon(QIcon(":custom-chart-u-shape.svg"))
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("] shape")
        self.buttonNames.append("]")
        button.setIcon(QIcon(":custom-chart-]-shape.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("None")
        self.buttonNames.append("n")
        button.setIcon(QIcon())
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)

        self.setLayout(hbox)

    def parameterValues(self):
        params = QString()
        if self.isChecked():
            params.append(", bty='%s'" % str(self.buttonNames[
                self.buttonGroup.checkedId()]))
        return {self.id:params}

class PlotTypeBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
        self.setTitle("Adjust plot type")
        self.setToolTip("<p>Adjust plot type (leave "
                            "unchecked to use default)</p>")
        self.setCheckable(True)
        self.setChecked(False)
        self.buttonGroup = QButtonGroup(self)
        self.buttonNames = []
        hbox = HBoxLayout()
        id = 0
        button = QToolButton()
        button.setToolTip("Points")
        self.buttonNames.append("p")
        button.setIcon(QIcon(":custom-chart-point.svg"))
        button.setCheckable(True)
        button.setChecked(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Lines")
        self.buttonNames.append("l")
        button.setIcon(QIcon(":custom-chart-line.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Both")
        self.buttonNames.append("b")
        button.setIcon(QIcon(":custom-chart-both.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Overplotted")
        self.buttonNames.append("o")
        button.setIcon(QIcon(":custom-chart-overplotted.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Histogram")
        self.buttonNames.append("h")
        button.setIcon(QIcon(":custom-chart-hist.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("Stair steps")
        self.buttonNames.append("s")
        button.setIcon(QIcon(":custom-chart-stairs.svg"))
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)
        id += 1
        button = QToolButton()
        button.setToolTip("No plotting")
        self.buttonNames.append("n")
        button.setIcon(QIcon())
        button.setCheckable(True)
        self.buttonGroup.addButton(button, id)
        hbox.addWidget(button)

        self.setLayout(hbox)

    def parameterValues(self):
        params = QString()
        if self.isChecked():
            params = "'%s'" % str(self.buttonNames[
                self.buttonGroup.checkedId()])
        return {self.id:params}

class TitlesBox(QGroupBox):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
        self.setTitle("Custom titles and axis labels")
        self.setToolTip("<p>Specify custom plot titles "
                        "and axis labels (leave unchecked to use defaults</p>")
        self.setCheckable(True)
        self.setChecked(False)
        gbox = GridLayout()
        self.mainLineEdit = QLineEdit()
        self.mainLineEdit.setToolTip("<p>Specify text for title above "
                                     "plot (leave blank for no text)</p>")
        label = QLabel("Main title:")
        label.setBuddy(self.mainLineEdit)
        gbox.addWidget(label,0,0)
        gbox.addWidget(self.mainLineEdit,0,1)

        self.subLineEdit = QLineEdit()
        self.subLineEdit.setToolTip("<p>Specify text for title below "
                                     "plot (leave blank for no text)</p>")
        label = QLabel("Sub title:")
        label.setBuddy(self.subLineEdit)
        gbox.addWidget(label,1,0)
        gbox.addWidget(self.subLineEdit,1,1)

        self.xlabLineEdit = QLineEdit()
        self.xlabLineEdit.setToolTip("<p>Specify text for X axis (leave "
                                     "blank for no text)</p>")
        label = QLabel("X label:")
        label.setBuddy(self.xlabLineEdit)
        gbox.addWidget(label,2,0)
        gbox.addWidget(self.xlabLineEdit,2,1)

        self.ylabLineEdit = QLineEdit()
        self.ylabLineEdit.setToolTip("<p>Specify text for Y axis (leave "
                                     "blank for no text)</p>")
        label = QLabel("Y label:")
        label.setBuddy(self.ylabLineEdit)
        gbox.addWidget(label,3,0)
        gbox.addWidget(self.ylabLineEdit,3,1)

        vbox = VBoxLayout()
        self.setLayout(gbox)

    def parameterValues(self):
        params = QString()
        if self.isChecked():
            params.append(", main='%s'" % self.mainLineEdit.text())
            params.append(", sub='%s'" % self.subLineEdit.text())
            params.append(", xlab='%s'" % self.xlabLineEdit.text())
            params.append(", ylab='%s'" % self.ylabLineEdit.text())
        return {self.id:params}

class ParametersBox(QWidget):

    def __init__(self, id):
        QGroupBox.__init__(self)
        self.id = id
        self.setToolTip("<p>Add/adjust plotting parameters.</p>")
        hbox = HBoxLayout()
        label = QLabel("Additional parameters:")
        self.parameterLineEdit = QLineEdit()
        self.parameterLineEdit.setToolTip("<p>Enter additional (comma separated) "
                                      "parameter=value pairs here</p>")
        hbox.addWidget(label)
        hbox.addWidget(parameterLineEdit)
        self.setLayout(hbox)

    def parameterValues(self):
        params = QString()
        params = self.parameterLineEdit.text().trimmed()
        return {self.id:params}
        
class FileOpenLineEdit(QWidget):

    def __init__(self, id, text="Input file:"):
        QWidget.__init__(self)
        self.id = id
        
        label = QLabel(text)
        self.pathLineEdit = QLineEdit()
        self.pathLineEdit.setToolTip("<p>Enter Input file path here</p>")
        
        button = QToolButton(self)
        button.setToolTip("Browse to existing file")
        button.setWhatsThis("Browse to existing file")
        button.setIcon(QIcon(":document-open.svg"))
        button.setText("...")
        button.setAutoRaise(True)

        horiz = HBoxLayout()
        horiz.addWidget(label)
        horiz.addWidget(self.pathLineEdit)
        horiz.addWidget(button)
        self.connect(button, SIGNAL("clicked()"), self.browseToFolder)
        self.setLayout(horiz)

    def browseToFolder(self):
        f = QFileDialog.getOpenFileName(
        self.parent(), "Specify input file",self.pathLineEdit.text())
        if not f.isEmpty():
            self.pathLineEdit.setText(f)
            
    def parameterValues(self):
        if self.isEnabled() and self.pathLineEdit.text().isEmpty():
            raise Exception("Error: Missing input path")
        params = QString()
        params = self.pathLineEdit.text().trimmed()
        return {self.id:params}
        
class FileSaveLineEdit(QWidget):

    def __init__(self, id, text="Output file:"):
        QWidget.__init__(self)
        self.id = id
        
        label = QLabel(text)
        self.pathLineEdit = QLineEdit()
        self.pathLineEdit.setToolTip("<p>Enter output file path here</p>")
        
        button = QToolButton(self)
        button.setToolTip("Browse to new file")
        button.setWhatsThis("Browse to new file")
        button.setIcon(QIcon(":document-new.svg"))
        button.setText("...")
        button.setAutoRaise(True)

        horiz = HBoxLayout()
        horiz.addWidget(label)
        horiz.addWidget(self.pathLineEdit)
        horiz.addWidget(button)
        self.connect(button, SIGNAL("clicked()"), self.browseToFolder)
        self.setLayout(horiz)

    def browseToFolder(self):
        f = QFileDialog.getSaveFileName(
        self.parent(), "Specify output file",self.pathLineEdit.text())
        if not f.isEmpty():
            self.pathLineEdit.setText(f)
            
    def parameterValues(self):
        if self.isEnabled() and self.pathLineEdit.text().isEmpty():
            raise Exception("Error: Missing output path")
        params = QString()
        params = self.pathLineEdit.text().trimmed()
        return {self.id:params}

def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    robjects.r.load(".RData")
    window = PluginDialog(None)
    window.addWidget(ModelBuilderBox(0))
    window.addWidget(PlotTypeBox(), "main")
    window.addWidget(PlotOptionsWidget(True, True, True, True, True, True), "plotoptions")
    window.addWidget(CheckBox(id=1, text="Some text goes here"), "configure")
    window.addWidget(CheckBox(id=2, text="Some more text goes here"), "configure")
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
