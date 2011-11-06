import unittest

from app import gateway
from webtest import TestApp

from authentification.google.googleUserEntryPoint import application as googleUserApp


from google.appengine.ext import testbed
from helper.googleUser import setCurrentUser, logoutCurrentUser

from helper.amf import executeService, getMessageFromResponse
from helper.html import getFlashVarsFromResponse
from stats.model import setReviewTimeUnit



import time
from error import NO_ACTIVE_SESSION_ERROR

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
        return executeService(gateway(True), "sessionTokenCall", flashvars['sessionToken'], flashvars['playerId'], service, *args)




    def test_googleUserAuthenticatedEcho(self):
        answer = self.executeGoogleUserSecureService("test@mail.com", "test", "score.service.echo", "hello")
        self.assertEqual(answer, "player googleUser_test : hello")

    def test_unauthenticatedEchoReturnBadResponse(self):
        message = self.executeSessionTokenService({'sessionToken' : 'non existing token' , 'playerId' : 'non authenticated playerID'}, "score.service.echo", "hello")
        response = message.body.body
        self.assertTrue('success' in response and response['success'] == False and 'error' in response and response['error'] == NO_ACTIVE_SESSION_ERROR['code'])

    def test_userSetScoreOtherDoNotRetrieveItIfTimeUnitNotPassed(self):

        setReviewTimeUnit(5000)
        seed = self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.start")

        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}

        #set score (score, actions)
        self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.setScore", score)


        ## get a random score (seed, score, actions) and it should not match
        answer = self.executeGoogleUserSecureService("player2@mail.com", "player2", "score.service.getRandomScore")
        self.assertFalse('proof' in answer and score['proof'] == answer['proof'] and 'seed' in answer and seed == answer['seed'])

    def test_userSetScoreOtherRetrieveItIfTimeUnitPassed(self):

        setReviewTimeUnit(3000)
        response = self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.start")
        seed= response['seed']

        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}

        #set score (score, actions)
        self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.setScore", score)

        time.sleep(3)

        ## get a random score (seed, score, actions) and it should match
        answer = self.executeGoogleUserSecureService("player2@mail.com", "player2", "score.service.getRandomScore")
        self.assertTrue('proof' in answer and score['proof'] == answer['proof'] and 'seed' in answer and seed == answer['seed'])

#    def test_userSetScoreOtherRetrieveItAfterManyPlayerPlayed(self):
#        self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.start")
#        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
#        self.executeGoogleUserSecureService("player1@mail.com", "player1", "score.service.setScore", score)
#
#        # loop many players :
#        match = False
#        counter = 2
#        while not match:
#            ## get a random score (seed, score, actions) and it should match at some point
#
#            answer = self.executeGoogleUserSecureService("player" + str(counter) + "@mail.com", "player" + str(counter), "score.service.getRandomScore")
#            if answer != {}:
#                match = (answer['proof'] == score['proof']) # check whether they are assigned to review the first player's score
#
#            self.executeGoogleUserSecureService("player" + str(counter) + "@mail.com", "player" + str(counter), "score.service.start")
#            checkerScore = {'score' : 10, 'proof' : "sdsdsdsdsd" +str(counter), 'time' : 0}
#            self.executeGoogleUserSecureService("player" + str(counter) + "@mail.com", "player" + str(counter), "score.service.setScore", checkerScore)
#
#            counter += 1
#            if (counter > 90):
#                break
#
#        self.assertTrue(75 < counter < 85)



if __name__ == "__main__":
    unittest.main()
