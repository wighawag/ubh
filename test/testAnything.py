'''
Created on 1 Apr 2012

@author: Rsandford
'''
import unittest
import simplejson as json

class Test(unittest.TestCase):


    def testName(self):
        data = json.loads('{"id": 4, "method":"sds"}')
        self.assertEquals(data.id, 4)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()