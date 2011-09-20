import os
import sys

HERE = os.path.dirname(__file__)
sys.path[0:0] = [HERE, os.path.join(HERE, 'pyamf.zip'), ]
