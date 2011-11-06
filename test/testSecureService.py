
import unittest
from google.appengine.ext import testbed

from player.model import createPlayer
from player.session import createPlayerSession, DEFAULT_MAX_SESSION_LIFE_TIME

from django.utils import simplejson as json

import datetime

from service.secure import sessionTokenCall, signedRequestCall

from crypto.signature import create_HMACSHA256_Signature
from encodings.base64_codec import base64_encode
from error import SESSION_EXPIRED_ERROR, UNKNOW_SERVICE_CALL_ERROR,\
    INVALID_SESSION_TOKEN_ERROR, INVALID_SIGNATURE_ERROR, SIGNED_REQUEST_METHOD_ERROR

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

        response = sessionTokenCall(session.token, playerId, 'score.service.echo', 'hello')
        self.assertTrue('success' in response and response['success'] == False and 'error' in response and response['error'] == SESSION_EXPIRED_ERROR['code'])


    def testNonExistingMethodTokenCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, 'token')
        response = sessionTokenCall(session.token, playerId, 'nonExisitingMehtod')
        self.assertTrue('success' in response and response['success'] == False and 'error' in response and response['error'] == UNKNOW_SERVICE_CALL_ERROR['code'])

    def testWrongSessionTokenForPlayer(self):
        playerId = "test"
        createPlayer(playerId, "test")
        createPlayerSession(playerId, 'token')
        response = sessionTokenCall("wrong token", playerId, 'score.service.echo', 'hello')
        self.assertTrue('success' in response and response['success'] == False and 'error' in response and response['error'] == INVALID_SESSION_TOKEN_ERROR['code'])





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
        response = signedRequestCall(signedRequest)
        self.assertTrue('success' in response and response['success'] == False and 'error' in response and response['error'] == SESSION_EXPIRED_ERROR['code'])


    def testNonExistingMethodSignedRequestCall(self):
        playerId = "test"
        createPlayer(playerId, "test")
        session = createPlayerSession(playerId, 'signedRequest')
        signedRequest = createSignedRequest(playerId, session.secret, 'nonExisitingMehtod')
        response = signedRequestCall(signedRequest)
        self.assertTrue('success' in response and response['success'] == False and 'error' in response and response['error'] == UNKNOW_SERVICE_CALL_ERROR['code'])

    def testWrongSessionSignedRequestForPlayer(self):
        playerId = "test"
        createPlayer(playerId, "test")
        createPlayerSession(playerId, 'signedRequest')
        signedRequest = createSignedRequest(playerId, "wrong secret", 'score.service.echo', 'hello')
        response = signedRequestCall(signedRequest)
        self.assertTrue('success' in response and response['success'] == False and 'error' in response and response['error'] == INVALID_SIGNATURE_ERROR['code'])

    def testWrongSessionMethod(self):
        playerId = "test"
        createPlayer(playerId, "test")
        createPlayerSession(playerId, 'token')
        signedRequest = createSignedRequest(playerId, "wrong secret", 'score.service.echo', 'hello')
        response = signedRequestCall(signedRequest)
        self.assertTrue('success' in response and response['success'] == False and 'error' in response and response['error'] == SIGNED_REQUEST_METHOD_ERROR['code'])

if __name__ == "__main__":
    unittest.main()
