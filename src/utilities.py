
"""
Utility methods

author: Chris Scott
last edited: February 2012
"""

import os
import sys
import random
import string


################################################################################
def iconPath(icon):
    """
    Return full path to given icon.
    
    """
    return os.path.join(":/icons", icon)


################################################################################
def idGenerator(size=16, chars=string.digits + string.ascii_letters + string.digits):
    """
    Generate random string of size "size" (defaults to 16)
    
    """
    return ''.join(random.choice(chars) for x in range(size))


################################################################################
def createTmpDirectory():
    """
    Create temporary directory
    
    """
    name = "CDJSVis-" + idGenerator(size=8)
    try:
        tmpDir = os.path.join("/tmp", name)
        while os.path.exists(tmpDir):
            name = "CDJSVis-" + idGenerator(size=8)
            tmpDir = os.path.join("/tmp", name)
        os.mkdir(tmpDir)
    except:
        tmpDir = os.path.join(os.getcwd(), name)
        while os.path.exists(tmpDir):
            name = "CDJSVis-" + idGenerator(size=8)
            tmpDir = os.path.join(os.getcwd(), name)
    
    return tmpDir
