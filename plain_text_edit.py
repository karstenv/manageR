# PyQt imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *

# os and system imports
import os, re, sys, platform, base64

class PlainTextEdit(QPlainTextEdit):
    
    returnPressed = pyqtSignal(QTextBlock)
    tabPressed = pyqtSignal(int)
    blockChanged =pyqtSignal() 

    def __init__(self, parent=None):
        QPlainTextEdit.__init__(self, parent)
        # these properties should be changed directly if need be
        self.tabwidth = 4
        self.autobracket = True
        self.highlight = True
        # allow line wrapping here, but may need to set to NoWrap for console
        #self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFrameShape(QTextEdit.NoFrame)
        # accept drops here, but may need to set to False for console
        self.setAcceptDrops(True)
        self.cursorPositionChanged.connect(self.highlight_parentheses)
        self.cursorPositionChanged.connect(self.check_block_change)
        # this makes sure parents get this instead
        self.setContextMenuPolicy(Qt.NoContextMenu) 
        self.block_number = 0

    def keyPressEvent(self, event):
        indent = " "*self.tabwidth
        cursor = self.textCursor()
        if event.key() == Qt.Key_Tab:
            if not self.tabChangesFocus():
                if not cursor.hasSelection():
                    cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
                    text = cursor.selectedText().trimmed()
                    if text.isEmpty():
                        self.insertPlainText(indent)
                    else:
                        self.tabPressed.emit(1)
                else:
                    self.indent_region()
            return
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            insert = "\n"
            line = cursor.block().text()
            if line.startsWith(indent):
                for c in line:
                    if c == " ":
                        insert += " "
                    else:
                        break
            block = cursor.block()
            self.returnPressed.emit(block) # in case we need to know this...
            cursor.insertText(insert)
            self.setTextCursor(cursor)
            return
        elif event.key() in (Qt.Key_ParenLeft,
                             Qt.Key_BracketLeft,
                             Qt.Key_BraceLeft):
            if self.autobracket:
                cursor.movePosition(QTextCursor.NextCharacter, 
                                    QTextCursor.KeepAnchor)
                insert = QString()
                if event.key() == Qt.Key_ParenLeft and \
                   cursor.selectedText().trimmed().isEmpty():
                    insert = QString(Qt.Key_ParenRight)
                elif event.key() == Qt.Key_BracketLeft and \
                     cursor.selectedText().trimmed().isEmpty():
                    insert = QString(Qt.Key_BracketRight)
                elif event.key() == Qt.Key_BraceLeft and \
                     cursor.selectedText().trimmed().isEmpty():
                    insert = QString(Qt.Key_BraceRight)
                cursor = self.textCursor()
                cursor.insertText("%s%s" % (QString(event.key()),insert))
                if not insert.isEmpty():
                    cursor.movePosition(QTextCursor.PreviousCharacter,
                                        QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
                return
        elif event.key() in (Qt.Key_QuoteDbl,
                             Qt.Key_Apostrophe):
            if self.autobracket:
                cursor.movePosition(QTextCursor.NextCharacter,
                                    QTextCursor.KeepAnchor)
                insert = QString()
                if event.key() == Qt.Key_QuoteDbl and \
                   cursor.selectedText().trimmed().isEmpty():
                    insert = QString(Qt.Key_QuoteDbl)
                elif event.key() == Qt.Key_Apostrophe and \
                     cursor.selectedText().trimmed().isEmpty():
                    insert = QString(Qt.Key_Apostrophe)
                cursor = self.textCursor()
                cursor.insertText("%s%s" % (QString(event.key()),insert))
                if not insert.isEmpty():
                    cursor.movePosition(QTextCursor.PreviousCharacter,
                    QTextCursor.MoveAnchor)
                self.setTextCursor(cursor)
                return
        QPlainTextEdit.keyPressEvent(self, event)
        
    def mousePressEvent(self, event):
        # Mask right click to left click so that the cursor will be moved
        # to the location of the mouse. This is necessary for the word under
        # the cursor to be selected.
        if event.button() == Qt.RightButton:
            event = QMouseEvent(QEvent.MouseButtonPress, event.pos(), 
                                Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QPlainTextEdit.mousePressEvent(self, event)
      
    def highlight_line(self):
        selection = QTextEdit.ExtraSelection()

        selection.format.setBackground(self.palette().alternateBase())
        selection.format.setProperty(QTextFormat.FullWidthSelection, 
                                         QVariant(True))
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def check_block_change(self):
        cur = self.textCursor().block()
        if not cur == self.block_number:
            self.blockChanged.emit()
        self.block_number = cur

    def highlight_parentheses(self):
        extraSelections = []        
        self.setExtraSelections(extraSelections)
        if not self.highlight:
            return
        self.highlight_line()
        format = QTextCharFormat()
        format.setBackground(QColor(Qt.yellow).lighter(160))
        first_selection = QTextEdit.ExtraSelection()
        first_selection.format = format
        second_selection = QTextEdit.ExtraSelection()
        second_selection.format = format
        doc = self.document()
        cursor = self.textCursor()
        before_cursor = QTextCursor(cursor)

        cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        brace = cursor.selectedText()

        before_cursor.movePosition(QTextCursor.PreviousCharacter, 
                                   QTextCursor.KeepAnchor)
        before_brace = before_cursor.selectedText()

        if ((brace != "{") and \
            (brace != "}") and \
            (brace != "[") and \
            (brace != "]") and \
            (brace != "(") and \
            (brace != ")")):
            if ((before_brace == "{") or \
                (before_brace == "}") or \
                (before_brace == "[") or \
                (before_brace == "]") or \
                (before_brace == "(") or \
                (before_brace == ")")):
                cursor = before_cursor
                brace = cursor.selectedText();
            else:
                return

        #format = QTextCharFormat()
        #format.setForeground(Qt.red)
        #format.setFontWeight(QFont.Bold)

        if ((brace == "{") or (brace == "}")):
            open_brace = "{"
            close_brace = "}"
        elif ((brace == "[") or (brace == "]")):
            open_brace = "["
            close_brace = "]"
        elif ((brace == "(") or (brace == ")")):
            open_brace = "("
            close_brace = ")"

        if (brace == open_brace):
            cursor1 = doc.find(close_brace, cursor)
            cursor2 = doc.find(open_brace, cursor)
            if (cursor2.isNull()):
                first_selection.cursor.clearSelection()
                first_selection.cursor = cursor
                if (not cursor1.isNull()):
                    extraSelections.append(first_selection)
                #self.setExtraSelections(extraSelections)
                second_selection.cursor.clearSelection()
                second_selection.cursor = cursor1
                extraSelections.append(second_selection)
                self.setExtraSelections(extraSelections)
            else:
                while (cursor1.position() > cursor2.position()):
                    cursor1 = doc.find(close_brace, cursor1)
                    cursor2 = doc.find(open_brace, cursor2)
                    if (cursor2.isNull()):
                        break
                first_selection.cursor.clearSelection()
                first_selection.cursor = cursor
                if (not cursor1.isNull()):
                    extraSelections.append(first_selection)
                #self.setExtraSelections(extraSelections)
                second_selection.cursor.clearSelection()
                second_selection.cursor = cursor1
                extraSelections.append(second_selection)
                self.setExtraSelections(extraSelections)

        else:
            if (brace == close_brace):
                cursor1 = doc.find(open_brace, cursor, 
                                   QTextDocument.FindBackward)
                cursor2 = doc.find(close_brace, cursor, 
                                   QTextDocument.FindBackward)
                if (cursor2.isNull()):
                    first_selection.cursor.clearSelection()
                    first_selection.cursor = cursor
                    if (not cursor1.isNull()):
                        #cursor.mergeCharFormat(syntaxformat)
                    #else:
                        extraSelections.append(first_selection)
                   # self.setExtraSelections(extraSelections)
                    second_selection.cursor.clearSelection()
                    second_selection.cursor = cursor1
                    extraSelections.append(second_selection)
                    self.setExtraSelections(extraSelections)
                else:
                    while (cursor1.position() < cursor2.position()):
                        cursor1 = doc.find(open_brace, cursor1,
                                           QTextDocument.FindBackward)
                        cursor2 = doc.find(close_brace, cursor2,
                                           QTextDocument.FindBackward)
                        if (cursor2.isNull()):
                            break
                    first_selection.cursor.clearSelection()
                    first_selection.cursor = cursor
                    if (not cursor1.isNull()):
                        #cursor.mergeCharFormat(syntaxformat)
                    #else:
                        extraSelections.append(first_selection)
                    #self.setExtraSelections(extraSelections)
                    second_selection.cursor.clearSelection()
                    second_selection.cursor = cursor1
                    extraSelections.append(second_selection)
                    self.setExtraSelections(extraSelections)

    def goto_line(self, line=None):
        cursor = self.textCursor()
        ok = True
        if line is None:
            line, ok = QInputDialog.getInteger(self,
                    "Goto line", "Goto line:", cursor.blockNumber()+1, 1,
                    self.document().blockCount())
        if ok:
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, 
                                QTextCursor.MoveAnchor, line-1)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()

    def indent_region(self):
        self.walk_the_lines(True, " "*self.tabwidth)

    def unindent_region(self):
        self.walk_the_lines(False, " "*self.tabwidth)

    def comment_region(self):
        self.walk_the_lines(True, "# ")

    def uncomment_region(self):
        self.walk_the_lines(False, "# ")

    def walk_the_lines(self, insert, text):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        start = cursor.position()
        end = cursor.anchor()
        if start > end:
            start, end = end, start
        block = self.document().findBlock(start)
        while block.isValid():
            cursor = QTextCursor(block)
            cursor.movePosition(QTextCursor.StartOfBlock)
            if insert:
                cursor.clearSelection()
                cursor.insertText(text)
            else:
                # also look for lines with leading whitespace
                regexp = QRegExp(r"^\s*%s" % text)
                if block.text().contains(regexp):
                    cursor = self.document().find(text, cursor)
                    if cursor.selectedText() == text:
                        cursor.removeSelectedText()
            block = block.next()
            if block.position() > end:
                break
        cursor.endEditBlock()
        
class Highlighter(QSyntaxHighlighter):

    def __init__(self, parent=None):
        QSyntaxHighlighter.__init__(self, parent)
        self.setDocument(parent.document())
        self.initialize_formats()
        rules = []
        rules.append((r"[a-zA-Z_]+[a-zA-Z_\.0-9]*(?=[\s]*[(])", "keyword"))
        rules.append((r"\b%s\b" % "else","keyword"))
        # other keywords can be added above
        builtins = ["array", "character", "complex", "data.frame", "double",
                    "factor", "function", "integer", "list", "logical",
                    "matrix", "numeric", "vector", "numeric"]
        rules.append(("|".join([r"\b%s\b" % b for b in builtins]), "builtin"))
        # constants
        constants = ["Inf", "NA", "NaN", "NULL", "TRUE", "FALSE"]
        rules.append(("|".join([r"\b%s\b" % c for c in constants]), "constant"))
        # numbers
        rules.append((r"\b[+-]?[0-9]+[lL]?\b"
                     r"|\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b"
                     r"|\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b",
                     "number"))
        # delimiters
        rules.append((r"[\)\(]+|[\{\}]+|[][]+", "delimiter"))
        # assignment operators
        rules.append((r"[<]{1,2}\-|\-[>]{1,2}|=(?!=)|\$|\@", "assignment"))
        # syntax errors
        rules.append((r"([\+\-\*/\^\:\$~!&\|=>@^])([<]{1,2}\-|\-[>]{1,2})"
                      r"|([<]{1,2}\-|\-[>]{1,2})([\+\-\*/\^\:\$~!&\|=<@])"
                      r"|([<]{3}|[>]{3})|([\+\-\*/\^\:\$~&\|@^])="
                      r"|=([\+\-\*/\^\:\$~!<>&\|@^])", "syntax"))
        # single line brackets (syntax)
        rules.append((r"[a-zA-Z_\.][0-9a-zA-Z_\.]*[\s]*=(?=([^=]|$))", "inbrackets"))
        # double quoted strings (on one line)
#        rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', 'string'))
#        # single-quoted strings (on one line)
#        rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", 'string'))
        # comments
        rules.append((r"#.*", "comment"))
        # put these all into the self.rules list
        self.rules = [(QRegExp(e), 0, self.formats[f]) for e, f in rules]
        # now for the more complicated multiline strings and brackets
        self.multiline_single = (QRegExp(r"""'"""),1, self.formats["string"])
        self.multiline_double = (QRegExp(r'''"'''), 2, self.formats["string"])
        self.bracket_both = QRegExp(r"[\(\)]")
        self.bracket_start = QRegExp(r"\(")
        self.bracket_end = QRegExp(r"\)")
        

    def highlightBlock(self, text):
        # so far, nothing special...
        self.setCurrentBlockState(0)
        for exp, nth, format in self.rules:
            index = exp.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = exp.pos(nth)
                cap = exp.cap(nth)
                length = cap.length()                    
                self.setFormat(index, length, format)
                index = exp.indexIn(text, index + length)
                if cap.startsWith("#"):
                    self.setCurrentBlockState(3)
                    break

        # multiline strings
        in_multiline = self.match_multiline(text, *self.multiline_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.multiline_double)

    def match_multiline(self, text, delimiter, in_state, style):
        # if inside quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # otherwise, look for the delimiter on this line
        elif self.currentBlockState() == 3:
            return False
        else:
            start = delimiter.indexIn(text)
            # move past this match
            add = delimiter.matchedLength()

        # while there's a delimiter match on this line...
        while start >= 0:
            # look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
                # apply formatting
                self.setFormat(start, length-add, style)
            else:
                self.setCurrentBlockState(in_state)
                length = text.length() - start + add
                # apply formatting
                self.setFormat(start, length, style)
            # look for the next match
            start = delimiter.indexIn(text, start + length)

        # return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        return False

    def rehighlight(self):
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        QSyntaxHighlighter.rehighlight(self)
        QApplication.restoreOverrideCursor()
        
    def initialize_formats(self):
        self.formats = dict()
        base = QTextCharFormat()
        base.setFontFamily(QSettings().value("manageR/fontfamily", 
                                             "DejaVu Sans Mono").toString())
        base.setFontPointSize(QSettings().value("manageR/fontsize", 
                                                      10).toInt()[0])
        settings = QSettings()
        for name, color, bold, italic in (
                ("normal", "#000000", False, False),
                ("keyword", "#000080", True, False),
                ("builtin", "#0000A0", False, False),
                ("constant", "#0000C0", False, False),
                ("delimiter", "#0000E0", False, False),
                ("comment", "#007F00", False, True),
                ("string", "#808000", False, False),
                ("number", "#924900", False, False),
                ("error", "#FF0000", False, False),
                ("assignment", "#50621A", False, False),
                ("syntax", "#FF0000", False, True)):
            format = QTextCharFormat(base)
            col = QColor(settings.value("manageR/%sfontcolor" % name, 
                                        color).toString())
            format.setForeground(col)
            if name == "syntax":
                under = settings.value("manageR/%sfontunderline" % name, 
                                       bold).toBool()
                format.setFontUnderline(under)
            else:
                if settings.value("manageR/%sfontbold" % name, bold).toBool():
                    format.setFontWeight(QFont.Bold)
            itl = settings.value("manageR/%sfontitalic" % name, 
                                    italic).toBool()
            format.setFontItalic(itl)
            self.formats[name] = format

        format = QTextCharFormat(base)
        if settings.value("manageR/assignmentfontbold").toBool():
            format.setFontWeight(QFont.Bold)
        col =QColor(settings.value("manageR/assignmentfontcolor").toString())
        format.setForeground(col)
        itl = settings.value("manageR/%sfontitalic" % name).toBool()
        format.setFontItalic(itl)
        self.formats["inbrackets"] = format
        
class UserData(QTextBlockUserData):

    def __init__(self, data=None, extra=None):
        QTextBlockUserData.__init__(self)
        self.data = data
        self.extra = extra

    def has_extra(self):
        return not self.extra is None
        
class SidePanel(QWidget):
    
    paintEventSignal = pyqtSignal(QWidget, QEvent)

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.adjust_width(10)

    def paintEvent(self, event):
        self.paintEventSignal.emit(self, event)
#        self.parent().update_sidepanel(self, event)
        QWidget.paintEvent(self, event)
        
    def event(self, event):
        if event.type() == QEvent.ToolTip:
            cursor = self.parent().edit.cursorForPosition(QPoint(0,event.y()))
            block = cursor.block()
            data = block.userData()
            if data:
                if data.has_extra():
                    QToolTip.showText(event.globalPos(), data.extra)
        return QWidget.event(self, event)
        
    def adjust_width(self, count):
        if count < 10:
            count += 10
        width = self.fontMetrics().width(unicode(count))+20
        if self.width() != width:
            self.setFixedWidth(width)

    def update_contents(self, rect, scroll):
        if scroll:
            self.scroll(0, scroll)
        else:
            self.update(0, rect.y(), self.width(), rect.height())

class SearchBar(QWidget):

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        # create search elements

        self.search_edit = QLineEdit(self)
        self.search_edit.setToolTip("Find text")
        self.search_edit.setPlaceholderText("Search...")
        self.search_edit.setStyleSheet(
        "QLineEdit{"
        "padding-right: 16px;"
        "padding-left: 5px;"
        "background: url(:edit-find-small.png);"
        "background-position: right;"
        "background-repeat: no-repeat;"
        "border: 1px solid grey;"
        "border-radius: 6.5px;}")
        self.next_button = QToolButton(self)
        self.next_button.setText("Next")
        self.next_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.next_button.setIcon(QIcon(":go-next"))
        self.next_button.setToolTip("Find next")
        self.next_button.setAutoRaise(True)
        self.previous_button = QToolButton(self)
        self.previous_button.setToolTip("Find previous")
        self.previous_button.setText("Prev")
        self.previous_button.setIcon(QIcon(":go-previous"))
        self.previous_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.previous_button.setAutoRaise(True)
        self.close_button = QToolButton(self)
        self.close_button.setText("Close")
        self.close_button.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.close_button.setIcon(QIcon(":window-close"))
        self.close_button.setToolTip("Close search bar")
        self.close_button.setAutoRaise(True)
        
        self.options_button = QToolButton(self)
        self.options_button.setAutoRaise(True)
        self.options_button.setIcon(QIcon(":preferences-system.svg"))
        self.options_button.setPopupMode(QToolButton.InstantPopup)
      
        # create popup menu
        menu = QMenu("Search options")
        group = QActionGroup(menu)
        self.whole_action = QAction("Whole words", menu)
        self.whole_action.setCheckable(True)
        self.whole_action.setChecked(False)
        self.case_action = QAction("Match case", menu)
        self.case_action.setCheckable(True)
        self.case_action.setChecked(False)
        menu.addAction(self.whole_action)
        menu.addAction(self.case_action)
        self.options_button.setMenu(menu)

        # create replace elements
        self.replace_edit = QLineEdit(self)
        self.replace_edit.setToolTip("Replace text")
        self.replace_edit.setPlaceholderText("Replace...")
        self.replace_edit.setStyleSheet(
        "QLineEdit{"
        "padding-right: 16px;"
        "padding-left: 5px;"
        "background: url(:edit-replace-small.png);"
        "background-position: right;"
        "background-repeat: no-repeat;"
        "border: 1px solid grey;"
        "border-radius: 6.5px;}")
        self.replace_button = QToolButton(self)
        self.replace_button.setText("Replace")
        self.replace_button.setToolTip("Replace text")
        self.replace_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.replace_button.setIcon(QIcon(":gtk-edit"))
        self.replace_button.setAutoRaise(True)
        self.all_button = QToolButton(self)
        self.all_button.setToolTip("Replace all")
        self.all_button.setText("Replace all")
        self.all_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.all_button.setIcon(QIcon(":accessories-text-editor"))
        self.all_button.setAutoRaise(True)
        
        # add search elements to widget
        gbox = QGridLayout(self)
        hbox = QHBoxLayout()
        gbox.addWidget(self.close_button,0,0)
        gbox.addWidget(self.search_edit,0,1)
        gbox.addWidget(self.previous_button,0,2)
        gbox.addWidget(self.next_button,0,3)
        gbox.addWidget(self.options_button,0,4)

        gbox.addWidget(self.replace_edit,1,1)
        gbox.addWidget(self.replace_button,1,2)
        gbox.addWidget(self.all_button,1,3)
        
        self.setFocusProxy(self.search_edit)
        self.hide()

        # setup connections
        self.next_button.clicked.connect(self.find_next)
        self.previous_button.clicked.connect(self.find_previous)
        self.replace_button.clicked.connect(self.replace_next)
        self.search_edit.returnPressed.connect(self.find_next)
        self.all_button.clicked.connect(self.replace_all)
        self.close_button.clicked.connect(self.hide)
        
    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.parent().setFocus(True)
        elif e.key() == Qt.Key_Tab:
            self.focusNextChild()

    def toggle(self, show_replace=False):
        text = self.parent().textCursor().selectedText()
        if not self.isVisible() or (self.isVisible() and \
            show_replace != self.replace_edit.isVisible()):
            self.show(show_replace)
            self.setFocus(True)
            if not text.isEmpty():
                self.search_edit.setText(text)
        elif not self.hasFocus():
            self.setFocus(True)
            if not text.isEmpty():
                self.search_edit.setText(text)
        else:
            self.parent().setFocus(True)
            self.hide()

    def show(self, show_replace=False):
        self.setVisible(True)
        if show_replace:
            self.replace_edit.setVisible(True)
            self.replace_button.setVisible(True)
            self.all_button.setVisible(True)
        else:
            self.replace_edit.setVisible(False)
            self.replace_button.setVisible(False)
            self.all_button.setVisible(False)

    def hide(self):
        self.setVisible(False)

    def find(self, forward):
        document = self.parent().document()
        editor = self.parent()
        if not document:
            return False
        text = self.search_edit.text()
        found = False
        if text.isEmpty():
            return False
        else:
            flags = QTextDocument.FindFlag()
            if self.whole_action.isChecked():
                flags = (flags|QTextDocument.FindWholeWords)
            if self.case_action.isChecked():
                flags = (flags|QTextDocument.FindCaseSensitively)
            if not forward:
                flags = (flags|QTextDocument.FindBackward)

            cursor = QTextCursor(editor.textCursor())
            tmpcursor = QTextCursor(cursor)
            cursor = document.find(text, cursor, flags)
            if cursor.isNull():
                cursor = tmpcursor
                if forward:
                    cursor.movePosition(QTextCursor.Start, 
                                        QTextCursor.MoveAnchor)
                else:
                    cursor.movePosition(QTextCursor.End, 
                                        QTextCursor.MoveAnchor)
                cursor = document.find(text, cursor, flags)
                if not cursor.isNull():
                    editor.setTextCursor(cursor)
                    return True
                return False
            else:
                editor.setTextCursor(cursor)
                return True
        return False

    def find_next(self):
        return self.find(True)

    def find_previous(self):
        return self.find(False)

    def replace_next(self):
        cursor = QTextCursor(self.parent().textCursor())
        selection = cursor.hasSelection()
        if selection:
            text = QString(cursor.selectedText())
            current = QString(self.search_edit.text())
            replace = QString(self.replace_edit.text())
            if text == current:
                cursor.insertText(replace)
                cursor.select(QTextCursor.WordUnderCursor)
        else:
            return self.find_next()
        self.find_next()
        return True

    def replace_all(self):
        while self.find_next():
            self.replace_next()
        self.replace_next()
        
        
class BookmarksPane(QWidget):

    jumpRequested = pyqtSignal(int)

    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.bookmark_list = QTreeWidget(self)
        self.bookmark_list.setColumnCount(1)
        self.bookmark_list.setHeaderHidden(True)
#        self.bookmark_list.setIndentation(0)
        self.bookmark_list.setExpandsOnDoubleClick(False)
        self.bookmark_list.setToolTip("Click to jump to bookmark")
        hbox = QHBoxLayout(self)
        hbox.addWidget(self.bookmark_list)
        self.setFocusProxy(self.bookmark_list)
        user = QTreeWidgetItem()
        user.setText(0, "Custom")
        auto = QTreeWidgetItem()
        auto.setText(0, "Automatic")
        self.bookmark_list.insertTopLevelItems(0,[user, auto])
        self.bookmark_list.itemDoubleClicked.connect(self.jump)
        
    def update_bookmarks(self, bookmarks):
        autos = bookmarks["auto"]
        users = bookmarks["user"]
        user = self.bookmark_list.topLevelItem(0)
        user.takeChildren()
        for i, text in users.iteritems():
            item = QTreeWidgetItem(user)
            item.setText(0, "%s (%s)" % (text,i+1))
            item.setData(0,Qt.UserRole, i)
        user.setExpanded(True)
        auto = self.bookmark_list.topLevelItem(1)
        auto.takeChildren()
        for i, text in autos.iteritems():
            item = QTreeWidgetItem(auto)
            item.setText(0, "%s (%s)" % (text,i+1))
            item.setData(0,Qt.UserRole, i)
        auto.setExpanded(True)        
            
    def jump(self, item, col):
        if not item.parent() is None:
            self.jumpRequested.emit(item.data(0,Qt.UserRole).toInt()[0])

class PlainTextEditor(QFrame):

    textChanged = pyqtSignal()
    modificationChanged = pyqtSignal(bool)
    copyAvailable = pyqtSignal(bool)
    redoAvailable = pyqtSignal(bool)
    undoAvailable = pyqtSignal(bool)
    cursorPositionChanged = pyqtSignal()
    blockCountChanged = pyqtSignal()
    bookmarksUpdated = pyqtSignal(dict)

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        # default settings
        self.tabwidth = 4
        self.autobracket = True
        self.highlight = True
        self.suggest = True
        self.find_only = False
        self.bookmarks = {"user":{}, "auto":{}}
        self.block_count = 1

        # main widgets
        self.edit = PlainTextEdit(self)
        self.search_bar = SearchBar(self.edit)
        self.side_panel = SidePanel(self.edit)

        # connections
        self.edit.blockCountChanged.connect(self.side_panel.adjust_width)
        self.edit.updateRequest.connect(self.side_panel.update_contents)
        self.edit.textChanged.connect(self.textChanged.emit)
        self.edit.modificationChanged.connect(self.modificationChanged.emit)
        self.edit.undoAvailable.connect(self.undoAvailable.emit)
        self.edit.redoAvailable.connect(self.redoAvailable.emit)
        self.edit.copyAvailable.connect(self.copyAvailable.emit)
        self.edit.cursorPositionChanged.connect(self.cursorPositionChanged)
        self.edit.blockCountChanged.connect(self.blockCountChanged)
        self.edit.blockChanged.connect(self.check_bookmarks)
        self.side_panel.paintEventSignal.connect(self.update_sidepanel)
        self.edit.blockCountChanged.connect(self.block_count_change)

        # create layout
        hbox = QHBoxLayout()
        hbox.addWidget(self.side_panel)
        hbox.addWidget(self.edit)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        vbox = QVBoxLayout(self)
        vbox.addLayout(hbox)
        vbox.addWidget(self.search_bar)
        self.setFocusProxy(self.edit)
    
    def document(self):
        return self.edit.document()
        
    def textCursor(self):
        return self.edit.textCursor()
        
    def setTextCursor(self, cursor):
        self.edit.setTextCursor(cursor)
        
    def insertPlainText(self, text):
        self.edit.insertPlainText(text)
        
    def setPlainText(self, text):
        self.edit.setPlainText(text)
        
    def toPlainText(self):
        return self.edit.toPlainText()

    def toggle_find(self):
        self.search_bar.toggle(False)

    def toggle_replace(self):
        self.search_bar.toggle(True)
        
    def selectAll(self):
        self.edit.selectAll()
        
    def copy(self):
        self.edit.copy()
        
    def paste(self):
        self.edit.paste()
        
    def cut(self):
        self.edit.cut()
        
    def undo(self):
        self.edit.undo()
        
    def redo(self):
        self.edit.redo()
        
    def indent(self):
        self.edit.indent_region()
        
    def unindent(self):
        self.edit.unindent_region()
        
    def comment(self):
        self.edit.comment_region()
        
    def uncomment(self):
        self.edit.uncomment_region()
        
    def goto_line(self):
        self.edit.goto_line()
        
    def block_count_change(self, new_count):
        cursor = self.textCursor()
        line = cursor.blockNumber()
        count = new_count - self.block_count
        self.block_count = new_count
        for item in sorted(self.bookmarks["user"].keys()):
            adjust = False
            if count > 0: # positive
                cursor.movePosition(QTextCursor.Up)
                cursor.select(QTextCursor.LineUnderCursor)
                if line <= item + 1 and cursor.selectedText().trimmed().isEmpty():
                    adjust = True
            elif count < 0:
                if line < item:
                    adjust = True
            if adjust:
                text = self.bookmarks["user"][item]
                self.bookmarks["user"][item+count] = text
                self.bookmarks["user"].pop(item)
        self.bookmarksUpdated.emit(self.bookmarks)
        
    def bookmark(self, line=None, type="user"):
        if line is None:
            line = self.textCursor().blockNumber()
        type = str(type)
        if line in self.bookmarks[type]:
            if type == "user":
                self.bookmarks[type].pop(line)
        else:
            doc = self.document()
            block = doc.findBlockByNumber(line)
            text = block.text()
            self.bookmarks[type][line] = text
        self.check_bookmarks()
            
    def check_bookmarks(self):
        doc = self.document()
        cursor = QTextCursor(doc)
        regexp = QRegExp(r".*<-\s*function\(.*")
        self.bookmarks["auto"] = {}
        cursor = doc.find(regexp, cursor)
        while not cursor.isNull():
            line = cursor.blockNumber()
            cursor.select(QTextCursor.LineUnderCursor)
            text = cursor.selectedText()
            cursor.clearSelection()
            self.bookmarks["auto"][line] = text
            cursor = doc.find(regexp, cursor)
        # check the custom ones as well
        for i, text in self.bookmarks["user"].iteritems():
            block = doc.findBlockByNumber(i)
            self.bookmarks["user"][i] = block.text()
        self.bookmarksUpdated.emit(self.bookmarks)
        
    def update_sidepanel(self, panel, event):
        metrics = self.fontMetrics()
        pos = self.edit.textCursor().position()
        line = self.document().findBlock(pos).blockNumber()+1

        block = self.edit.firstVisibleBlock()
        count = block.blockNumber()
        painter = QPainter(panel)
        palette = self.parent().palette()
        color = palette.color(QPalette.Normal, QPalette.Window)
        painter.fillRect(event.rect(), color)

        # iterate over all visible text blocks in the document
        while block.isValid():
            count += 1
            bound = self.edit.blockBoundingGeometry(block)
            top = bound.translated(self.edit.contentOffset()).top()
            # check position of block is outside visible area.
            if block.isVisible():
                rect = QRect(panel.width()/2.0, top, panel.width(), metrics.height())
                painter.drawText(rect, Qt.AlignRight, "-")
            if top >= event.rect().bottom():
                break
            # draw line number right justified at position of line
            rect = QRect(0, top, panel.width()/2.0, metrics.height())
            painter.drawText(rect, Qt.AlignRight, unicode(count))
            block = block.next()
        painter.end()
        
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
    editor = PlainTextEditor(window)
    highlighter = Highlighter(editor)
    # main settings
    fontfamily = QSettings().value("manageR/fontfamily", "DejaVu Sans Mono").toString()
    fontsize = QSettings().value("manageR/fontsize", 10).toInt()[0]
    tabwidth = QSettings().value("manageR/tabwidth", 4).toInt()[0]
    autobracket = QSettings().value("manageR/bracketautocomplete", True).toBool()
    delay = QSettings().value("manageR/delay", 1000).toInt()[0]
    chars = QSettings().value("manageR/minimumchars", 3).toInt()[0]
    
    editor.setFont(QFont(fontfamily, fontsize))
    editor.tabwidth = tabwidth
    editor.autobracket = autobracket
    editor.highlight = QSettings().value("manageR/enablehighlighting", True).toBool()
    window.setCentralWidget(editor)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
