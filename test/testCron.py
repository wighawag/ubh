import unittest

from webtest import TestApp

from cron.updateReviewTimeUnit import application as updateReviewTimeUnitApplication
#from cron.clearOldReviewTimeUnitWeights import application as clearOldReviewTimeUnitWeightsApplication

from google.appengine.ext import testbed
from helper.googleUser import setCurrentUser, logoutCurrentUser

from score import service
from player.model import createPlayer
from stats.model import setReviewTimeUnit

import config

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

        self.updateReviewTimeUnitApp = TestApp(updateReviewTimeUnitApplication())
#        self.clearOldReviewTimeUnitWeightsApp = TestApp(clearOldReviewTimeUnitWeightsApplication())

    def tearDown(self):
        logoutCurrentUser()
        self.testbed.deactivate()


    def test_whetherTimeUnitIsInitializedWithHighNumber(self):
        setCurrentUser('test@mail.com', 'test', True)
        response = self.updateReviewTimeUnitApp.get('/cron/updateReviewTimeUnit')
        value = str(30 * 24 * 3600 * 1000)
        self.assertEqual(response.body, value)

    def test_whetherTimeUnitIsUpdatedProperly(self):
        setReviewTimeUnit(0)
        for i in range(0,10):
            playerId = 'test' + str(i)
            createPlayer(playerId, playerId)
            service.start(playerId)
            service.setScore(playerId, {'score' : 3, 'proof' : "sdsd", 'time' : 0})

        for i in range(10,20):
            playerId = 'test' + str(i)
            createPlayer(playerId, playerId)
            service.getRandomScore(playerId)
            service.reviewScore(playerId, {'score' : 3, 'time' : 0})

        config.nbPlayerPerTimeUnit = 10
        setCurrentUser('test@mail.com', 'test', True)
        response = self.updateReviewTimeUnitApp.get('/cron/updateReviewTimeUnit')
        responseValue = int(response.body)
        self.assertTrue(responseValue > 0 and responseValue < 10000)




if __name__ == "__main__":
    unittest.main()
