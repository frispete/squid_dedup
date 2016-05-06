# this is required to make this package work with setuptools entry_points
import os
import sys

path = os.path.dirname(__file__)
if path not in sys.path:
    sys.path.insert(0, path)
#print(path)
del path
