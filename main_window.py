#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = '''
manageR - Interface to the R statistical programming language

Copyright (C) 2009-2010 Carson J. Q. Farmer

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public Licence as published by the Free Software
Foundation; either version 2 of the Licence, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public Licence for more details.

You should have received a copy of the GNU General Public Licence along with
this program (see LICENSE file in install directory); if not, write to the Free
Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.

Portions of the Console and EditR window, as well as several background
funtions are based on the Sandbox python gui of Mark Summerfield.
  Copyright (C) 2007-9 Mark Summerfield. All rights reserved.
  Released under the terms of the GNU General Public License.
The 'plugin' functinality is based largely on the PostGisTools plugin of
Mauricio de Paulo.
  Copyright (C) 2009 Mauricio de Paulo. All rights reserved.
  Released under the terms of the GNU General Public License.
manageR makes extensive use of rpy2 (Laurent Gautier) to communicate with R.
  Copyright (C) 2008-9 Laurent Gautier.
  Rpy2 may be used under the terms of the GNU General Public License.
'''

# general python imports  
import os, re, sys, platform, base64
from threading import Timer

# PyQt imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import QHttp

# extra resources
import complete, resources
from browsers import AboutBrowser, HelpBrowser
from script_text_edit import REditor, Validator
from plain_text_edit import Highlighter, BookmarksPane
from tab_widget import TabWidget
from rpy_helper_functions import *

# rpy2 (R) imports
import rpy2
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc

__currentdir__ = unicode(os.path.abspath(os.path.dirname(__file__)))
__version__ = "0.0.1"

rpy2.rinterface.set_cleanup(cleanup)

class MainWindow(QMainWindow):

    outputCommands = pyqtSignal(QString)
    updateBookmarks = pyqtSignal(dict)
    

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowIcon(QIcon(":icon.png"))
        self.setWindowTitle("editR")
        # main settings
        fontfamily = QSettings().value("manageR/fontfamily", 
                                       "DejaVu Sans Mono").toString()
        fontsize = QSettings().value("manageR/fontsize", 10).toInt()[0]
        tabwidth = QSettings().value("manageR/tabwidth", 4).toInt()[0]
        autobracket = QSettings().value("manageR/bracketautocomplete", 
                                        True).toBool()
        autopopup = QSettings().value("manageR/enableautocomplete", 
                                      True).toBool()
        font = QFont(fontfamily, fontsize)
        self.setFont(font)
        self.setMinimumSize(600, 400)

        if QSettings().value("manageR/enablehighlighting", True).toBool():
            backcolor = QColor(QSettings().value("manageR/backgroundfontcolor", 
                                                 "#FFFFFF").toString())
            fontcolor = QColor(QSettings().value("manageR/normalfontcolor", 
                                                 "#000000").toString())
            palette = QPalette(backcolor)
            palette.setColor(QPalette.Active, QPalette.Base, backcolor)
            palette.setColor(QPalette.Active, QPalette.WindowText, 
                             QColor(fontcolor))
            palette.setColor(QPalette.Inactive, QPalette.WindowText, 
                             QColor(fontcolor))
        self.setPalette(palette)

        self.tabs = TabWidget(self)
        self.tabs.setDocumentMode(False)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tab_close)
        self.tabs.modificationChanged.connect(self.file_modified)
        self.tabs.cursorPositionChanged.connect(self.update_indicators)
        self.tabs.blockCountChanged.connect(self.update_indicators)
        self.file_new()
        
        self.setCentralWidget(self.tabs)
        self.paths = QStringList(os.path.join(__currentdir__, "doc", "html"))
        self.view_menu = QMenu("&View") # create this first...
        self.create_file_actions()
        self.create_edit_actions()
        self.menuBar().addMenu(self.view_menu)
        self.create_help_actions()
        self.create_doc_widgets()
        
        self.column_count_label = QLabel("Column 1")
        self.statusBar().addPermanentWidget(self.column_count_label)
        self.line_count_label = QLabel("Line 1 of 1")
        self.statusBar().addPermanentWidget(self.line_count_label)
        
        # start with an empty editor...
        self.startTimer(30)
        self.statusBar().showMessage("Ready", 5000)
        
    def timerEvent(self, event):
        # use this to process interactive R events (plots & help system)
        try:
            robjects.rinterface.process_revents()
        except Exception, err:
            pass
            
    def create_file_actions(self):
        file_menu = self.menuBar().addMenu("&File")
        file_tool_bar = self.addToolBar("File Toolbar")
        file_tool_bar.setObjectName("file_tool_bar")

        file_new_action = self.create_action("&New", self.file_new,
            QKeySequence.New, "document-new", "Open empty R script")
        file_open_action = self.create_action("&Open...", self.file_open,
            QKeySequence.Open, "document-open", "Open existing R script")
        file_save_action = self.create_action("&Save", self.file_save,
            QKeySequence.Save, "document-save", "Save R script")
        file_saveas_action = self.create_action("Save &As...",
            self.file_saveas, QKeySequence.SaveAs,
            "document-save-as", "Save R script as...")
        file_close_action = self.create_action("&Close", self.tab_close,
            QKeySequence.Close, "window-close", "Close tab")
#        file_config_action = self.create_action("Config&ure...",
#            self.file_configure, "","gconf-editor", "Configure manageR")
        file_quit_action = self.create_action("&Quit", self.file_quit,
            "Ctrl+Q", "system-shutdown", "Quit editR")
        file_send_action = self.create_action("", self.send_commands,
            "Ctrl+Enter", "custom-terminal-line", "Send commands to console")

        self.add_actions(file_menu, (file_new_action, file_open_action, None, 
                                     file_save_action, file_saveas_action, None,
                                     file_send_action, None, file_close_action, 
                                     file_quit_action,))
        self.add_actions(file_tool_bar, (file_new_action, file_open_action, 
                                         file_save_action,None, file_send_action))
        self.add_actions(self.view_menu, (file_tool_bar.toggleViewAction(),))

    def create_edit_actions(self):
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_tool_bar = self.addToolBar("Edit Toolbar")
        edit_tool_bar.setObjectName("edit_tool_bar")
       
        edit_undo_action = self.create_action("&Undo", 
            lambda: self.current_tab().undo(), QKeySequence.Undo, "edit-undo",
            "Undo last editing action")
        self.tabs.undoAvailable.connect(edit_undo_action.setEnabled)
        edit_undo_action.setEnabled(False)
        edit_redo_action = self.create_action("&Redo", 
            lambda: self.current_tab().redo(), QKeySequence.Redo, "edit-redo",
            "Redo last editing action")
        self.tabs.redoAvailable.connect(edit_redo_action.setEnabled)
        edit_redo_action.setEnabled(False)
        edit_copy_action = self.create_action("&Copy", 
            lambda: self.current_tab().copy(), QKeySequence.Copy, "edit-copy", 
            "Copy text to clipboard")
        self.tabs.copyAvailable.connect(edit_copy_action.setEnabled)
        edit_copy_action.setEnabled(False)
        edit_cut_action = self.create_action("Cu&t", 
            lambda: self.current_tab().cut(), QKeySequence.Cut, "edit-cut", 
            "Cut text to clipboard")
        self.tabs.copyAvailable.connect(edit_cut_action.setEnabled)
        edit_cut_action.setEnabled(False)
        edit_paste_action = self.create_action("&Paste",
            lambda: self.current_tab().paste(), QKeySequence.Paste, "edit-paste",
            "Paste text from clipboard")
        edit_selectall_action = self.create_action("Select &All",
            lambda: self.current_tab().selectAll(), QKeySequence.SelectAll,
            "edit-select-all", "Select all")
        edit_find_action = self.create_action("&Find", 
            lambda: self.current_tab().toggle_find(), QKeySequence.Find, 
            "edit-find", "Find text")
        edit_replace_action = self.create_action("&Replace",
            lambda: self.current_tab().toggle_replace(), QKeySequence.Replace,
            "edit-find-replace", "Replace text")
        edit_gotoline_action =  self.create_action("&Go to line",
            lambda: self.current_tab().goto_line(), "Ctrl+G", "go-jump",
            "Move cursor to line")
        edit_indent_action = self.create_action("&Indent Region",
            lambda: self.current_tab().indent(), "Ctrl+I", "format-indent-more",
            "Indent the selected text or the current line")
        edit_unindent_action = self.create_action(
            "Unin&dent Region", lambda: self.current_tab().unindent(),
            "Ctrl+Shift+I", "format-indent-less",
            "Unindent the selected text or the current line")
        edit_comment_action = self.create_action("C&omment Region",
            lambda: self.current_tab().comment(), "Ctrl+M", "list-add",
            "Comment out the selected text or the current line")
        edit_uncomment_action = self.create_action(
            "Uncomment Re&gion", lambda: self.current_tab().uncomment(),
            "Ctrl+Shift+M", "list-remove",
            "Uncomment the selected text or the current line")
        edit_hide_action = self.create_action(
            "Hide selected text", lambda: self.current_tab().hide_blocks(),
            "Ctrl+K", "window-close", "Hide selected text")
        edit_hide_action.setEnabled(False)
        self.tabs.hideAvailable.connect(edit_hide_action.setEnabled)
        edit_show_action = self.create_action(
            "Show hidden text", lambda: self.current_tab().show_blocks(),
            "Ctrl+Shift+K", "dialog-apply", "Show hidden text")
        edit_show_action.setEnabled(False)
        self.tabs.showAvailable.connect(edit_show_action.setEnabled)
        edit_bookmark_action = self.create_action(
            "Toggle bookmark", lambda: self.current_tab().bookmark(),
            "Ctrl+B", "help-about", "Toggle bookmark on/off")
        
        self.add_actions(edit_menu, (edit_undo_action, edit_redo_action, None,
                          edit_cut_action, edit_copy_action, edit_paste_action,
                          None, edit_selectall_action, None, edit_comment_action,
                          edit_uncomment_action, None, edit_indent_action,
                          edit_unindent_action, None, edit_gotoline_action,None,
                          edit_hide_action, edit_show_action, edit_bookmark_action))

        self.add_actions(edit_tool_bar,(edit_copy_action, edit_cut_action, 
                                     edit_paste_action, None, edit_find_action,
                                     edit_replace_action, None, 
                                     edit_undo_action, edit_redo_action, None,
                                     edit_hide_action, edit_show_action,
                                     edit_bookmark_action))

        self.add_actions(self.view_menu, (edit_tool_bar.toggleViewAction(),))
        
    def create_doc_widgets(self):
        bookmark_widget = BookmarksPane(self)
        self.tabs.bookmarksUpdated.connect(bookmark_widget.update_bookmarks)
        bookmark_widget.jumpRequested.connect(self.current_tab().goto_line)
        bookmark_dockwidget = QDockWidget("Bookmarks", self)
        bookmark_dockwidget.setObjectName("bookmarks_dockwidget")
        bookmark_dockwidget.setAllowedAreas(Qt.LeftDockWidgetArea|Qt.RightDockWidgetArea)
        bookmark_dockwidget.setWidget(bookmark_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, bookmark_dockwidget)
        action = bookmark_dockwidget.toggleViewAction()
        self.view_menu.addAction(action)
        
    def send_commands(self):
        commands = self.current_tab().textCursor().selectedText()
        if not commands.isEmpty():
            self.outputCommands.emit(commands)
        clipboard = QApplication.clipboard()
        clipboard.setText(commands)
        
    def current_tab(self):
        return self.tabs.widget(self.tabs.currentIndex())
        
    def create_help_actions(self, console=True):
        help_menu = self.menuBar().addMenu("&Help")

        help_search_action = self.create_action("&Help", self.help_search,
            QKeySequence.HelpContents, "help-contents", "Commands help")
        help_about_action = self.create_action("&About", self.help_about,
            icon="help-about", tip="About editR")
            
        self.add_actions(help_menu, (help_search_action, help_about_action,))

    def update_indicators(self):
        lines = self.current_tab().document().blockCount()
        cursor = self.current_tab().textCursor()
        self.column_count_label.setText("Column %d" % (cursor.columnNumber()+1))
        if lines == 0:
            text = "(empty)"
        else:
            text = "Line %d of %d " % (cursor.blockNumber()+1, lines)
        self.line_count_label.setText(text)
        
    def update_statusbar(self, text, extra):
        self.statusBar().showMessage(text+extra)
        
    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()",
                     param=None):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":%s" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            if param is not None:
                self.connect(action, SIGNAL(signal), slot, param)
            else:
                self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        self.addAction(action)
        return action

    def help_search(self):
        browser = HelpBrowser(self, self.paths)
        browser.show()

    def help_about(self):
        browser = AboutBrowser(self, __version__, __license__, __currentdir__)
        browser.exec_()
        
    def file_modified(self, mod):
        name = self.tabs.tabText(self.tabs.currentIndex())
        if name.startsWith("*"):
            if not mod:
                self.tabs.setTabText(self.tabs.currentIndex(), name[1:])
        else:
            if mod:
                self.tabs.setTabText(self.tabs.currentIndex(), "*%s" % name)

    def file_new(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        editor = REditor(self)
        editor.highlight = QSettings().value("manageR/enablehighlighting", 
                                             True).toBool()
        if editor.highlight:
            validator = Validator(editor)
            validator.found_bookmark.connect(editor.bookmark)
            highlighter = Highlighter(editor)
        editor.tabwidth = QSettings().value("manageR/tabwidth", 4).toInt()[0]
        editor.autobracket = QSettings().value("manageR/bracketautocomplete", 
                                               True).toBool()
        count = 1
        for i in range(self.tabs.count()):
            if self.tabs.widget(i).file_path == "Untitled-%s" % count:
                count += 1
            else:
                break
        name = "Untitled-%s" % count
        index = self.tabs.addTab(editor, QIcon(":text-x-generic"), name)
        editor.file_path = name
        editor.setFocus()
        self.tabs.setCurrentIndex(index)
        self.statusBar().showMessage("New script", 5000)
        QApplication.restoreOverrideCursor()

    def file_open(self, path=None):
        if path is None:
            path = QFileDialog.getOpenFileName(self,
                            "editR - Open File",
                            unicode(robjects.r.getwd()[0]),
                            "R scripts (*.R,*.r);;All files (*)")
        if path.isEmpty():
            return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        info = QFileInfo(path)
        # this should give the _full_ name, even with 'extra' dots...
        name = info.baseName() + "." + info.completeSuffix()
        
        # to prevent opening the same file twice
        for i in range(self.tabs.count()):
            if self.tabs.widget(i).file_path == path:
                self.tabs.setCurrentIndex(i)
                self.statusBar().showMessage("Showing %s" % name, 5000)
                QApplication.restoreOverrideCursor()
                return
        self.file_load(info.absoluteFilePath())
        self.statusBar().showMessage("Opened %s" % path, 5000)
        QApplication.restoreOverrideCursor()
        
    def file_load(self, path=None):
        if path is None:
            return
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        info = QFileInfo(path)
        if not info.exists():
            return
        name = info.baseName() + "." + info.completeSuffix()
        if not (self.tabs.count() == 1 and \
            self.tabs.widget(0).file_path.contains(QRegExp(r"^Untitled-\d{1,2}$"))):
            self.file_new()
        fh = None
        try:
            try:
                fh = QFile(path)
                if not fh.open(QIODevice.ReadOnly):
                    raise IOError, unicode(fh.errorString())
                stream = QTextStream(fh)
                stream.setCodec("UTF-8")
                text = stream.readAll()
                self.tabs.setTabText(self.tabs.currentIndex(), name)
                tab = self.current_tab()
                tab.file_path = path
                tab.setPlainText(text)
                tab.document().setModified(False)
            except (IOError, OSError), err:
                QMessageBox.warning(self, "editR - Load Error",
                        "Failed to load %s: %s" % (path, err))
        finally:
            if fh is not None:
                fh.close()
        self.setWindowModified(False)
        QApplication.restoreOverrideCursor()

    def file_saveas(self, path=None):
        if path is None:
            name = self.current_tab().file_path
            path = QFileDialog.getSaveFileName(self,
                   "editR - Save File As",
                   "%s.R" % name, "*.R;;*.r")
        if path.isEmpty():
            return False
        return self.file_save(path)

    def file_save(self, path=None):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        if path is None:
            path = QString(self.current_tab().file_path)
        if path.contains(QRegExp(r"^Untitled-\d{1,2}$")):
            QApplication.restoreOverrideCursor()
            return self.file_saveas()
        path = QDir(path).absolutePath()
        if QFile.exists(path):
            backup = "%s%s" % (path, QSettings().value("manageR/backupsuffix", "~").toString())
            ok = True
            if QFile.exists(backup):
                ok = QFile.remove(backup)
                if not ok:
                    QMessageBox.information(self,
                            "editR - Save Warning",
                            "Failed to remove existing backup file %s" % backup)
            if ok:
                # Must use copy rather than rename to preserve file
                # permissions; could use rename on Windows though
                if not QFile.copy(path, backup):
                    QMessageBox.information(self,
                            "editR - Save Warning",
                            "Failed to save backup file %s" % backup)
        fh = None
        try:
            try:
                fh = QFile(path)
                if not fh.open(QIODevice.WriteOnly):
                    raise IOError, unicode(fh.errorString())
                stream = QTextStream(fh)
                stream.setCodec("UTF-8")
                stream << self.current_tab().toPlainText()
                self.current_tab().document().setModified(False)
                self.setWindowModified(False)
                info = QFileInfo(path)
                name = info.baseName() + "." + info.completeSuffix()
                self.current_tab().file_path = path
                self.tabs.setTabText(self.tabs.currentIndex(), name)
                self.statusBar().showMessage("Saved %s" % path, 5000)
            except (IOError, OSError), e:
                QMessageBox.warning(self, "editR - Save Error",
                        "Failed to save %s: %s" % (path, e))
        finally:
            if fh is not None:
                fh.close()
        QApplication.restoreOverrideCursor()
        self.saved.emit()
        return True
        
    def file_close(self, index=None):
        if index is None:
            index = self.tabs.currentIndex()
        tab = self.tabs.widget(index)
        if tab.document().isModified():
            reply = QMessageBox.question(self, "editR - Unsaved changes",
                        "Do you want to save unsaved changes"
                        " to %s?" % self.tabs.tabText(index),
                        QMessageBox.Yes|QMessageBox.No|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                self.file_save()
        self.tabs.removeTab(index)
        if self.tabs.count() < 1: # if that was the last one
            self.file_quit()
        return True
        
    def tab_close(self, index):
        if self.tabs.count() == 1:
            reply = QMessageBox.question(self, "editR - Last tab",
                    "Are you sure you want to close the last tab?\n"
                    "This will quit editR.",
                    QMessageBox.Yes|QMessageBox.Cancel)
            if reply == QMessageBox.Cancel:
                return
        self.file_close()

    def file_quit(self):
        i = self.tabs.count()
        while self.tabs.count() > 0:
            i -= 1
            if not self.file_close(i):
                return False
        QSettings().setValue("manageR/toolbars", self.saveState())
        if QSettings().value("manageR/remembergeometry", True).toBool():
            QSettings().setValue("manageR/editorposition", self.pos())
            QSettings().setValue("manageR/editorsize", self.size())
        self.close()
        return True
        
    def closeEvent(self, event):
        if self.file_quit():
            event.accept()
        else:
            event.ignore()
            
def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    app.setOrganizationName("manageR")
    app.setOrganizationDomain("ftools.ca")
    app.setApplicationName("manageR")
    app.setWindowIcon(QIcon(":icon.png"))
    app.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
