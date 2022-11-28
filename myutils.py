import sys
import inspect

def getLineLastException():
    return str( sys.exc_info()[-1].tb_lineno )

def myfunc_name():
    return inspect.stack()[1][3]