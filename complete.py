# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
import rpy2.robjects as robjects


class RCompleter:

    def __init__(self, linebuffer="", end=-1):
        self.linebuffer = linebuffer
        self.end = end
        self.start = 0
        self.can_suggest = False
        self.guess_token()

    def guess_token(self):
        # first check if we're in a string, then check if we have special chars
        # if neither, we can probably just start from the start
        if self.linebuffer == "":
            self.can_suggest = False
        self.start = 0
        if self.end < 0:
            self.end  = len(self.linebuffer)
        self.linebuffer = QString(self.linebuffer[0:self.end])
        if self.inside_quotes():
            # set 'start' to the location of the last quote
            regex = QRegExp(r"['\"]")
        else:
            regex = QRegExp(r"[^\.\w:?$@[\]]+")
        self.start = self.linebuffer.lastIndexOf(regex)+1
        if self.start < 1:
            self.start = 0
        self.can_suggest = True
        self.token = self.linebuffer[self.start:self.end]

    def inside_quotes(self):
        # simply count the number of quotes before the current cursor (end)
        double = self.linebuffer.count("'")
        single = self.linebuffer.count('"')
        return ((double % 2) or (single % 2))


    def file_completions(self, token = ""):
        # uses R's Sys.glob to filter files and path.expand to expand paths
        token = unicode(token)
        expanded = robjects.r['path.expand'](token)[0]
        comps = list(robjects.r['Sys.glob']("%s*" % expanded, dirmark=True))
        if not expanded == token:
            exp = robjects.r['path.expand']("~")[0]
            comps = [comp.replace(exp, "~") for comp in comps]
        return comps

    def make_regexp_safe(self, token=""):
        return QRegExp.escape(token)

    def keyword_completions(self, token=""):
        regexp = QRegExp(r"^%s" % self.make_regexp_safe(token))
        strings = QStringList([
            "NULL", "NA", "TRUE", "FALSE", "Inf", "NaN",
            "NA_integer_", "NA_real_", "NA_character_", "NA_complex_",
            "repeat ", "in ", "next ", "break ", "else "])
        return list(strings.filter(regexp))

    def attached_package_completions(self, token = ""):
        strings = QStringList(list(robjects.r.search()))
        strings = strings.filter(QRegExp(r"^package:(%s)" % self.make_regexp_safe(token)))
        suffix = robjects.r["$"](robjects.r['rc.options'](),"package.suffix")[0]
        return ["%s%s" % (i[8:],suffix) for i in strings]

    def normal_completions(self, token="", suffix=None):
        if token == "":
            return list()
        else:
            kwargs = {"ignore.case": False}
            comps = QStringList(list(robjects.r.apropos("^%s" % self.make_regexp_safe(token), **kwargs)))
            function = [robjects.r.exists(unicode(i), mode="function")[0] for i in comps]
            if suffix is None:
                suffix = robjects.r["$"](robjects.r['rc.options'](),"function.suffix")[0]
            for i, item in enumerate(comps):
                if function[i]:
                    comps[i] = "%s%s" % (item,suffix)
            #comps = ["%s%s" % (item,suffix) for i, item in enumerate(comps) if function[i] else item]
            keys = QStringList(self.keyword_completions(token))
            packs = QStringList(self.attached_package_completions(token))
            comps << keys << packs
            return comps

    def help_completions(self, prefix="", suffix=""):
        # this one might be slow?
        nc = self.match_available_topics(suffix)
        if len(nc) < 1:
            return list()
        return ["%s?%s" % (prefix, i) for i in nc]

    def match_available_topics(self, token=""):
        def read_aliases(path):
            f = robjects.r['file.path'](unicode(path), "help", "aliases.rds")[0]
            info = QFileInfo(f)
            if info.exists():
                return list(robjects.r['.readRDS'](f).names)
            else:
                f = robjects.r['file.path'](unicode(path), "help", "AnIndex")[0]
                info = QFileInfo(f)
                if info.exists():
                    # aliases.rds was introduced before 2.10.0, as can phase this out
                    return list(list(robjects.r.scan(f, what = list("", ""),
                    sep = "\t", quote = "", na_strings = "", quiet = True))[0])
                else:
                    return list()
        if token == "":
            return list()
        pkgpaths = QStringList(list(robjects.r.searchpaths()))
        pkgs = [QString(i).startsWith('package:') for i in list(robjects.r.search())]
        aliases = []
        for i, item in enumerate(pkgpaths):
            if pkgs[i]:
                aliases.extend(read_aliases(item))
        aliases = QStringList(aliases)
        aliases.removeDuplicates()
        return list(aliases.filter(QRegExp(r"^%s" % self.make_regexp_safe(token))))

    def special_operations_location(self, token):
        regexp = QRegExp(r"([\$@\?\[])")
        token = QString(token)
        tmp = regexp.lastIndexIn(token)
        tmp2 = tmp
        tmpcap = regexp.cap()
        regexp = QRegExp(r":::")
        tmp2 = regexp.lastIndexIn(token)
        if tmp2 > tmp:
            return (tmp2, regexp.cap())
        regexp = QRegExp(r"::")
        tmp2 = regexp.lastIndexIn(token)
        if tmp2 > tmp:
            return (tmp2, regexp.cap())
        return (tmp, tmpcap)

    def argument_names(self, fname):
        args = QString(str(robjects.r('do.call(argsAnywhere, list("%s"))' % fname)))
        args = args.remove("NULL").replace(QRegExp(r'^function'), "")
        args = args.remove("\n").replace(QRegExp(r"[\(\)]"), "").split(",")
        return [arg.trimmed() for arg in args]

    def special_function_arguments(self, fun="", text=""):
        if fun in ("library", "require"):
            regexp = QRegExp(r"^%s" % self.make_regexp_safe(text))
            packages = QStringList(list(robjects.r['installed.packages']().rownames))
            return list(packages.filter(regexp))
        elif fun == "data":
            data = robjects.r.data().rx2("results")
            data = [data.rx(i,4)[0] for i in range(1,data.nrow)]
            return list(QStringList(data).filter(QRegExp(r"^%s" % self.make_regexp_safe(text))))
        else:
            return list()

    def inside_function(self, line = "", cursor = 1, first = False):
        line = QString(line[0:cursor])
        openBracket = line.count("(")
        closeBracket = line.count(")")
        wp = openBracket-closeBracket
        if wp > 0:
            index = line.lastIndexOf("(")
            prefix = line[0:index]
            suffix = line[index+1:]
            if suffix.count(QRegExp(r"[=,]")) < 1:
                first = True
            tmp = suffix.lastIndexOf("=")
            if tmp > 0 and suffix[tmp:].count(",") < 1:
                return (None, first)
            else: ## guess function name
                regexp = QRegExp(r"[^\.\w]")
                possible = list(prefix.split(regexp, QString.SkipEmptyParts))
                if len(possible) > 0:
                    return (possible[-1], first)
                else:
                    return (None, first)
        else: # not inside function
            return (None, first)

    def function_arguments(self, fun="", text=""):
        add = robjects.r["$"](robjects.r['rc.options'](),"funarg.suffix")[0]
        if fun == "" or text == "":
            return list()
        methods = []
        fun = unicode(fun)
        specialFunArgs = self.special_function_arguments(fun, text)
        if robjects.r.exists(fun, mode = "function")[0]:
            methods = list(robjects.r.methods(fun))
            methods.insert(0,fun)
        allArgs = QStringList()
        for func in methods:
            allArgs << self.argument_names(func)
        allArgs.removeDuplicates()
        allArgs = allArgs.filter(QRegExp(r"^%s" % make_regexp_safe(text)))
        if len(allArgs) > 0 and not add == "":
            allArlgs = allArgs.replaceInStrings(QRegExp(r"*"), "\\1%s" % add)
            allArgs << specialFunArgs
            return allArgs
        return QStringList()

    def special_completions(self, text=""):
        # spl (locations of matches) is guaranteed to be non-empty
        specialOp = self.special_operations_location(text)
        opStart = specialOp[0]
        op = specialOp[1]
        opEnd = opStart+len(op)
        if opStart < 0:
            return list()
        prefix = text[0:opStart]
        suffix = text[opEnd:]
        if op == "?":
            return self.help_completions(prefix, suffix)
        def try_evaluate(s):
            return robjects.r("try(eval(parse(text = '%s')), silent = TRUE)" % s)
        if op == "$":
            object = try_evaluate(prefix)
            if robjects.r.inherits(object, "try-error")[0]: ## nothing else to do
                comps = [suffix]
            else:
                comps = list(robjects.r['.DollarNames'](object,
                pattern = "^%s" % self.make_regexp_safe(suffix)))
        elif op == "@":
            object = try_evaluate(prefix)
            if robjects.r.inherits(object, "try-error")[0]: ## nothing else to do
                comps = [suffix]
            else:
                slots = QStringList(robjects.r('methods::slotNames')(try_evaluate('meuse')))
                comps = list(slots.filter(QRegExp(r"^%s" % self.make_regexp_safe(suffix))))
        elif op == "::":
            nse = robjects.r['try'](robjects.r.getNamespaceExports(prefix), silent = True)
            if robjects.r.inherits(nse, "try-error")[0]: ## nothing else to do
                comps = [suffix]
            else:
                comps = list(QStringList(list(nse)).filter(QRegExp(r"^%s" % self.make_regexp_safe(suffix))))
        elif op == ":::":
            ns = robjects.r['try'](robjects.r.getNamespace(prefix), silent = True)
            if robjects.r.inherits(ns, "try-error")[0]: ## nothing else to do
                comps = [suffix]
            else:
                comps = robjects.r.ls(ns, all_names = True, pattern = "^%s" % self.make_regexp_safe(suffix))
        #elif op in ("[", "[["):
            #comps = normal_completions(suffix)
            #if len(comps) < 1:
              #comps = [suffix]
        else:
            comps = [suffix]
        if len(comps) < 1:
            comps = [""]
        return ["%s%s%s" % (prefix, op, comp) for comp in comps]

    def complete_token(self):
        if self.inside_quotes():
            st = self.start
            probablyNotFilename = (st > 2L and \
                                   self.linebuffer[st-1] in ("[", ":", "$"))
            if probablyNotFilename:
                return list()
            else:
                comps = self.file_completions(self.token)
                return comps
        else:
            comps = QStringList()
            first = False
            guessedFunction = self.inside_function()
            fguess = guessedFunction[0]
            first = guessedFunction[1]
            if not fguess is None:
                comps << QStringList(self.function_arguments(fguess, token))
            if first and not fguess == "" and \
               fguess in ("library", "require", "data"):
                return comps
            lastArithOp = QString(self.token).lastIndexOf(QRegExp(r"[\"'^/*+-]"))
            haveArithOp = lastArithOp > 0
            if haveArithOp:
                prefix = token[0:lastArithOp]
                text = token[lastArithOp+1:]
            comps << QStringList(self.special_completions(self.token))
            normal = QStringList(self.normal_completions(self.token))
            if haveArithOp and len(normal) > 0:
                comps << QStringList(["%s%s" % (prefix, comp) for comp in normal])
            else:
                comps << normal
            return list(comps)

def main():
    #robjects.r("test <- data.frame('one'=c(1,2,3,4,5), 'twobaloo'=c(1,2,3,4,5))")
    linebuffer = 'save(x, file="/home/cf")'
    completer = RCompleter(linebuffer, 22)
    if completer.can_suggest:
        comps = completer.complete_token()
    print comps

if __name__ == '__main__':
    main()
