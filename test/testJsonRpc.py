
import unittest
from google.appengine.ext import testbed

from player.model import createPlayer
from player.session import createPlayerSession, DEFAULT_MAX_SESSION_LIFE_TIME
from helper.signedRequest import createSignedRequest

from json import application as jsonApp
from authentification.google.googleUserEntryPoint import application as googleApp
from webtest import TestApp
from helper.googleUser import setCurrentUser
from helper.html import getFlashVarsFromResponse

import simplejson as json

class Test(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.jsonApp = TestApp(jsonApp())
        self.googleApp = TestApp(googleApp())

    def tearDown(self):
        self.testbed.deactivate()

    def executeGoogleUserSecureService(self, userEmail, userId, service, *args):
        # authenticate user first
        setCurrentUser(userEmail, userId)
        response = self.googleApp.get('/googleUser?method=signedRequest')
        flashvars = getFlashVarsFromResponse(response)

        #execute a secured service
        response = self.executeJsonSignedRequestCall(flashvars['playerId'], flashvars['secret'],  service, *args)

        return response

    def executeJsonSignedRequestCall(self, playerId, secret, service, *args):
        signedRequest = createSignedRequest(playerId,  secret, service, *args)

        sendData = {'method' : 'signedRequestCall', 'params' : [signedRequest], 'id' : 1}

        postBody = json.dumps(sendData)
        return self.jsonApp.post("/json", postBody)



    def test_googleUserAuthenticatedEcho(self):
        userId = 'test'
        message = 'hello'
        answer = self.executeGoogleUserSecureService("test@mail.com", userId, "score.service.echo", message)
        answerDict = json.loads(answer.body)
        self.assertEqual(answerDict['result'], "googleUser_" + userId + ":" + message)

if __name__ == "__main__":
    unittest.main()
