# -*- coding: utf-8 -*-
"""Usage:
from PyQt4 import QtCore, QtGui
from GenericVerticalUI import GenericVerticalUI
class GenericNewDialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = GenericVerticalUI ()
        interface=[["label combobox","comboBox","a;b;c;d","false"   ] , ["label spinbox","doubleSpinBox","10","false"   ] ]
        self.ui.setupUi(self,interface)
"""

from PyQt4.QtCore import (QRegExp, QObject, QString, QUrl, QVariant, Qt, SLOT,
                          SIGNAL, QStringList, )
from PyQt4.QtGui import (QAction, QApplication, QButtonGroup, QCheckBox,
                         QComboBox, QDialog, QDialogButtonBox, QFileDialog,
                         QGridLayout, QHBoxLayout, QIcon, QLabel, QLineEdit,
                         QListWidget, QPixmap, QPushButton, QSpinBox, QTextBrowser,
                         QTextEdit, QVBoxLayout, QDoubleSpinBox, QWidget,
                         QDockWidget, QToolButton, QListView,)

import rpy2.robjects as robjects
import sys, os

class RComboBox(QComboBox):
    def __init__(self, parent=None, types=QStringList()):
        QComboBox.__init__(self, parent)
        self.__types = types

    def types(self):
        return self.__types

class RListWidget(QListWidget):
    def __init__(self, parent=None, types=QStringList(), delimiter=','):
        QListWidget.__init__(self, parent)
        self.__types = types
        self.__delimiter = delimiter

    def types(self):
        return self.__types

    def delimiter(self):
        return self.__delimiter

class GenericVerticalUI(object):
    """Generic class of user interface"""
    def addGuiItem(self, ParentClass, parameters, width):
        """Defines a new set of Label and a box that can be a
        ComboBox, RComboBox, LineEdit, TextEdit or DoubleSpinBox."""
        widgetType=parameters[1]
        #check if there are default values:
        if len(parameters)>2:
            default=parameters[2]
        else:
            default=""
        skip = False
        notnull=parameters[3]
        #setting the right type of widget
        if widgetType=="comboBox":
            widget = QComboBox(ParentClass)
            widget.addItems(default.split(';'))
            widget.setFixedHeight(26)
        elif widgetType=="RComboBox":
            widget = RComboBox(ParentClass, default.split(';'))
            widget.setFixedHeight(26)
            self.hasRComboBox = True
            widget.setEditable(True)
        elif widgetType=="RListWidget":
            widget = RListWidget(ParentClass,
            default.split(';'), notnull)
            widget.setMinimumHeight(116)
            self.hasRComboBox = True
            widget.setSelectionMode(
            QAbstractItemView.ExtendedSelection)
        elif widgetType=="doubleSpinBox":
            widget = QDoubleSpinBox(ParentClass)
            widget.setValue(float(default))
            widget.setFixedHeight(26)
            widget.setMaximum(999999.9999)
            widget.setDecimals(4)
        elif widgetType=="textEdit":
            widget = QTextEdit(ParentClass)
            widget.setPlainText(default)
            widget.setMinimumHeight(116)
        elif widgetType=="helpString":
            self.helpString = default
            skip = True
        else:
            #if unknown assumes lineEdit
            widget = QLineEdit(ParentClass)
            widget.setText(default)
            widget.setFixedHeight(26)
        if not skip:
            hbox = QHBoxLayout()
            name="widget"+unicode(self.widgetCounter)
            widget.setObjectName(name)
            widget.setMinimumWidth(250)
            self.widgets.append(widget)
            name="label"+unicode(self.widgetCounter)
            self.widgetCounter += 1
            label = QLabel(ParentClass)
            label.setObjectName(name)
            label.setFixedWidth(width*8)
            label.setText(parameters[0])
            hbox.addWidget(label)
            hbox.addWidget(widget)
            self.vbox.addLayout(hbox)

    def isSpatial(self):
        return self.hasRComboBox

    def updateRObjects(self):
        layers = browseEnv()
        for widget in self.widgets:
            if isinstance(widget, RComboBox) or isinstance(widget, RListWidget):
                types = widget.types()
                for type in types:
                    for layer in layers:
                        if layer.className() == type.strip() or type.strip() == "all":
                            value = layer.name()
                            widget.addItem(value)
                        if layer in VECTORTYPES \
                        and (sptype.strip() == "data.frame" \
                        or sptype.strip() == "all"):
                            value = layer+"@data"
                            widget.addItem(value)
                        if splayers[layer] in VECTORTYPES \
                        or splayers[layer] == "data.frame":
                            names =  robjects.r('names(%s)' % (layer))
                            if not unicode(names) == 'NULL':
                                for item in list(names):
                                    if splayers[layer] == "data.frame":
                                        value = layer+"$"+item
                                    else:
                                        value = layer+"@data$"+item
                                    try:
                                        if unicode(robjects.r('class(%s)' % (value))[0]) == sptype.strip() \
                                        or sptype.strip() == "all":
                                             widget.addItem(value)
                                    except:
                                        pass



    def setupUi(self, ParentClass, itemlist):
        self.ParentClass = ParentClass
        self.ParentClass.setObjectName("ParentClass")
        self.exists={"RComboBox":0, "comboBox":0, "textEdit":0,
                     "doubleSpinBox":0, "lineEdit":0,  "label":0}
        self.helpString = "There is no help available for this plugin"
        self.widgetCounter = 0
        self.widgets = []
        width = 0
        self.hasRComboBox = False
        self.vbox = QVBoxLayout(self.ParentClass)
        for item in itemlist:
            if len(item[0]) > width:
                width = len(item[0])
        # Draw a label/widget pair for every item in the list
        for item in itemlist:
            self.addGuiItem(self.ParentClass, item, width)
        self.showCommands = QCheckBox("Append commands to console",self.ParentClass)
        self.buttonBox = QDialogButtonBox(self.ParentClass)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(
        QDialogButtonBox.Help|QDialogButtonBox.Close|QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.vbox.addWidget(self.showCommands)
        self.vbox.addWidget(self.buttonBox)
        # accept gets connected in the plugin manager
        QObject.connect(self.buttonBox, SIGNAL("rejected()"), self.ParentClass.reject)
        QObject.connect(self.buttonBox, SIGNAL("helpRequested()"), self.help)
        #QMetaObject.connectSlotsByName(self.ParentClass)

    def help(self):
        if QString(self.helpString).startsWith("topic:"):
            topic = QString(self.helpString).remove("topic:")
            self.ParentClass.parent().editor.moveToEnd()
            self.ParentClass.parent().editor.cursor.movePosition(
            QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
            self.ParentClass.parent().editor.cursor.removeSelectedText()
            self.ParentClass.parent().editor.cursor.insertText(
            "%shelp(%s)" % (
            self.ParentClass.parent().editor.currentPrompt,
            unicode(topic)))
            self.ParentClass.parent().editor.execute(
            QString("help('%s')" % (unicode(topic))))
        else:
            HelpForm(self.ParentClass, self.helpString).show()

class HelpForm(QDialog):

    def __init__(self, parent=None, text=""):
        #super(HelpForm, self).__init__(parent)
        self.setAttribute(Qt.WA_GroupLeader)
        self.setAttribute(Qt.WA_DeleteOnClose)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(text)
        layout = QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(browser)
        self.setLayout(layout)
        self.resize(400, 200)
        QShortcut(QKeySequence("Escape"), self, self.close)
        self.setWindowTitle("R plugin - Help")

class PluginManager:
    def __init__(self, parent):#, iface):
        ## Save reference to the QGIS interface
        #self.iface = iface
        #self.tools = os.path.join(str(os.path.abspath(os.path.dirname(__file__))),"tools.xml")
        self.tools = os.path.join(CURRENTDIR,"tools.xml")
        self.parent = parent

    def makeCaller(self, n):
        return lambda: self.run(n)

    def createActions(self, pluginsMenu):
        self.actionlist=[] #list of actions
        self.callerlist=[] #list of funcions to call run() with id parameter
        self.sublist=[]
        #starting xml file reading
        if not self.tools is None:
            xmlfile=open(self.tools)
            dom=minidom.parse(xmlfile)
            tool=dom.firstChild.firstChild

            #loads every tool in the file
            while tool:
                if isinstance(tool, minidom.Element):
                    add = False
                    name = tool.getAttribute("name")
                    category = tool.getAttribute("category")
                    if not category == "":
                        sub = QMenu(category, self.parent)
                        sub.setIcon(QIcon(":mActionAnalysisMenu.png"))
                        add = True
                    else:
                        sub = pluginsMenu
                        add = False
                    for item in self.sublist:
                        if category == item.title():
                            sub = item
                            add = False
                            break
                    if add:
                        self.sublist.append(sub)
                        pluginsMenu.addMenu(sub)
                    # Create action that will start plugin configuration
                    self.actionlist.append(QAction(
                    QIcon(":mActionAnalysisTool"), name, self.parent))
                    #create a new funcion that calls run() with the id parameter
                    self.callerlist.append(self.makeCaller(len(self.actionlist)-1))
                    # connect the action to the run method
                    QObject.connect(self.actionlist[-1],
                    SIGNAL("activated()"), self.callerlist[-1])
                    # Add toolbar button and menu item
                    self.parent.addActions(sub, (self.actionlist[-1],))
                tool=tool.nextSibling
            xmlfile.close()

    def runCommand(self, command):
        mime = QMimeData()
        self.parent.editor.moveToEnd()
        self.parent.editor.cursor.movePosition(
        QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        self.parent.editor.cursor.removeSelectedText()
        self.parent.editor.cursor.insertText(
        self.parent.editor.currentPrompt)
        if self.dlg.ui.showCommands.isChecked():
            mime.setText("# manageR '%s' tool\n%s" % (self.name,command))
            self.parent.editor.insertFromMimeData(mime)
            self.parent.editor.entered()
        else:
            mime.setText("# manageR '%s' tool" % (self.name))
            self.parent.editor.insertFromMimeData(mime)
            self.parent.editor.execute(QString(command))

    def start(self):
        #reads the info in the widgets and calls the sql command
        command = self.command
        for i,item in enumerate(self.dlg.ui.widgets):
            if type(item)==type(QTextEdit()):
                text=unicode(item.toPlainText())
            elif type(item)==type(QLineEdit()):
                text=unicode(item.text())
            elif type(item)==type(QDoubleSpinBox()):
                text=unicode(item.value())
            elif type(item)==type(QComboBox()):
                text=unicode(item.currentText())
            elif isinstance(item, RListWidget):
                items=item.selectedItems()
                text=QString()
                for j in items:
                    text.append(j.text()+item.spDelimiter())
                text.remove(-1,1)
            else:
                try:
                    text=unicode(item.currentText())
                except:
                    text="Error loading widget."
            command = command.replace("|"+unicode(i+1)+"|",text)
        self.runCommand(command)
        self.dlg.close()

    def getTool(self,toolid):
        """Reads the xml file looking for the tool with toolid
        and returns it's commands and the parameters double list."""
        xmlfile=open(self.tools)
        dom=minidom.parse(xmlfile)
        tools=dom.firstChild
        count = 0
        for tool in tools.childNodes:
            if isinstance(tool, minidom.Element):
                if count == toolid:
                    break
                count += 1
        query=tool.getAttribute("query")
        name= tool.getAttribute("name")
        lines=[]
        parm=tool.firstChild
        while parm:
            if isinstance(parm, minidom.Element):
                line = [
                parm.attributes.getNamedItem("label").value,
                parm.attributes.getNamedItem("type").value,
                parm.attributes.getNamedItem("default").value,
                parm.attributes.getNamedItem("notnull").value]
                lines.append(line)
            parm=parm.nextSibling
        xmlfile.close()
        return name, query, lines

    # run method that performs all the real work
    def run(self, actionid):
        #reads the xml file
        self.name, self.command, parameters = self.getTool(actionid)
        # create and show the dialog
        self.dlg = PluginsDialog(self.parent, parameters)
        self.dlg.setWindowTitle(self.name)
        if self.dlg.ui.isSpatial():
            self.dlg.ui.updateRObjects()
        #connect the slots
        QObject.connect(self.dlg.ui.buttonBox, SIGNAL("accepted()"), self.start)
        # show the dialog
        self.dlg.show()

class PluginsDialog(QDialog):
    def __init__(self, parent, interface):
        QDialog.__init__(self, parent)
        self.ui = GenericVerticalUI()
        self.ui.setupUi(self, interface)