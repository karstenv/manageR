# -*- coding: utf-8 -*-
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import * 
from PyQt4.QtGui import *
from PyQt4.QtXml import *
#from PyQt4.QtSql import *
#from qgis.core import *
import sys, os, resources
from plugins_dialog import (SpinBox, DoubleSpinBox, ComboBox, CheckBox, LineEdit, 
                            VariableLineEdit, VariableListBox, HBoxLayout,
                            AxesBox, MinMaxBox, PlotOptionsWidget, LineStyleBox,
                            BoundingBoxBox, PlotTypeBox, TitlesBox, ParametersBox,
                            PluginDialog, Widget, VariableComboBox, GridCheckBox,
                            RadioGroupBox, GroupBox, RadioGroupBox, VBoxLayout,
                            VariableTreeBox, GroupCheckBox, FileSaveLineEdit,
                            FileOpenLineEdit)
CURRENTDIR = unicode(os.path.abspath(os.path.dirname(__file__)))

class ToolsCollection:
    def __init__(self, category="__default__"):
        self.__tools__ = []
        self.__category__ = QString(category)
        
    def addTool(self, tool):
        if isinstance(tool, Tool):
            self.__tools__.append(tool)
        else:
            raise Exception("Error: Expected type Tool")
            
    def tools(self):
        return self.__tools__
        
    def setCategory(self, category):
        if isinstance(category, QString):
            self.__category__ = category
        else:
            raise Exception("Error: Expected type QString")

    def category(self):
        return self.__category__
        
    def currentTool(self):
        return self.__tools__[-1]

class Tool:
    def __init__(self, name="__default__", query=None,
                       help=None, icon=None, dialog=None):
        self.__query__ = None
        self.__help__ = None
        if dialog is None:
            self.__dialog__ = Dialog()
        self.__name__ = name
        self.__sub__= None
        self.__icon__ = QIcon(":system-run.svg")
        
    def setName(self, name):
        if not isinstance(name, QString):
            raise TypeError("Error: Expected type QString")
        self.__name__ = name
        
    def name(self):
        return self.__name__
        
    def setIcon(self, icon):
        if not isinstance(icon, QString):
            raise TypeError("Error: Expected type QString")
        self.__icon__ = icon.trimmed()
        
    def icon(self):
        return self.__icon__

    def setDialog(self, dialog):
        if not isinstance(dialog, Dialog):
            raise TypeError("Error: Expected type list")
        self.__dialog__ = dialog
        
    def dialog(self):
        return self.__dialog__
        
    def setQuery(self, query):
        if not isinstance(query, QString):
            raise TypeError("Error: Expected type QString")
        self.__query__ = query.trimmed()
            
    def query(self):
        return self.__query__
        
    def setHelp(self, help):
        if not isinstance(help, QString):
            raise TypeError("Error: Expected type QString")
        self.__help__ = help.trimmed()
            
    def help(self):
        return self.__help__
        
    def setSubcategory(self, sub):
        if not isinstance(sub, QString):
            raise TypeError("Error: Expected type QString")
        self.__sub__ = sub.trimmed()
            
    def subcategory(self):
        return self.__sub__

class Dialog:
    def __init__(self):
        self.__pages__ = []

    def pages(self):
        return self.__pages__
        
    def addPage(self, page):
        self.__pages__.append(page)
        
    def insertPage(self, index, page):
        self.__pages__.insert(index, page)

class Page:
    def __init__(self, name="__default__", parent=None):
        self.__name__ = name
        self.__items__ = []
        self.__parent__ = parent
        
    def parent(self):
        return self.__parent__
        
    def name(self):
        return self.__name__

    def items(self):
        return self.__items__
        
    def addItem(self, item):
        self.__items__.append(item)
        
class Group:
    def __init__(self, name="__default__", checkable=False, default=False, parent=None):
        self.__name__ = name
        self.__parent__ = parent
        self.__checkable__ = checkable
        self.__id__ = 0
        self.__items__ = []
        self.__default__ = default
        
    def parent(self):
        return self.__parent__
        
    def name(self):
        return self.__name__
        
    def setName(self, name):
        if isinstance(name, QString):
            self.__name__ = name
            
    def id(self):
        return self.__id__
        
    def setId(self, id):
        if isinstance(id, QString):
            self.__id__ = id
        
    def setCheckable(self, checkable):
        if isinstance(checkable, bool):
            self.__checkable__ = checkable
        else:
            self.__checkable__ = False
            
    def isCheckable(self):
        return self.__checkable__
        
    def setDefault(self, default):
        if isinstance(default, bool):
            self.__default__ = default
            
    def default(self):
        return self.__default__
        
    def addItem(self, item):
        self.__items__.append(item)
        
    def items(self):
        return self.__items__
        
class Layout:
    ROWS, COLUMNS = range(2)
    def __init__(self, layoutType=0, parent=None):
        self.__items__ = []
        self.__parent__ = parent
#        if not parent is None:
#            self.__id__ = parent.id()+1
#        else:
#            self.__id__ = 0
        self.__type__ = layoutType
        
    def setLayoutType(self, layoutType):
        if layoutType in range(2):
            self.__type__ = layoutType
            
    def layoutType(self):
        return self.__type__

#    def id(self):
#        return self.__id__
        
    def parent(self):
        return self.__parent__
        
    def addItem(self, item):
        self.__items__.append(item)
        
    def items(self):
        return self.__items__
        
class Variables:

    def __init__(self, name="__default__", parent=None):
        self.__items__ = []
        self.__parent__ = parent
        self.__name__ = name
      
    def parent(self):
        return self.__parent__
        
    def addItem(self, item):
        self.__items__.append(item)
        
    def items(self):
        return self.__items__
        
    def name(self):
        return self.__name__
        
    def setName(self, name):
        if isinstance(name, QString):
            self.__name__ = name
        
class Widget:
    def __init__(self, attributes={}):
        self.__attributes__ = attributes
        
    def attributes(self):
        return self.__attributes__
        
    def setAttributes(self, attributes):
        if isinstance(attributes, dict):
            self.__attributes__ = attributes
        else:
            raise Exception("Error: Expected type dict")

class PluginManager(QObject):
    def __init__(self, parent=None, path="."):
        QObject.__init__(self, parent)
        filters = QStringList(["*.xml"])
        dir = QDir(path)
        self.path = path
        dir.setNameFilters(filters)
        self.files = dir.entryInfoList()

    def parseXmlFiles(self):
        reader = QXmlSimpleReader()
        handler = Handler()
        reader.setContentHandler(handler)
        reader.setErrorHandler(handler)
        self.structure = []
        errors = False
        for file in self.files:
            tmp = QFile(file.absoluteFilePath())
            source = QXmlInputSource(tmp)
            ok = reader.parse(source)
            if not ok:
                errors = True
            else:
                self.structure.append(handler.documentStructure())

    def createPlugins(self):
        for collection in self.structure:
            main = self.parent().menuBar()
            menu = None
            # check to see if we already have a menu by this name
            for child in main.findChildren(QMenu):
                title = child.title()
                title.remove("&")
                if title.trimmed() == collection.category().trimmed() and \
                   child.parent() == main:
                    menu = child
                    break
            if menu is None:
                menu = main.addMenu(collection.category())
            for tool in collection.tools():
                sub = tool.subcategory()
                # check to see if we already have a (sub)menu by this name
                for child in menu.findChildren(QMenu):
                    title = child.title()
                    title.remove("&")
                    if title.trimmed() == sub:
                        sub = child
                        break
                if sub is None:
                    sub = menu
                elif isinstance(sub, QString):
                    sub = menu.addMenu(sub)
                    sub.setIcon(QIcon(":preferences-others"))
                self.createTool(tool, sub)

    def run(self, tool):
        dialog = PluginDialog(self.parent(), tool.name())
        self.query = tool.query()
        self.help = tool.help()
        if self.query is None:
            QMessageBox.warning(self.parent(), "manageR - Plugin Error",
            "Error building tool user interface")
            return
        gui = tool.dialog()
        for page in gui.pages():
            if len(page.items()) > 0:
                dialog.addPage(page.name())
                for item in page.items():
                    dialog.addItem(self.recursiveGuiBuilder(item))
        self.connect(dialog, SIGNAL("pluginOutput(PyQt_PyObject)"), self.runCommand)
        self.connect(dialog, SIGNAL("helpRequested()"), self.runHelp)
        dialog.show()

    def runCommand(self, params):
        query = QString(self.query)
        if query.startsWith('"') or query.startsWith("'"):
            query = query[1:]
        if query.endsWith('"') or query.endsWith("'"):
            query = query[0:-1]
        for (key, value) in params.iteritems():
            try:
                query.replace("|%s|" % key, unicode(value))
            except ValueError:
                QMessageBox.warning(self.parent(), "manageR - Plugin Error",
                "Error building command string")
        regexp = QRegExp(r",\s*(?=[,\)]\s*)")
        query.remove(regexp)
        self.emit(SIGNAL("emitCommands(QString)"), query)
        
    def runHelp(self):
        help = QString("?%s" % self.help)
        self.emit(SIGNAL("emitCommands(QString)"), help)

    def createTool(self, tool, menu):
        icon = tool.icon()
        if not isinstance(icon, QIcon):
            icon = QIcon(os.path.join(unicode(self.path), unicode(icon)))
        action = QAction(icon, tool.name(), self.parent())
        action.setData(QVariant(tool))
        QObject.connect(action, SIGNAL("activated()"), lambda: self.run(tool))
        self.parent().addActions(menu, (action,))
        
    def recursiveGuiBuilder(self, item):
        if not isinstance(item, Widget):
            widget = self.createGuiItem(item)
            for i in item.items():
                widget.addItem(self.recursiveGuiBuilder(i))
        else:
            widget = self.createGuiItem(item)
        return widget

    def createGuiItem(self, item):
        if isinstance(item, Layout):
            if item.layoutType() == Layout.COLUMNS:
                return HBoxLayout()
            else:
                return VBoxLayout()
        elif isinstance(item, Group):
            if item.isCheckable():
                default = item.default()
                return GroupCheckBox(id=item.id(), default=default, title=item.name())
            else:
                return GroupBox(id=-1, title=item.name())
        elif isinstance(item, Variables):
            if item.name() == QString("__default__"):
                    item.setName(QString("Choose Variables"))
            return VariableTreeBox(id=-1, name=item.name())
        elif isinstance(item, Widget):
            attributes = item.attributes()
            widgetType = attributes[QString("type")]
            try:
                if widgetType == "SpinBox":
                    widget = SpinBox(attributes[QString("id")], attributes[QString("label")])
                    widget.widget.setValue(int(attributes[QString("default")]))
                elif widgetType == "DoubleSpinBox":
                    widget = DoubleSpinBox(attributes[QString("id")], attributes[QString("label")])
                    widget.widget.setValue(float(attributes[QString("default")]))
                elif widgetType == "ComboBox":
                    widget = ComboBox(attributes[QString("id")], attributes[QString("label")])
                    vals = attributes[QString("default")].split(";")
                    if QString("alternate") in attributes:
                        data = attributes[QString("alternate")].split(";")
                        if len(data) == len(vals):
                            for i in range(len(vals)):
                                widget.widget.addItem(data[i], QVariant(vals[i]))
                    else:
                        widget.widget.addItems(vals)
                elif widgetType == "CheckBox":
                    widget = CheckBox(attributes[QString("id")], attributes[QString("label")])
                    if attributes[QString("default")].toLower() == "true":
                        widget.setChecked(True)
                    else:
                        widget.setChecked(False)
                elif widgetType == "VariableComboBox":
                    widget = VariableComboBox(attributes[QString("id")], 
                                              attributes[QString("label")], 
                                              attributes[QString("default")].split(";"))
                elif widgetType == "VariableLineEdit":
                    widget = VariableLineEdit(attributes[QString("id")], attributes[QString("label")])
                elif widgetType == "VariableListBox":
                    sep=","
                    try:
                        sep = attributes[QString("separator")]
                    except KeyError:
                        pass
                    widget = VariableListBox(attributes[QString("id")], attributes[QString("label")], sep)
                elif widgetType == "RadioGroupBox":
                    ops = attributes[QString("default")].split(";")
                    widget = RadioGroupBox(attributes[QString("id")])
                    widget.setTitle(attributes[QString("label")])
                    if QString("alternate") in attributes:
                        data = attributes[QString("alternate")].split(";")
                        if len(data) == len(ops):
                            for i in range(len(ops)):
                                widget.addButton(ops[i], data[i])
                    else:
                        for subwidget in ops:
                            widget.addButton(subwidget)
                elif widgetType == "AxesBox":
                    ops = attributes[QString("default")].split(";")
                    logscale = False
                    style = False
                    if "logscale" in ops:
                        logscale = True
                    if "style" in ops:
                        style = True
                    widget = AxesBox(attributes[QString("id")], logscale, style)
                elif widgetType == "FileOpenLineEdit":
                    widget = FileOpenLineEdit(attributes[QString("id")], attributes[QString("label")])
                elif widgetType == "FileSaveLineEdit":
                    widget = FileSaveLineEdit(attributes[QString("id")], attributes[QString("label")])
                elif widgetType == "MinMaxBox":
                    widget = MinMaxBox(attributes[QString("id")])
                elif widgetType == "GridCheckBox":
                    widget = GridCheckBox(attributes[QString("id")])
                    if attributes[QString("default")].toLower() == "true":
                        widget.widget.setChecked(True)
                    else:
                        widget.setChecked(False)
                elif widgetType == "PlotOptionsBox":
                    ops = attributes[QString("default")].split(";")
                    box = False
                    titles = False
                    axes = False
                    logscale = False
                    style = False
                    minmax = False
                    if "logscale" in ops:
                        logscale = True
                    if "style" in ops:
                        style = True
                    if "titles" in ops:
                        titles = True
                    if "axes" in ops:
                        axes = True
                    if "box" in ops:
                        box = True
                    if "minmax" in ops:
                        minmax = True
                    widget = PlotOptionsWidget(attributes[QString("id")], box, titles, axes, logscale, style, minmax)
                elif widgetType == "LineStyleBox":
                    widget = LineStyleBox(attributes[QString("id")])
                elif widgetType == "BoundingBoxBox":
                    widget = BoundingBoxBox(attributes[QString("id")])
                elif widgetType == "PlotTypeBox":
                    widget = PlotTypeBox(attributes[QString("id")])
                elif widgetType == "TitlesBox":
                    widget = TitlesBox(attributes[QString("id")])
                elif widgetType == "ParametersBox":
                    widget = ParametersBox()
                else: # default to line edit (LineEditBox)
                    widget = LineEdit(attributes[QString("id")], attributes[QString("label")])
                    widget.widget.setText(attributes[QString("default")])
                return widget
            except KeyError, e:
                QMessageBox.warning(self.parent(), "manageR - Plugin Error",
                "Widget missing required field in plugin XML file:\n"
                +str(e))
                return

class Handler(QXmlDefaultHandler):
    def __init__(self):
        QXmlDefaultHandler.__init__(self)
        self.collection = ToolsCollection()
        self.currentItem = None

    def fatalError(self, err):
        QMessageBox.warning(None, "manageR - XML Parsing Error",
            "Error encountered when building '%s' tool!\n" % self.collection.currentTool().name()
            + "There was a problem with the XML file for "
            + "the '%s' category:\n" % self.collection.category()
            + "    Fatal error on line %s" % err.lineNumber()
            + ", column %s (%s)\n" % (err.columnNumber(), err.message())
            + "Some plugin tools and menus have been ignored.")
        return False

#    def startDocument(self):
#        self.inTool = False
#        self.inQuery = False
#        self.inPage = False
#        self.inGroup = False
#        self.inColumn = False
#        self.inRow = False
#        self.currentGroup = Group()
#        self.currentColumn = Column()
#        self.currentPage = Page()
#        self.currentColumn.addGroup(self.currentGroup)
#        self.currentPage.addColumn(self.currentColumn)
#        self.currentTool = Tool()
#        self.currentTool.gui().append(self.currentPage)
#        self.currentCat = QString("Plugins")
#        return True

    def documentStructure(self):
        return self.collection

    def endElement(self, str1, str2, name):
        if name == "RTool":
            self.inTool = False
        elif name == "Dialog":
            self.inDialog = False
        elif name == "Query":
            self.inQuery = False
        elif name  in ("Group", "Columns", "Rows", 
                       "Variables", "Page"):
            try:
                self.currentItem = self.currentItem.parent()
            except AttributeError:
                pass
            if name == "Variables":
                self.inVariables = False
            elif name == "Page":
                self.inPage = False
#                self.inBase = True
        return True

    def characters(self, chars):
        if self.inQuery:
            self.collection.currentTool().setQuery(chars)
        return True

    def startElement(self, str1, str2, name, attrs):
        if name == "manageRTools":
            self.collection = ToolsCollection()
            for i in range(attrs.count()):
                if attrs.localName(i) == "category" and not attrs.value(i).isEmpty():
                    self.collection.setCategory(attrs.value(i))
                    break
            self.inTool = False
            self.inQuery = False
            self.currentItem = None
        elif name == "RTool":
            self.inTool = True
            tool = Tool()
            for i in range(attrs.count()):
                tmp = attrs.localName(i)
                if tmp == "name":
                    tool.setName(attrs.value(i))
                elif tmp == "subcategory":
                    tool.setSubcategory(attrs.value(i))
                elif tmp == "icon":
                    tool.setIcon(attrs.value(i))
            self.collection.addTool(tool)
            self.inDialog = False
            self.inQuery = False
#            self.inBase = True
            self.currentItem = None
            self.inVariables = False
        elif self.inTool:
            if name == "Help":
                for i in range(attrs.count()):
                    if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                        self.collection.currentTool().setHelp(attrs.value(i))
                        break
                self.currentItem = None
            elif name == "Query":
                if self.inQuery:
                    raise Exception("Error: Nested queries not allowed")
                self.inQuery = True
                self.currentItem = None
            elif name == "Dialog":
                if self.inDialog:
                    raise Exception("Error: Nested dialogs not allowed")
                self.inDialog = True
                self.collection.currentTool().setDialog(Dialog())
                self.inPage = False
#                self.inBase = True
                page = Page()
                self.collection.currentTool().dialog().addPage(page)
                self.currentItem = page
            elif self.inDialog:
                if name == "Page":
                    if self.inPage:
                        raise Exception("Error: Nested pages not allowed")
                    self.inPage = True
#                    self.inBase = False
                    for i in range(attrs.count()):
                        if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                            page = Page(attrs.value(i), self.currentItem)
                            self.collection.currentTool().dialog().addPage(page)
                            break
                    self.currentItem = page
                elif name == "Columns":
                    item = Layout(layoutType=Layout.COLUMNS, parent=self.currentItem)
                    self.currentItem.addItem(item)
                    self.currentItem = item
                elif name == "Rows":
                    item = Layout(layoutType=Layout.ROWS, parent=self.currentItem)
                    self.currentItem.addItem(item)
                    self.currentItem = item
                elif name == "Group":
                    item = Group(parent=self.currentItem)
                    for i in range(attrs.count()):
                        if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                            item.setName(attrs.value(i))
                        if attrs.localName(i) == "id" and not attrs.value(i).isEmpty():
                            item.setId(attrs.value(i))
                        if attrs.localName(i) == "checkable" and not attrs.value(i).isEmpty():
                            if attrs.value(i) == "true":
                                item.setCheckable(True)
                        if attrs.localName(i) == "default" and not attrs.value(i).isEmpty():
                            if attrs.value(i) == "true":
                                item.setDefault(True)
                    self.currentItem.addItem(item)
                    self.currentItem = item
                elif name == "Variables":
                    if self.inVariables:
                        raise Exception("Error: Nested variable tags not allowed")
                    self.inVariables = True
                    item = Variables(parent=self.currentItem)
                    for i in range(attrs.count()):
                        if attrs.localName(i) == "name" and not attrs.value(i).isEmpty():
                            item.setName(attrs.value(i))
                            break
                    self.currentItem.addItem(item)
                    self.currentItem = item
                elif name == "Widget":
                    item = { QString("id")     : QString("0"),
                               QString("label")  : QString(""),
                               QString("type")   : QString("lineEdit"),
                               QString("default"): QString("") }
                    for i in range(attrs.count()):
                        if self.inVariables and \
                            attrs.localName(i) == QString("type") and \
                            not attrs.value(i) in (QString("VariableLineEdit"), 
                                                   QString("VariableListBox")):
                            raise Exception("Error: Currently only VariableLineEdit and "
                                            "VariableListBox allowed in Variables environment")
                        item[attrs.localName(i)] = attrs.value(i)
                    self.currentItem.addItem(Widget(attributes=item))
        return True
