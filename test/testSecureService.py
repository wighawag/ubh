
import unittest
from google.appengine.ext import testbed

from player.model import createPlayer
from player.session import createPlayerSession, getPlayerSession, deletePlayerSession, DEFAULT_MAX_SESSION_LIFE_TIME

from pyamf.remoting.gateway import UnknownServiceMethodError

from django.utils import simplejson as json

import datetime

from service.secure import sessionTokenCall, InvalidSessionError, SessionExpiredError, signedRequestCall

from crypto.signature import create_HMACSHA256_Signature
from encodings.base64_codec import base64_encode

def createSignedRequest(playerId, secret, methodName, *args):
    jsonData = json.dumps({u'playerId' : playerId, 'methodName' : methodName, 'args' : args} )
    payload, length_consumed = base64_encode(jsonData)

    signature = create_HMACSHA256_Signature(payload, secret)
    encoded_signature, length_consumed = base64_encode(signature)

    return encoded_signature + '.' + payload

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def testCorrectSessionTokenCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, 'token')
        answer = sessionTokenCall(session.token, playerId, 'score.service.echo', 'hello')
        self.assertEqual(answer, "player test : hello")

    def testExpiredSessionTokenCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, 'token', datetime=datetime.datetime.now() - DEFAULT_MAX_SESSION_LIFE_TIME)

        self.failUnlessRaises(SessionExpiredError, sessionTokenCall, session.token, playerId, 'score.service.echo', 'hello')


    def testNonExistingMethodTokenCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, 'token')
        self.failUnlessRaises(UnknownServiceMethodError, sessionTokenCall, session.token, playerId, 'nonExisitingMehtod')

    def testWrongSessionTokenForPlayer(self):
        playerId = "test"
        createPlayer(playerId, "test")
        createPlayerSession(playerId, 'token')
        self.failUnlessRaises(InvalidSessionError, sessionTokenCall, "wrong token", playerId, 'score.service.echo', 'hello')





    def testCorrectSessionSignedRequestCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, 'signedRequest')

        signedRequest = createSignedRequest(playerId, session.secret, 'score.service.echo', 'hello')
        answer = signedRequestCall(signedRequest)

        self.assertEqual(answer, "player test : hello")

    def testExpiredSessionSignedRequestCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, 'signedRequest', datetime=datetime.datetime.now() - DEFAULT_MAX_SESSION_LIFE_TIME)

        signedRequest = createSignedRequest(playerId, session.secret, 'score.service.echo', 'hello')
        self.failUnlessRaises(SessionExpiredError, signedRequestCall, signedRequest)


    def testNonExistingMethodSignedRequestCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, 'signedRequest')
        signedRequest = createSignedRequest(playerId, session.secret, 'nonExisitingMehtod')
        self.failUnlessRaises(UnknownServiceMethodError, signedRequestCall, signedRequest)

    def testWrongSessionSignedRequestForPlayer(self):
        playerId = "test"
        createPlayer(playerId, "test")
        createPlayerSession(playerId, 'signedRequest')
        signedRequest = createSignedRequest(playerId, "wrong secret", 'score.service.echo', 'hello')
        self.failUnlessRaises(InvalidSessionError, signedRequestCall, signedRequest)


if __name__ == "__main__":
    unittest.main()
