from PyQt4.QtCore import QString, QRegExp
import rpy2.robjects as robjects

def function_arguments(fun):
    try:
        args = robjects.r('do.call(argsAnywhere, list("%s"))' % fun)
        args = QString(str(args))
        if args.contains("function"):
            regexp = QRegExp(r"function\s\(")
            start = regexp.lastIndexIn(args)
            regexp = QRegExp(r"\)")
            end = regexp.lastIndexIn(args)
            args = args[start:end+1].replace("function ", "") # removed fun
        else:
            args = args.replace("\n\n", "").remove("NULL")
    except Exception: # if something goes wrong, ignore it!
        args = QString()
    return args
    
    
def cleanup(saveact, status, runlast):
    # cancel all attempts to quit R from the console
    print("Error: Exit from manageR not allowed, please use File > Quit")
    return None
    

