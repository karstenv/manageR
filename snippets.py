    def highlightBlock(self, text):
        NORMAL, MULTILINESINGLE, MULTILINEDOUBLE, ERROR = range(4)
        INBRACKETS, INBRACKETSSINGLE, INBRACKETSDOUBLE = range(4,7)

        textLength = text.length()
        prevState = self.previousBlockState()

        cursor = self.parent().textCursor()
        block = cursor.block()

        self.setFormat(0, textLength, Highlighter.Formats["normal"])

        for regex, format in Highlighter.Rules:
            i = regex.indexIn(text)
            while i >= 0:
                length = regex.matchedLength()
                self.setFormat(i, length, Highlighter.Formats[format])
                i = regex.indexIn(text, i + length)
        self.setCurrentBlockState(NORMAL)

        startIndex = 0
        startCount = 0
        endCount = 0
        endIndex = 0
        if not self.previousBlockState() >= 4:
            startIndex = self.bracketStartExpression.indexIn(text)
        while startIndex >= 0:
            startCount += 1
            endIndex = self.bracketBothExpression.indexIn(text, startIndex+1)
            bracket = self.bracketBothExpression.cap()
            if endIndex == -1 or bracket == "(":
                self.setCurrentBlockState(self.currentBlockState() + 4)
                length = text.length() - startIndex
            elif bracket == ")":
                endCount += 1
                tmpEndIndex = endIndex
                while tmpEndIndex >= 0:
                    tmpLength = self.bracketBothExpression.matchedLength()
                    tmpEndIndex = self.bracketBothExpression.indexIn(text, tmpEndIndex + tmpLength)
                    bracket = self.bracketBothExpression.cap()
                    if tmpEndIndex >= 0:
                        if bracket == ")":
                            endIndex = tmpEndIndex
                            endCount += 1
                        else:
                            startCount += 1
                if startCount > endCount:
                    self.setCurrentBlockState(self.currentBlockState() + 4)
                length = endIndex - startIndex + self.bracketBothExpression.matchedLength() + 1

            bracketText = text.mid(startIndex, length+1)
            regex = QRegExp(r"[a-zA-Z_\.][0-9a-zA-Z_\.]*[\s]*=(?=([^=]|$))")
            format = "inbrackets"
            i = regex.indexIn(bracketText)
            while i >= 0:
                bracketLength = regex.matchedLength()
                self.setFormat(startIndex + i, bracketLength, Highlighter.Formats[format])
                length = length + bracketLength
                i = regex.indexIn(bracketText, i + bracketLength)
            startIndex = self.bracketStartExpression.indexIn(text, startIndex + length)

        if text.indexOf(self.stringRe) != -1:
            return
        for i, state in ((text.indexOf(self.multilineSingleStringRe),
                          MULTILINESINGLE),
                        (text.indexOf(self.multilineDoubleStringRe),
                          MULTILINEDOUBLE)):
            if (self.previousBlockState() == state or \
            self.previousBlockState() == state + 4) and \
            not text.contains("#"):
                if i == -1:
                    i = text.length()
                    self.setCurrentBlockState(state)
                self.setFormat(0, i + 1, Highlighter.Formats["string"])
            elif i > -1 and not text.contains("#"):
                self.setCurrentBlockState(state)
                self.setFormat(i, text.length(), Highlighter.Formats["string"])
