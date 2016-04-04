# PyQt imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# os and system imports
import os, re, sys, platform, base64

# local (project) imports
from plain_text_edit import *
from complete import RCompleter
import resources

# rpy2 imports
import rpy2.robjects as robjects
import rpy2.rinterface as rinterface


class REditor(PlainTextEditor):

    showAvailable = pyqtSignal(bool)
    hideAvailable = pyqtSignal(bool)
    suggestionRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        PlainTextEditor.__init__(self, parent)
        self.completer = Completer(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.file_path = QString("Untitled")
        self.hidden = {}
        self.edit.tabPressed.connect(self.suggestionRequested)
        self.suggestionRequested.connect(self.completer.suggest)
        self.edit.selectionChanged.connect(self.hide_availability)
        self.edit.blockChanged.connect(self.show_availability)
        self.layout().setContentsMargins(0,0,0,0)
        
    def contextMenuEvent(self, event):
        cursor = self.textCursor()
        tmp = QTextCursor(cursor)
        menu = self.edit.createStandardContextMenu()
        keyword_action = QAction(QIcon(":gtk-edit"), "Insert keywords", menu)
        inside, word = self.guess_function(tmp)
        keyword_action.setEnabled(not word.isEmpty())
        keyword_action.triggered.connect(lambda: 
            self.insert_parameters(inside,word,cursor))
        hide_action = QAction(QIcon(":window-close"), "Hide selected text", menu)
        hide_action.triggered.connect(self.hide_blocks)
        hide_action.setEnabled(False)
        show_action = QAction(QIcon(":dialog-apply"), "Show hidden text", menu)
        show_action.triggered.connect(self.show_blocks)
        show_action.setEnabled(False)
        if cursor.hasSelection():
            pos1 = cursor.selectionStart()
            pos2 = cursor.selectionEnd()
            top = self.document().findBlock(pos2)
            bottom = self.document().findBlock(pos1)
            if not top == bottom:
                hide_action.setEnabled(True)
        if cursor.block().blockNumber() in self.hidden:
            show_action.setEnabled(True)
        menu.addSeparator()
        menu.addAction(keyword_action)
        menu.addSeparator()
        menu.addAction(hide_action)
        menu.addAction(show_action)
        menu.exec_(event.globalPos())
        return event.accept()
        
#    def position_changed(self):
#        cursor = self.textCursor()
#        pos1 = cursor.selectionStart()
#        pos2 = cursor.selectionEnd()
#        top = self.document().findBlock(pos2)
#        bottom = self.document().findBlock(pos1)
#        self.can_hide.emit(top == bottom and cursor.hasSelection())
#        self.can_show.emit(cursor.block().blockNumber() in self.hidden)
#        PlainTextEditor.position_changed(self)

    def hide_availability(self):
        cur = self.textCursor()
        sel = cur.hasSelection()
        doc = self.document()
        start = cur.selectionStart()
        end = cur.selectionEnd()
        same = doc.findBlock(start) == doc.findBlock(end)
        self.hideAvailable.emit(sel and not same)
        
    def show_availability(self):
        block = self.textCursor().block().blockNumber()
        self.showAvailable.emit(block in self.hidden)

    def insert_parameters(self, inside, word, cursor):
        if not inside:
            cursor.movePosition(QTextCursor.EndOfWord)
        if not word.isEmpty():
            args = self.function_arguments(word).remove("\n")
            if inside:
                args = args[1:-1]
            if not args.isEmpty():
                self.setTextCursor(cursor)
                self.insertPlainText(args)
                
    def show_blocks(self):
        cursor = self.textCursor()
        line = cursor.blockNumber()
        if not line in self.hidden:
            return
        for i in self.hidden[line]:
            block = self.document().findBlockByNumber(i)
            block.setVisible(True)
        self.hidden.pop(line)
        self.edit.viewport().update()
        self.side_panel.update()
                
    def hide_blocks(self):
        cursor = self.textCursor()
        if not cursor.hasSelection() or cursor.hasComplexSelection():
            return # can't hide non-contiguous blocks
        pos1 = cursor.selectionStart()
        pos2 = cursor.selectionEnd()
        top = self.document().findBlock(min(pos1, pos2))
        bottom = self.document().findBlock(max(pos1, pos2))
        if top == bottom:
            return
        start = top.blockNumber()
        end = bottom.blockNumber()
        cursor.clearSelection()
        cursor.setPosition(min(pos1, pos2))
        blocks = []
#        print start, range(start+1, end+1)
        for line in range(start+1, end+1):
            block = self.document().findBlockByNumber(line)
            if block.isVisible():
                block.setVisible(False)
                blocks.append(block.blockNumber())
        self.hidden[start] = blocks# store hidden blocks
        self.setTextCursor(cursor)
        self.edit.viewport().update()
        self.side_panel.update()

    def update_sidepanel(self, panel, event):
        metrics = self.fontMetrics()
        pos = self.edit.textCursor().position()
        line = self.document().findBlock(pos).blockNumber()+1

        block = self.edit.firstVisibleBlock()
        count = block.blockNumber()
        painter = QPainter(panel)
        palette = self.parent().palette()
        color = palette.color(QPalette.Normal, QPalette.AlternateBase)
#        painter.fillRect(event.rect(), color)

        # iterate over all visible text blocks in the document
        while block.blockNumber()>=0:
            count += 1
            bound = self.edit.blockBoundingGeometry(block)
            top = bound.translated(self.edit.contentOffset()).top()
            # check position of block is outside visible area.
            if top >= event.rect().bottom():
                break
            if block.isVisible():
                pixmap = QPixmap()
                rect = QRect(panel.width()-11, top+3, 11, 11)
                if block.blockNumber() in self.hidden:
                    pixmap.load(":custom-triangle")
#                    painter.drawText(rect, Qt.AlignLeft, "+")
                    painter.drawPixmap(rect, pixmap)
                if block.blockNumber() in self.bookmarks["user"]:
                    pixmap.load(":custom-placeholder")
#                    painter.drawText(rect, Qt.AlignLeft, "+")
                    painter.drawPixmap(rect, pixmap)
                # draw line number right justified at position of line
                painter.setPen(palette.color(QPalette.Normal, QPalette.Text))
                user_data = block.userData()
                if user_data:
                    if user_data.data == "syntax":
                        if block == self.textCursor().block():
                            painter.setPen(QPen(QColor("orange")))
                        else:
                            painter.setPen(QPen(QColor("red")))
                rect = QRect(0, top, panel.width()-20, metrics.height())
                painter.drawText(rect, Qt.AlignRight, unicode(count))
            block = block.next()
        painter.end()
       
    def current_command(self, block, cursor=None):
        command = QString(block.text())
        if not cursor is None:
            pos1 = cursor.position()
        else:
            pos1 = self.textCursor().position()
        pos2 = block.position()
        block = block.previous()
        while block.isValid():
            user_data = block.userData()
            if not user_data: # we'll assume this is ok
                break
            if not user_data.data == "continue": # we're good
                break
            if not block.text().trimmed().isEmpty():
                command.prepend("%s\n" % block.text())
            pos2 = block.position()
            block = block.previous()
        return (command, pos1-pos2)

    def function_arguments(self, fun):
        cmd = 'do.call(argsAnywhere, list("%s"))' % fun
        try:
            
            args = QString(str(robjects.r(cmd)))
            if args.contains("function"):
                regexp = QRegExp(r"function\s\(")
                start = regexp.lastIndexIn(args)
                regexp = QRegExp(r"\)")
                end = regexp.lastIndexIn(args)
                args = args[start:end+1].replace("function ", "") # removed fun
            else:
                args = args.replace("\n\n", "").remove("NULL")
        except Exception, err:
            args = QString()
        return args
        
    def guess_current_word(self, cursor):
        pos = cursor.position() - cursor.block().position()
        cursor.select(QTextCursor.LineUnderCursor)
        line = cursor.selectedText()
        prefix = line[0:pos]
        suffix = line[pos:]
        regstart = QRegExp(QString("[^\w\.]"))
        regend = QRegExp(QString("[^\w\.]"))
        start = regstart.lastIndexIn(prefix)
        if start < 0: start = 0
        end = regend.indexIn(suffix)
        if end < 0: end = len(suffix)
        return line[start:len(prefix)+end].trimmed()
        
    def guess_function(self, cursor):
        pos = cursor.position() - cursor.block().position()
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.KeepAnchor)
        line = cursor.selectedText()
        open_bracket = line.count("(")
        close_bracket = line.count(")")
        wp = open_bracket-close_bracket
        found = False
        fun_name = QString()
        if wp > 0: # probably inside function
            index = line.lastIndexOf("(")
            prefix = line[0:index]
            suffix = line[index+1:]
            regexp = QRegExp(r"[^\.\w]")
            possible = list(prefix.split(regexp, QString.SkipEmptyParts))
            if len(possible) > 0:
                found = True
                fun_name = QString(possible[-1])
            return found, fun_name
        else: # not inside function
            return found, self.guess_current_word(cursor)
        
class Completer(QObject):

    completed = pyqtSignal(QString,QString)
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        
        self.delay = 1000
        self.minchars = 3
        self.active = True

        self.popup = QListWidget()
        self.popup.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.popup.setSelectionBehavior(QTreeWidget.SelectRows)
        self.popup.setFrameStyle(QFrame.Box|QFrame.Plain)
        self.popup.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.popup.installEventFilter(self)
        self.popup.setMouseTracking(True)
        self.popup.setWindowFlags(Qt.Popup)
        self.popup.setFocusPolicy(Qt.NoFocus)
        self.popup.setFocusProxy(self.parent())
        self.popup.itemClicked.connect(self.done_completion)
        self.current = ""

        if self.active:
            self.timer = QTimer(self)
            self.timer.setSingleShot(True)
            self.timer.setInterval(self.delay)

            self.timer.timeout.connect(self.suggest, self.minchars)
            self.parent().textChanged.connect(self.start_timer)
        else:
            self.timer = None
            
    def start_timer(self):
        if not self.timer is None:
            self.timer.start()

    def eventFilter(self, obj, event):
        if not obj == self.popup:
            return False
        if event.type() == QEvent.MouseButtonPress:
            self.popup.hide()
            self.parent().setFocus()
            return True
        if event.type() == QEvent.KeyPress:
            consumed = False
            key = event.key()
            if key == Qt.Key_Enter or key == Qt.Key_Return:
                self.done_completion()
                consumed = True
            elif key == Qt.Key_Escape:
                self.parent().setFocus()
                self.popup.hide()
                consumed = True
            elif key == Qt.Key_Up or key == Qt.Key_Down or \
                 key == Qt.Key_Home or key == Qt.Key_End or \
                 key == Qt.Key_PageUp or key == Qt.Key_PageDown:
                pass
            else:
                # pass on to underlying editor (and keep suggesting)
                self.parent().edit.event(event)
                self.suggest(1)
            return consumed
        return False

    def show_completion(self, choices):
        if not self.timer is None:
            active = self.timer.isActive()
        else:
            active = True
        if len(choices) == 1 and active and not self.popup.isVisible():
            self.replace_current_word(choices[0])
            self.prevent_suggest()
            self.done_completion.emit(QString(unicode(choices[0])),QString())
            return
        pal = self.parent().palette()
        color = pal.color(QPalette.Disabled, QPalette.WindowText)
        self.popup.clear()
        self.popup.insertItems(0,choices)
        self.popup.setCurrentRow(0)
        self.popup.adjustSize()

        h = self.popup.sizeHintForRow(0)*min([7, len(choices)])+3
        self.popup.resize(self.popup.width(), h)
        loc = self.parent().edit.cursorRect().bottomRight()
        self.popup.move(self.parent().mapToGlobal(loc))
        self.popup.setFocus()
        self.popup.show()

    def done_completion(self):
        if not self.timer is None:
            self.timer.stop()
        self.popup.hide()
        self.parent().setFocus()
        item = self.popup.currentItem()
        #self.editor.parent.statusBar().showMessage(
        #item.data(0, Qt.StatusTipRole).toString().\
        #replace("function", item.text()))
        if item:
            self.replace_current_word(item.text())
            self.prevent_suggest()
            self.current = item
            self.completed.emit(QString(unicode(item.text())),QString())

    def prevent_suggest(self):
        if not self.timer is None:
            self.timer.stop()

    def suggest(self, minchars=None):
        if minchars is None:
            minchars = self.minchars
        block = self.parent().textCursor().block()
        text = block.text()
        if len(text) < minchars:
            return
        line_buffer, cursor = self.parent().current_command(block)
        if QString(line_buffer).trimmed().isEmpty():
            return
        completer = RCompleter(line_buffer)
        if not completer.can_suggest or len(completer.token) < minchars:
            return
        self.move = len(completer.token)
        comps = completer.complete_token()
        comps.sort()
        if len(comps) < 1:
            return
        elif len(comps) == 1 and comps[0] == completer.token:
            return
        del completer
        self.show_completion(comps)

    def replace_current_word(self, word):
        cursor = self.parent().textCursor()
        cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, self.move)
        cursor.removeSelectedText()
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        sel = cursor.selectedText()
        if not word[-1] == sel and not sel.isEmpty():
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
        self.parent().setTextCursor(cursor)
        self.parent().insertPlainText(word)
        
class Validator(QSyntaxHighlighter):

    found_bookmark = pyqtSignal(int, str)

    def __init__(self, parent=None):
        QSyntaxHighlighter.__init__(self, parent)
        self.setDocument(parent.document())
        
    def check_syntax(self, text):
        block = self.currentBlock()
        block = block.previous()
        user_data = block.userData()
        if user_data:
            if user_data.data == "continue":
                self.setCurrentBlockUserData(UserData("continue"))
        try: # if this works, then syntax is correct
            temp = rinterface.get_writeconsole()
            def f(x): pass
            rinterface.set_writeconsole(f)
            robjects.r.parse(text=unicode(text))
            rinterface.set_writeconsole(temp)
        except robjects.rinterface.RRuntimeError, err:
            err = QString(unicode(err))
            if err.contains("unexpected end of input"):
                self.setCurrentBlockUserData(UserData("continue"))
                return
            err = err.split(":", QString.SkipEmptyParts)[1:].join(" ")
            if err.startsWith("\n"): err = err[1:]
            self.setCurrentBlockUserData(UserData("syntax", err))
        
    def running_command(self, block):
        command = QString(block.text())
        block = block.previous()
        while block.isValid():
            user_data = block.userData()
            if not user_data: break # we'll assume this is ok
            if not user_data.data == "continue": break # we're good
            if not block.text().trimmed().isEmpty():
                command.prepend("%s\n" % block.text())
            block = block.previous()
        if not block.isValid():
            block = self.parent().document().begin()
        else:
            block = block.next()
        return command, block
        
    def check_bookmarks(self, block):
        text = block.text()
        regexp = QRegExp(r".*<-\s*function\(.*")
        if text.contains(regexp):
            self.found_bookmark.emit(block.blockNumber(), "auto")
        
    def highlightBlock(self, text):
        # so far, nothing special...
        self.setCurrentBlockUserData(UserData("normal"))
        block = self.currentBlock()
        current, block = self.running_command(block)
        self.check_syntax(current)
        self.check_bookmarks(block)

    def rehighlight(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QSyntaxHighlighter.rehighlight(self)
        QApplication.restoreOverrideCursor()
        
def main():
    app = QApplication(sys.argv)
    if not sys.platform.startswith(("linux", "win")):
        app.setCursorFlashTime(0)
    app.setOrganizationName("manageR")
    app.setOrganizationDomain("ftools.ca")
    app.setApplicationName("manageR")
    app.setWindowIcon(QIcon(":icon.png"))
    app.connect(app, SIGNAL('lastWindowClosed()'), app, SLOT('quit()'))
    window = QMainWindow()
    editor_one = REditor(window)
    editor_two = REditor(window)
    validator_one = Validator(editor_one)
    validator_two = Validator(editor_two)
    highlighter_one = Highlighter(editor_one)
    highlighter_two = Highlighter(editor_two)
    
    # main settings
    fontfamily = QSettings().value("manageR/fontfamily", "DejaVu Sans Mono").toString()
    fontsize = QSettings().value("manageR/fontsize", 10).toInt()[0]
    tabwidth = QSettings().value("manageR/tabwidth", 4).toInt()[0]
    autobracket = QSettings().value("manageR/bracketautocomplete", True).toBool()
    delay = QSettings().value("manageR/delay", 1000).toInt()[0]
    chars = QSettings().value("manageR/minimumchars", 3).toInt()[0]

    tabs = QTabWidget(window)
    tabs.addTab(editor_one, "Editor 1")
    tabs.addTab(editor_two, "Editor 2")
    editor_one.setFont(QFont(fontfamily, fontsize))
    editor_two.setFont(QFont(fontfamily, fontsize))
    
    editor_one.tabwidth = tabwidth
    editor_one.autobracket = autobracket
    editor_one.highlight = QSettings().value("manageR/enablehighlighting", True).toBool()
    window.setCentralWidget(tabs)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

