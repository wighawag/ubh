import unittest

from app import gateway
from webtest import TestApp

from authentification.google.googleUserEntryPoint import application as googleUserApp
from google.appengine.ext import testbed
from helper.googleUser import setCurrentUser, logoutCurrentUser

from helper.amf import executeService, getMessageFromResponse, isResponseBad
from helper.html import getFlashVarsFromResponse

#from pyamf.amf3 import ByteArray

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

        self.app = TestApp(googleUserApp())

    def tearDown(self):
        logoutCurrentUser()
        self.testbed.deactivate()

    def executeGoogleUserSecureService(self, userEmail, userId, service, *args):
        # authenticate user first
        setCurrentUser(userEmail, userId)
        response = self.app.get('/googleUser')
        flashvars = getFlashVarsFromResponse(response)

        #execute a secured service
        response = self.executeSessionTokenService(flashvars, service, *args)
        return getMessageFromResponse(response)

    def executeSessionTokenService(self, flashvars, service, *args):
        return executeService(gateway(True), "secureService.sessionTokenCall", flashvars['sessionToken'], flashvars['playerId'], service, *args)




    def test_googleUserAuthenticatedEcho(self):
        answer = self.executeGoogleUserSecureService("test@mail.com", "test", "score.service.echo", "hello")
        self.assertEqual(answer, "player googleUser_test : hello")

    def test_unauthenticatedEchoReturnBadResponse(self):
        response = self.executeSessionTokenService({'sessionToken' : 'non existing token' , 'playerId' : 'non authenticated playerID'}, "score.service.echo", "hello")
        self.assertTrue(isResponseBad(response))

    def test_userSetScoreOtherDoNotRetrieveIt(self):

        seed = self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.start")

        score = {'score' : 3, 'actions' : "sdsd", 'time' : 3}

        #set score (score, actions)
        self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.setScore", score)


        ## get a random score (seed, score, actions) and it should not match
        answer = self.executeGoogleUserSecureService("player2@mail.com", "player2", "score.service.getRandomScore")
        self.assertFalse('score' in answer and score['score'] == answer['score']
                         and 'actions' in answer and score['actions'] == answer['actions']
                         and 'time' in answer and score['time'] == answer['time']
                         and 'seed' in answer and seed == answer['seed']
                         )

    def test_userSetScoreOtherRetrieveItAfterManyPlayerPlayed(self):
        self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.start")
        score = {'score' : 3, 'actions' : "sdsd", 'time' : 0}
        self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.setScore", score)

        # loop many players :
        match = False
        counter = 2
        while not match:
            ## get a random score (seed, score, actions) and it should match at some point

            answer = self.executeGoogleUserSecureService("player" + str(counter) + "@mail.com", "player" + str(counter), "score.service.getRandomScore")
            if answer != {}:
                match = (answer['score'] == score['score'] and answer['actions'] == score['actions'] and answer['time'] == score['time'])

            self.executeGoogleUserSecureService("player" + str(counter) + "@mail.com", "player" + str(counter), "score.service.start")
            checkerScore = {'score' : 10, 'actions' : "sdsdsdsdsd" +str(counter), 'time' : 0}
            self.executeGoogleUserSecureService("player" + str(counter) + "@mail.com", "player" + str(counter), "score.service.setScore", checkerScore)

            counter += 1
            if (counter > 90):
                break

        self.assertTrue(75 < counter < 85)



if __name__ == "__main__":
    unittest.main()
