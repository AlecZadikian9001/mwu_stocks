__author__ = 'AlecZ'

def log(s, tag, end="\n"):
    if end == "\n":
        tag = "[{}] ".format(tag)
    else:
        tag = ""
    print(tag + s, end=end)

def error(s, end="\n"):
    log(s, "ERROR", end=end)
    raise Exception(s)

def verbose(s, end="\n"):
    log(s, "VERBOSE", end=end)

def info(s, end="\n"):
    log(s, "INFO", end=end)