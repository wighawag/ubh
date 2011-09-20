
import unittest
from google.appengine.ext import testbed

from player.model import createPlayer
from player.session import createPlayerSession, getPlayerSession, deletePlayerSession, DEFAULT_MAX_SESSION_LIFE_TIME

from pyamf.remoting.gateway import UnknownServiceMethodError

import datetime

from secureService import sessionTokenCall, InvalidSessionError, SessionExpiredError, NoActiveSessionError

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def testCorrectSessionCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId)
        answer = sessionTokenCall(session.token, playerId, 'score.service.echo', 'hello')
        self.assertEqual(answer, "player test : hello")

    def testExpiredSessionCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, datetime=datetime.datetime.now() - DEFAULT_MAX_SESSION_LIFE_TIME)

        self.failUnlessRaises(SessionExpiredError, sessionTokenCall, session.token, playerId, 'score.service.echo', 'hello')


    def testNonExistingMethodCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId)
        self.failUnlessRaises(UnknownServiceMethodError, sessionTokenCall, session.token, playerId, 'nonExisitingMehtod')

    def testWrongSessionForPlayer(self):
        playerId = "test"
        createPlayer(playerId, "test")
        createPlayerSession(playerId)
        self.failUnlessRaises(InvalidSessionError, sessionTokenCall, "wrong token", playerId, 'score.service.echo', 'hello')


if __name__ == "__main__":
    unittest.main()
