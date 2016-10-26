__author__ = 'AlecZ'

def log(s, end="\n"):
    print(s, end=end)

def verbose(s, end="\n"):
    log("[VERBOSE] " + s, end=end)

def info(s, end="\n"):
    log("[INFO] " + s, end=end)