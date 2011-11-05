import unittest
from google.appengine.ext import testbed
from player.session import createPlayerSession, getPlayerSession, deletePlayerSession, DEFAULT_MAX_SESSION_LIFE_TIME

import datetime

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def testGivenAPlayerIdCreateASessionThenRetrievIt(self):
        playerId = "randomId"
        session = createPlayerSession(playerId, 'signedRequest')
        getPlayerSession(playerId)
        self.assertEquals(session.key(), getPlayerSession(playerId).key())

    def testCreateASessionAndDeleteItWhenRetriveitReturnNone(self):
        playerId = "randomId3"
        createPlayerSession(playerId, 'signedRequest')
        deletePlayerSession(playerId)
        self.assertEquals(getPlayerSession(playerId), None)

    def testCreateSessionAndTestIfItExpireAfterMoreThan30Minutes(self):
        playerId = "randomId"
        createPlayerSession(playerId, 'signedRequest', datetime=datetime.datetime.now() - DEFAULT_MAX_SESSION_LIFE_TIME)

        session = getPlayerSession(playerId)

        self.assertTrue(session.isExpired())

if __name__ == "__main__":
    unittest.main()
