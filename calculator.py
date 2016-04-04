from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4.QtCore as QtCore
from ui_calculator import Ui_CalculatorDialog
import rpy2.robjects as robjects

class CalculatorDialog(QDialog, Ui_CalculatorDialog):
    def __init__(self, mobject, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self._mobject = mobject
        self._columns = mobject.colnames
        self.populateFields()
        self.setFocusProxy(self.mExpressionTextEdit)

        # disable ok button until there is text for output column and expression
        self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        # if something:
        #     self.mOnlyUpdateSelectedCheckBox.setChecked(True)
        # we'll ignore this for now and just always leave this unchecked

    def accept(self):
        calcString = self.mExpressionTextEdit.toPlainText()
        try:
            robjects.r.parse(text=unicode(calcString), n=1, encoding="UTF-8")
        except RRuntimeError, err:
            QMessageBox.critical(self, "Syntax error", 
            "Invalid expression syntax. The error message from R is:\n%s" % unicode(err))
            return
        QDialog.accept(self)

    def populateFields(self):
        #insert into field list and field combo box
        self.mFieldsListWidget.addItems(self._columns)
        self.mExistingFieldComboBox.addItems(self._columns)

    def on_mUpdateExistingFieldCheckBox_stateChanged(self, state):
        if state == Qt.Checked:
            self.mNewFieldGroupBox.setEnabled(False)
        else:
            self.mNewFieldGroupBox.setEnabled(True)
        self.setOkButtonState()

    def on_mFieldsListWidget_itemDoubleClicked(self, item):
        if not item:
            return
        self.mExpressionTextEdit.insertPlainText(item.text())

    def on_mValueListWidget_itemDoubleClicked(self, item):
        if not item:
            return
        self.mExpressionTextEdit.insertPlainText(" "+item.text()+ " ")

    @QtCore.pyqtSlot()
    def on_mPlusPushButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText(" + ")

    @QtCore.pyqtSlot()
    def on_mMinusPushButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText(" - ")

    @QtCore.pyqtSlot()
    def on_mMultiplyPushButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText(" * ")

    @QtCore.pyqtSlot()
    def on_mDividePushButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText(" / ")

    @QtCore.pyqtSlot()
    def on_mSqrtButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("sqrt(")

    @QtCore.pyqtSlot()
    def on_mExpButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("^")

    @QtCore.pyqtSlot()
    def on_mFactorialButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("factorial(")

    @QtCore.pyqtSlot()
    def on_mEulerButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("exp(")

    @QtCore.pyqtSlot()
    def on_mNaturalLogButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("log(")

    @QtCore.pyqtSlot()
    def on_mLogButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("log10(")

    @QtCore.pyqtSlot()
    def on_mRoundButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("round(" )

    @QtCore.pyqtSlot()
    def on_mCeilingButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("ceiling(")

    @QtCore.pyqtSlot()
    def on_mOpenBracketPushButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("(")

    @QtCore.pyqtSlot()
    def on_mCloseBracketPushButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText(")")

    @QtCore.pyqtSlot()
    def on_mFloorButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("floor(")
        
    @QtCore.pyqtSlot()
    def on_mIfelseButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("ifelse(test, yes, no)")
        
    @QtCore.pyqtSlot()
    def on_mNumericButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("as.numeric(")
        
    @QtCore.pyqtSlot()
    def on_mCharacterButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("as.character(")
        
    @QtCore.pyqtSlot()
    def on_mFactorButton_clicked(self):
        self.mExpressionTextEdit.insertPlainText("factor(")
        
    @QtCore.pyqtSlot()
    def on_mNormalButton_clicked(self):
        n = self._mobject.nrow
        self.mExpressionTextEdit.insertPlainText("rnorm(%s, mean=0, sd=1" % n)
        
    @QtCore.pyqtSlot()
    def on_mPoissonButton_clicked(self):
        n = self._mobject.nrow
        self.mExpressionTextEdit.insertPlainText("rpois(%s, lambda= " % n)
        
    @QtCore.pyqtSlot()
    def on_mUniformButton_clicked(self):
        n = self._mobject.nrow
        self.mExpressionTextEdit.insertPlainText("runif(%s, min=0, max=1" % n)
        
    @QtCore.pyqtSlot()
    def on_mClearButton_clicked(self):
        self.mExpressionTextEdit.clear()

    @QtCore.pyqtSlot()
    def on_mDeleteButton_clicked(self):
        cursor = self.mExpressionTextEdit.textCursor()
        cursor.deletePreviousChar()
        self.mExpressionTextEdit.setTextCursor(cursor)

    @QtCore.pyqtSlot()
    def on_mAllPushButton_clicked(self):
        self.getFieldValues(0)

    def on_mOutputFieldNameLineEdit_textChanged(self, text):
        self.setOkButtonState()

    def on_mExpressionTextEdit_textChanged(self):
        self.setOkButtonState()
        self.mExpressionTextEdit.setFocus(True)

    def getFieldValues(self, limit=0):
        self.mValueListWidget.clear()
        currentItem = self.mFieldsListWidget.currentItem()
        if not currentItem:
            return
        currentItem = unicode(currentItem.text())
        items = []
        if limit > 0:
            items = list(robjects.r.sample(self._mobject.rx2(unicode(currentItem)), size=limit))
        else:
            items = list(self._mobject.rx2(unicode(currentItem)))
        self.mValueListWidget.addItems([unicode(i) for i in items])

    def setOkButtonState(self):
        okEnabled = True
        if (self.mOutputFieldNameLineEdit.text().isEmpty() and \
            self.mUpdateExistingFieldCheckBox.checkState() == Qt.Unchecked) or \
            self.mExpressionTextEdit.toPlainText().isEmpty():
            okEnabled = False
        self.mButtonBox.button(QDialogButtonBox.Ok).setEnabled(okEnabled)

    def on_mFieldsListWidget_currentItemChanged(self, current, previous):
        self.getFieldValues(25)
