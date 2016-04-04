# -*- coding: utf-8 -*-

# PyQt imports
from PyQt4.QtGui import (QDialog, QListWidget, QListWidgetItem, QStackedWidget,
                         QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QSpinBox,
                         QPushButton, QListWidget, QWidget, QCheckBox, QFontComboBox,
                         QFont, QApplication, QIcon, QListView, QGroupBox, QLineEdit,
                         QPlainTextEdit, QFontMetrics, QPixmap, QColor, QColorDialog,
                         QRegExpValidator, )
from PyQt4.QtCore import (SIGNAL, SLOT, QString, QSettings, QVariant, QSize, Qt,
                          QRegExp,)

# generic Python imports
import sys, os

# config specific imports
import resources

CURRENTDIR = unicode(os.path.abspath(os.path.dirname(__file__)))

class ConfigDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.contentsWidget = QListWidget()
        self.contentsWidget.setViewMode(QListView.IconMode)
        self.contentsWidget.setIconSize(QSize(76, 66))
        self.contentsWidget.setMovement(QListView.Static)
        self.contentsWidget.setMaximumWidth(106)
        self.contentsWidget.setMinimumWidth(106)
        self.contentsWidget.setSpacing(12)

        self.pagesWidget = QStackedWidget()
        self.generalPage = GeneralPage(self)
        self.pagesWidget.addWidget(self.generalPage)
        self.highlightingPage = HighlightingPage(self)
        self.pagesWidget.addWidget(self.highlightingPage)
        self.consolePage = ConsolePage(self)
        self.pagesWidget.addWidget(self.consolePage)
        self.editorPage = EditorPage(self)
        self.pagesWidget.addWidget(self.editorPage)

        closeButton = QPushButton("Close")

        self.createIcons()
        self.contentsWidget.setCurrentRow(0)

        self.connect(closeButton, SIGNAL("clicked()"), self, SLOT("accept()"))

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.contentsWidget)
        horizontalLayout.addWidget(self.pagesWidget, 1)

        buttonsLayout = QHBoxLayout()
        buttonsLayout.addStretch(1)
        buttonsLayout.addWidget(closeButton)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(horizontalLayout)
        mainLayout.addStretch(1)
        mainLayout.addSpacing(12)
        mainLayout.addLayout(buttonsLayout)
        self.setLayout(mainLayout)
        self.setWindowTitle("Configure manageR")

    def accept(self):
        self.saveSettings()
        QDialog.close(self)

    def createIcons(self):
        generalButton = QListWidgetItem(self.contentsWidget)
        generalButton.setIcon(QIcon(":gconf-editor.svg"))
        generalButton.setText("General")
        generalButton.setTextAlignment(Qt.AlignHCenter)
        generalButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        highlightingButton = QListWidgetItem(self.contentsWidget)
        highlightingButton.setIcon(QIcon(":applications-graphics.svg"));
        highlightingButton.setText("Highlighting")
        highlightingButton.setTextAlignment(Qt.AlignHCenter)
        highlightingButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        consoleButton = QListWidgetItem(self.contentsWidget)
        consoleButton.setIcon(QIcon(":utilities-terminal.svg"))
        consoleButton.setText("Console")
        consoleButton.setTextAlignment(Qt.AlignHCenter)
        consoleButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        editorButton = QListWidgetItem(self.contentsWidget)
        editorButton.setIcon(QIcon(":accessories-text-editor.svg"));
        editorButton.setText("Editor")
        editorButton.setTextAlignment(Qt.AlignHCenter)
        editorButton.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        self.connect(self.contentsWidget,
                SIGNAL("currentItemChanged(QListWidgetItem*, QListWidgetItem*)"),
                self.changePage)

    def changePage(self, current, previous):
        if not current:
            current = previous
        self.pagesWidget.setCurrentIndex(self.contentsWidget.row(current))

    def saveSettings(self):
        sets = QSettings()
        settings = self.generalPage.settings()
        settings.extend(self.highlightingPage.settings())
        settings.extend(self.consolePage.settings())
        settings.extend(self.editorPage.settings())
        for name, setting in settings:
            sets.setValue("manageR/%s" % name, setting)

class GeneralPage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        settings = QSettings()
        
        monofont = QFont(settings.value("manageR/fontfamily", "DejaVu Sans Mono").toString(),
        settings.value("manageR/fontsize", 10).toInt()[0])
        self.rememberGeometryCheckBox = QCheckBox("&Remember geometry")
        self.rememberGeometryCheckBox.setToolTip("<p>Check this to make "
                "manageR remember the size and position of the console "
                "window and one editR window.</p>")
        remember = settings.value("manageR/remembergeometry", True).toBool()
        self.rememberGeometryCheckBox.setChecked(remember)

        self.fontComboBox = QFontComboBox()
        self.fontComboBox.setCurrentFont(monofont)
        self.fontComboBox.setFont(monofont)
        self.fontComboBox.setToolTip("<p>Specify the font family for "
                "the manageR console and all EditR windows.</p>")
        fontLabel = QLabel("&Font:")
        fontLabel.setBuddy(self.fontComboBox)

        self.fontSpinBox = QSpinBox()
        self.fontSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.fontSpinBox.setRange(6, 20)
        self.fontSpinBox.setSuffix(" pt")
        self.fontSpinBox.setFont(monofont)
        self.fontSpinBox.setFixedWidth(100)
        self.fontSpinBox.setValue(settings.value("manageR/fontsize", 10).toInt()[0])
        self.fontSpinBox.setToolTip("<p>Specify the font size for  "
                "the manageR console, and all EditR windows.</p>")

        self.tabWidthSpinBox = QSpinBox()
        self.tabWidthSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.tabWidthSpinBox.setRange(2, 20)
        self.tabWidthSpinBox.setSuffix(" spaces")
        self.tabWidthSpinBox.setFont(monofont)
        self.tabWidthSpinBox.setFixedWidth(100)
        tabwidth = settings.value("manageR/tabwidth", 4).toInt()[0]
        self.tabWidthSpinBox.setValue(tabwidth)
        self.tabWidthSpinBox.setToolTip("<p>Specify the number of "
                "spaces that a single tab should span.</p>")
        tabWidthLabel = QLabel("&Tab width:")
        tabWidthLabel.setBuddy(self.tabWidthSpinBox)

        self.timeoutSpinBox = QSpinBox()
        self.timeoutSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.timeoutSpinBox.setRange(0, 20000)
        self.timeoutSpinBox.setFont(monofont)
        self.timeoutSpinBox.setSingleStep(100)
        self.timeoutSpinBox.setSuffix(" ms")
        self.timeoutSpinBox.setFixedWidth(100)
        delay = settings.value("manageR/delay", 500).toInt()[0]
        self.timeoutSpinBox.setValue(delay)
        self.timeoutSpinBox.setToolTip("<p>Specify the time (in milliseconds) "
                "to wait before displaying the autocomplete popup when a set of "
                "possible matches are found.</p>")
        timeoutLabel = QLabel("Popup time delay:")
        timeoutLabel.setBuddy(self.timeoutSpinBox)

        self.mincharsSpinBox = QSpinBox()
        self.mincharsSpinBox.setAlignment(Qt.AlignVCenter|Qt.AlignRight)
        self.mincharsSpinBox.setRange(1, 100)
        self.mincharsSpinBox.setFont(monofont)
        self.mincharsSpinBox.setSuffix(" chars")
        self.mincharsSpinBox.setFixedWidth(100)
        minchars = settings.value("manageR/minimumchars", 3).toInt()[0]
        self.mincharsSpinBox.setValue(minchars)
        self.mincharsSpinBox.setToolTip("<p>Specify the minimum number of characters "
                "that must be typed before displaying the autocomplete popup when a "
                "set of possible matches are found.</p>")
        mincharsLabel = QLabel("Minimum word size:")
        mincharsLabel.setBuddy(self.mincharsSpinBox)

        self.autocompleteCheckBox = QCheckBox("Enable autocomplete/tooltips")
        self.autocompleteCheckBox.setToolTip("<p>Check this to enable "
                "autocompletion of R commands.</p>")
        complete = settings.value("manageR/enableautocomplete", True).toBool()
        self.autocompleteCheckBox.setChecked(complete)

        self.autocompleteBrackets = QCheckBox("Enable auto-insert of brackets/parentheses")
        self.autocompleteBrackets.setToolTip("<p>Check this to enable "
                "auto-insert of brackets and parentheses when typing R functions and commands.</p>")
        brackets = settings.value("manageR/bracketautocomplete", True).toBool()
        self.autocompleteBrackets.setChecked(brackets)

        #grid = QGridLayout()
        box = QVBoxLayout()
        box.addWidget(self.rememberGeometryCheckBox)
        hbox = QHBoxLayout()
        hbox.addWidget(fontLabel)
        hbox.addStretch()
        hbox.addWidget(self.fontComboBox)
        hbox.addWidget(self.fontSpinBox)
        box.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(tabWidthLabel)
        hbox.addStretch()
        hbox.addWidget(self.tabWidthSpinBox, Qt.AlignRight)
        box.addLayout(hbox)

        gbox = QGroupBox("Autocompletion")
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(timeoutLabel)
        hbox.addStretch()
        hbox.addWidget(self.timeoutSpinBox,Qt.AlignRight)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(mincharsLabel)
        hbox.addStretch()
        hbox.addWidget(self.mincharsSpinBox,Qt.AlignRight)
        vbox.addLayout(hbox)
        vbox.addWidget(self.autocompleteCheckBox)
        vbox.addWidget(self.autocompleteBrackets)
        gbox.setLayout(vbox)

        box.addWidget(gbox)
        self.setLayout(box)

    def settings(self):
        settings = []
        settings.append(("remembergeometry",self.rememberGeometryCheckBox.isChecked()))
        settings.append(("fontfamily",self.fontComboBox.currentFont()))
        settings.append(("fontsize",self.fontSpinBox.value()))
        settings.append(("tabwidth",self.tabWidthSpinBox.value()))
        settings.append(("delay",self.timeoutSpinBox.value()))
        settings.append(("minimumchars",self.mincharsSpinBox.value()))
        settings.append(("enableautocomplete",self.autocompleteCheckBox.isChecked()))
        settings.append(("bracketautocomplete",self.autocompleteBrackets.isChecked()))
        return settings

class ConsolePage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        settings = QSettings()
        monofont = QFont(settings.value("manageR/fontfamily", "DejaVu Sans Mono").toString(),
        settings.value("manageR/fontsize", 10).toInt()[0])
        
        before = settings.value("manageR/beforeinput", ">").toString()
        self.inputLineEdit = QLineEdit(before)
        self.inputLineEdit.setMaxLength(3)
        self.inputLineEdit.setFont(monofont)
        self.inputLineEdit.setFixedWidth(100)
        self.inputLineEdit.setToolTip(
                "<p>Specify the prompt (e.g. '>') that will be "
                "displayed each time the console is ready for input.</p>")
        inputPromptLabel = QLabel("&Input prompt:")
        inputPromptLabel.setBuddy(self.inputLineEdit)

        after = settings.value("manageR/afteroutput", "+").toString()
        self.outputLineEdit = QLineEdit(after)
        self.outputLineEdit.setMaxLength(3)
        self.outputLineEdit.setFont(monofont)
        self.outputLineEdit.setFixedWidth(100)
        self.outputLineEdit.setToolTip(
                "<p>Specify the prompt (e.g. '+') that will "
                "be displayed each time further input to "
                "the console is required.</p>")
        outputPromptLabel = QLabel("&Continuation prompt:")
        outputPromptLabel.setBuddy(self.outputLineEdit)

        folder = settings.value("manageR/setwd", ".").toString()
        self.workingFolderLineEdit = QLineEdit(folder)
        self.workingFolderLineEdit.setFont(monofont)
        workingFolderLabel = QLabel("&Default working directory:")
        workingFolderLabel.setBuddy(self.workingFolderLineEdit)
        self.workingFolderLineEdit.setToolTip(
                "<p>Specify the default working directory for "
                "the manageR console. Setting this to blank, or "
                "'.', will use the current Python working directory. "
                "Changes made here only take effect when manageR is next started.</p>")
                
        plugins = settings.value("manageR/plugins", CURRENTDIR).toString()
        self.pluginsFolderLineEdit = QLineEdit(plugins)
        self.pluginsFolderLineEdit.setFont(monofont)
        pluginsFolderLabel = QLabel("&Plugins (xml files) directory:")
        pluginsFolderLabel.setBuddy(self.pluginsFolderLineEdit)
        self.pluginsFolderLineEdit.setToolTip(
                "<p>Specify the directory that manageR should search for plugins "
                "See the manageR help (Help > About > Help) for information on the "
                "structure of the plugin XML files. "
                "Changes made here only take effect when manageR is next started.</p>")

        self.loadEnvironmentCheckBox = QCheckBox("Load existing '.RData' and '.Rhistory' file(s) on startup")
        self.loadEnvironmentCheckBox.setToolTip(
                "<p>Check this to make manageR automatically load any '.RData' and "
                "'.Rhistory' files in the current working directory "
                "on startup.</p>")
        load = settings.value("manageR/loadenvironment", True).toBool()
        self.loadEnvironmentCheckBox.setChecked(load)

        self.useRasterPackage = QCheckBox("Use 'raster' package for importing rasters")
        self.useRasterPackage.setToolTip(
                "<p>Check this to make manageR use the 'raster' "
                "package for loading raster layers</p>")
        raster = settings.value("manageR/useraster", True).toBool()
        self.useRasterPackage.setChecked(raster)

        gbox = QGroupBox("&At startup")
        self.editor = QPlainTextEdit(self)
        startup = settings.value("manageR/consolestartup", "").toString()
        self.editor.setPlainText(startup)
        self.editor.setTabChangesFocus(True)
        self.editor.document().setDefaultFont(monofont)
        #Highlighter(editor.document())
        vbox = QVBoxLayout()
        vbox.addWidget(self.editor)
        vbox.addWidget(QLabel("<font color=green><i><p>manageR executes the lines above "
                 "whenever the R interpreter is started.<br/>"
                 "Use them to add custom functions and/or load "
                 "libraries or additional tools.<br/>"
                 "Changes made here only take effect when manageR is next run."))
        gbox.setLayout(vbox)

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(inputPromptLabel)
        hbox.addStretch()
        hbox.addWidget(self.inputLineEdit,Qt.AlignRight)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(outputPromptLabel)
        hbox.addStretch()
        hbox.addWidget(self.outputLineEdit,Qt.AlignRight)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(workingFolderLabel)
        hbox.addStretch()
        hbox.addWidget(self.workingFolderLineEdit, Qt.AlignRight)
        vbox.addLayout(hbox)
        hbox = QHBoxLayout()
        hbox.addWidget(pluginsFolderLabel)
        hbox.addStretch()
        hbox.addWidget(self.pluginsFolderLineEdit, Qt.AlignRight)
        vbox.addLayout(hbox)
        vbox.addWidget(self.loadEnvironmentCheckBox)
        vbox.addWidget(self.useRasterPackage)
        vbox.addWidget(gbox)
        self.setLayout(vbox)

    def settings(self):
        settings = []
        settings.append(("beforeinput", self.inputLineEdit.text()))
        settings.append(("afteroutput", self.outputLineEdit.text()))
        settings.append(("sewd", self.workingFolderLineEdit.text()))
        settings.append(("plugins", self.pluginsFolderLineEdit.text()))
        settings.append(("loadenvironment", self.loadEnvironmentCheckBox.isChecked()))
        settings.append(("useraster", self.useRasterPackage.isChecked()))
        settings.append(("consolestartup", self.editor.toPlainText()))
        return settings

class HighlightingPage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        settings = QSettings()
        monofont = QFont(settings.value("manageR/fontfamily", "DejaVu Sans Mono").toString(),
        settings.value("manageR/fontsize", 10).toInt()[0])
        fm = QFontMetrics(monofont)
        self.highlightingCheckBox = QCheckBox("Enable syntax highlighting")
        self.highlightingCheckBox.setToolTip("<p>Check this to enable "
                "syntax highlighting in the console and EditR windows."
                "Changes made here only take effect when manageR is next run.</p>")
        highlighting = settings.value("manageR/enablehighlighting", True).toBool()
        self.highlightingCheckBox.setChecked(highlighting)

        minButtonWidth = 0
        minWidth = 0
        label = QLabel("Background:")
        label.setMinimumWidth(minWidth)
        color = settings.value("manageR/backgroundfontcolor", "#FFFFFF").toString()
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(color))
        colorButton = QPushButton("&0 Color...")
        colorButton.setIcon(QIcon(pixmap))
        minButtonWidth = max(minButtonWidth, 10+pixmap.width()+fm.width(colorButton.text()))

        #self.colors["background"] = [Config["backgroundcolor"], None]
        #self.colors["background"][1] = colorButton
        self.connect(colorButton, SIGNAL("clicked()"),
            lambda button=colorButton, name="background": self.setColor(button, name))

        gbox = QGridLayout()
        gbox.addWidget(self.highlightingCheckBox, 0,0,1,3)
        gbox.addWidget(label,2,0,1,1)
        gbox.addWidget(colorButton,2,3,1,1)
        count = 1
        for name, labelText, color, bold, italic in (
                                ("normal", "Normal:", "#000000", False, False), 
                                ("keyword", "Keywords:", "#000080", True, False),
                                ("builtin", "Builtins:", "#0000A0", False, False), 
                                ("constant", "Constants:", "#0000C0", False, False),
                                ("delimiter", "Delimiters:", "#0000E0", False, False),
                                ("comment", "Comments:", "#007F00", False, True),
                                ("string", "Strings:", "#808000", False, False),
                                ("number", "Numbers:", "#924900", False, False),
                                ("error", "Errors:", "#FF0000", False, False),
                                ("assignment", "Assignment operator:", "#50621A", False, False),
                                ("syntax", "Syntax errors:", "#FF0000", False, True)):
            label = QLabel(labelText)
            #labels.append(label)
            if name == "syntax":
                boldCheckBox = QCheckBox("Underline")
                boldCheckBox.setChecked(settings.value("manageR/%sfontunderline" % name, bold).toBool())
            else:
                boldCheckBox = QCheckBox("Bold")
                boldCheckBox.setChecked(settings.value("manageR/%sfontbold" % name, bold).toBool())
            #self.boldCheckBoxes[name] = boldCheckBox
            italicCheckBox = QCheckBox("Italic")
            italicCheckBox.setChecked(settings.value("manageR/%sfontitalic" % name, italic).toBool())
            #self.italicCheckBoxes[name] = italicCheckBox
            #self.colors[name] = [Config["%sfontcolor" % name], None]
            if count <= 9:
                colorButton = QPushButton("&%d Color..." % count)
            else:
                colorButton = QPushButton("&%s Color..." % labelText[0])
            count += 1
            pixmap.fill(QColor(settings.value("manageR/%sfontcolor" % name, color).toString()))
            colorButton.setIcon(QIcon(pixmap))
            minButtonWidth = max(minButtonWidth, 10 + pixmap.width()+fm.width(colorButton.text()))
            #buttons.append(colorButton)
            #self.colors[name][1] = colorButton
            gbox.addWidget(label,count+2,0,1,1)
            gbox.addWidget(boldCheckBox,count+2,1,1,1)
            gbox.addWidget(italicCheckBox,count+2,2,1,1)
            gbox.addWidget(colorButton,count+2,3,1,1)
            self.connect(colorButton, SIGNAL("clicked()"),
                lambda button=colorButton, name=name: self.setColor(button, name))
            self.connect(boldCheckBox, SIGNAL("stateChanged(int)"),
                lambda state, name=name: self.setWeight(state, name))
            self.connect(italicCheckBox, SIGNAL("stateChanged(int)"),
                lambda state, name=name: self.setItalic(state, name))
        self.setLayout(gbox)

    def setColor(self, button, name):
        settings = QSettings()
        color = QColorDialog.getColor(
            QColor(settings.value("manageR/%sfontcolor" % name, "#FFFFFF").toString()), self)
        if color is not None:
            settings.setValue("manageR/%sfontcolor" % name, color.name())
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(color.name()))
            button.setIcon(QIcon(pixmap))

    def setWeight(self, state, name):
        settings = QSettings()
        settings.setValue("manageR/%sfontbold" % name, state)
            
            
    def setItalic(self, state, name):
        settings = QSettings()
        settings.setValue("manageR/%sfontitalic" % name, state)

    def settings(self):
        return [("enablehighlighting", self.highlightingCheckBox.isChecked())]

class EditorPage(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        settings = QSettings()
        monofont = QFont(settings.value("manageR/fontfamily", "DejaVu Sans Mono").toString(),
        settings.value("manageR/fontsize", 10).toInt()[0])

        suffix = settings.value("manageR/backupsuffix", "~").toString()
        self.backupLineEdit = QLineEdit(suffix)
        self.backupLineEdit.setToolTip("<p>If non-empty, a backup will be "
                "kept with the given suffix. If empty, no backup will be made.</p>")
        regex = QRegExp(r"[~.].*")
        self.backupLineEdit.setValidator(QRegExpValidator(regex, self))
        self.backupLineEdit.setFont(monofont)
        self.backupLineEdit.setFixedWidth(100)
        backupLabel = QLabel("&Backup suffix:")
        backupLabel.setBuddy(self.backupLineEdit)

        gbox = QGroupBox("On &new file")
        self.editor = QPlainTextEdit(self)
        newfile = settings.value("manageR/newfile", "").toString()
        self.editor.setPlainText(newfile)
        self.editor.setTabChangesFocus(True)
        self.editor.document().setDefaultFont(monofont)
        #Highlighter(editor.document())
        vbox = QVBoxLayout()
        vbox.addWidget(self.editor)
        vbox.addWidget(QLabel("<font color=green><i>The text here is automatically "
                 "inserted into new R scripts.<br>It may be convenient to add "
                 "your standard libraries and copyright notice here."))
        gbox.setLayout(vbox)

        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(backupLabel)
        hbox.addStretch()
        hbox.addWidget(self.backupLineEdit)
        vbox.addLayout(hbox)
        vbox.addWidget(gbox)
        self.setLayout(vbox)

    def settings(self):
        settings = []
        settings.append(("backupsuffix", self.backupLineEdit.text()))
        settings.append(("newfile", self.editor.toPlainText()))
        return settings


def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    app.setOrganizationName("manageR")
    app.setOrganizationDomain("ftools.ca")
    app.setApplicationName("manageR")
    app.setWindowIcon(QIcon(":mActionIcon.png"))
    app.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))
    dialog = ConfigDialog(None)
    dialog.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
