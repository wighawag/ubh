import unittest
from google.appengine.ext import testbed, db
from score.model import VerifiedScore
from score import service
from player.model import createPlayer, ReviewSession, PendingScore, Record,\
    VerifiedScoreWrapper
from google.appengine.api.datastore_types import Key
from stats.model import setReviewTimeUnit

from time import sleep
from admin.model import getAdmin, setAdmin
from error import ADMIN_ONLY, TOO_MANY_REVIEWS

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()


    def test_given_score_and_approvingReviewer_then_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, {'score':3, 'time': 0})

        verifiedScoreWrapper = VerifiedScoreWrapper.get_by_key_name('verifiedScore', parent=playerKey)
        verifiedScore = verifiedScoreWrapper.verified
        self.assertEqual(verifiedScore.value, score['score'])


    def test_given_score_and_twoDisapprovingButAgreeingReviewers_then_playerIsCheater_and_verfiedScoreDoNotChange(self):
        score = {'score' : 99, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, {'score':3, 'time': 0})

        createReviewerAndReview("test3", playerKey, {'score':3, 'time': 0})

        verifiedScore = VerifiedScore.get_by_key_name("verified", parent=playerKey)
        self.assertTrue(verifiedScore is None or verifiedScore.value == 0)

        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

    def test_given_goodScoreWithWrongTime_thenPlayerIsCheater(self):
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, {'score':3, 'time': 3})

        createReviewerAndReview("test3", playerKey, {'score':3, 'time': 3})

        verifiedScore = VerifiedScore.get_by_key_name("verified", parent=playerKey)
        self.assertTrue(verifiedScore is None or verifiedScore.value == 0)

        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)


    def test_given_score_and_oneDisapprovingAndOneApprovingReviewer_then_firstReviewerIsCheater_and_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, {'score':99, 'time': 0})

        createReviewerAndReview("test3", playerKey, {'score':3, 'time': 0})

        verifiedScoreWrapper = VerifiedScoreWrapper.get_by_key_name('verifiedScore', parent=playerKey)
        verifiedScore = verifiedScoreWrapper.verified
        self.assertEqual(verifiedScore.value, 3)

        playerKey = Key.from_path('Player', 'test2')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

    def test_given_score_and_ThreeDisapprovingReviewerOfWhichTwoAgree_then_NonAgreeingReviewerAndPLayerAreCheater(self):
        score = {'score' : 99, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, {'score':3, 'time': 0})

        createReviewerAndReview("test3", playerKey, {'score':999, 'time': 0})

        createReviewerAndReview("test4", playerKey, {'score':3, 'time': 0})


        verifiedScore = VerifiedScore.get_by_key_name("verified", parent=playerKey)
        playerRecord = Record.get_by_key_name('record', parent=playerKey)

        self.assertTrue(verifiedScore is None or verifiedScore.value == 0)
        self.assertEqual(playerRecord.numCheat, 1)


        playerKey = Key.from_path('Player', 'test3')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

    def test_given_score_and_TwoDisapprovingButNonAgreeingReviewerAndOneApprovingReviewer_then_NonApprovingReviewerAreCheater_and_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)
        createReviewerAndReview("test2", playerKey, {'score':99, 'time': 0})

        createReviewerAndReview("test3", playerKey, {'score':999, 'time': 0})

        createReviewerAndReview("test4", playerKey, {'score':3, 'time': 0})

        verifiedScoreWrapper = VerifiedScoreWrapper.get_by_key_name('verifiedScore', parent=playerKey)
        verifiedScore = verifiedScoreWrapper.verified
        self.assertEqual(verifiedScore.value, 3)

        playerKey = Key.from_path('Player', 'test2')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

        playerKey = Key.from_path('Player', 'test3')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

    def test_given_reviewerVerifyingScore_if_playerSetNewScoreInTheMeanTime_when_reviewerSetReviewItShouldBeDiscarded(self):
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)
        reviewer = createPlayer("reviewer", "reviewer")
        assignScoreReview(reviewer, playerKey)


        reviewer2 = createPlayer("reviewer2", "reviewer2")
        scoreToReview = assignScoreReview(reviewer2, playerKey)

        score = {'score' : 4, 'proof' : "sdsd", 'time' : 0}
        service.start(playerId)
        service.setScore(playerId, score)

        service.reviewScore("reviewer", {'score':4, 'time': 0})
        service.reviewScore("reviewer2", {'score':3, 'time': 0})

        verifiedScore = VerifiedScore.get_by_key_name("verified", parent=playerKey)
        self.assertEqual(verifiedScore, None)

        # TDO : move to another test?
        scoreToReview = db.get(scoreToReview.key())
        self.assertEqual(scoreToReview, None)


    def test_newPlayerWithoutReviewAssigned_shouldGetNoReviews(self):
        playerId = "test"
        createPlayer(playerId, playerId)

        playerKey = Key.from_path('Player', playerId)
        reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
        self.assertEqual(reviewSession, None)

#    def test_newPlayerWithReviewAssigned_shouldGetReviewsAsOldAsRequested(self):
#
#        for i in range(0,41):
#            playerId = "playerTest" + str(i)
#            createPlayer(playerId, playerId)
#            service.start(playerId)
#            service.setScore(playerId, {'score' : 4, 'proof' : "sdsd", 'time' : 0})
#            playerKey = Key.from_path('Player', playerId)
#            pendingScore = PendingScore.get_by_key_name('pendingScore', parent=playerKey)
#            score = pendingScore.nonVerified
#            if i == 10: # will be the 30th reviews
#                oldReviewKey = Key.from_path('ScoreReview','review', parent=score.key())
#
#        playerId = "test"
#        createPlayer(playerId, playerId, 30)
#
#        playerKey = Key.from_path('Player', playerId)
#        reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
#        self.assertNotEqual(reviewSession, None)
#        self.assertEqual(reviewSession.currentScoreToReview,db.get(oldReviewKey))



    def test_given_aScoreSubmitedLate_ItShouldNotBeSubmited(self):
        score = {'score' : 3, 'proof' : "sdsd", 'time' : -10000} # -10 to fake a later submited score
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)
        pendingScore = PendingScore.get_by_key_name('pendingScore', parent=playerKey)
        self.assertEqual(pendingScore, None)


    def test_given_aScoreSubmitedTooEarly_ItShouldNotBeSubmited(self):
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 10000}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)
        pendingScore = PendingScore.get_by_key_name('pendingScore', parent=playerKey)
        self.assertEqual(pendingScore, None)

    def test_given_aReviewerReviewingTwoTimesTooQuickly_ItShouldBeAskedToRetryLater(self):

        setReviewTimeUnit(2000)
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test1"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test2"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        createPlayer("reviewer1", "reviewer1")

        sleep(3)

        service.getRandomScore("reviewer1")
        service.reviewScore("reviewer1", {'score':3, 'time': 0})

        response= service.getRandomScore("reviewer1")

        self.assertTrue('error' in response and response['error']['code'] == TOO_MANY_REVIEWS['code'] and response['error']['retry']  > 0)

    def test_given_aReviewerGettingRandomScoreQuickly_ItShouldNotBeAskedToRetryLater(self):

        setReviewTimeUnit(2000)
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test1"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test2"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        createPlayer("reviewer1", "reviewer1")

        sleep(3)

        service.getRandomScore("reviewer1")
        response= service.getRandomScore("reviewer1")

        self.assertFalse('retry' in response and response['retry'] > 0 and 'error' in response and response['error'] == TOO_MANY_REVIEWS['code'])


    def test_given_aReviewerTryingToReviewAsAdmin_ItShouldBeGivenAnError(self):

        setReviewTimeUnit(0)
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test1"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        createPlayer("reviewer1", "reviewer1")

        service.getRandomScore("reviewer1")
        response = service.reviewScore("reviewer1", {'score':3, 'time': 0}, True)

        self.assertTrue('error' in response and response['error']['code'] == ADMIN_ONLY['code'])

    def test_given_aAdminReviewerTryingToReviewAsAdmin_ItShouldSucceed(self):

        setReviewTimeUnit(0)
        score = {'score' : 3, 'proof' : "sdsd", 'time' : 0}
        playerId = "test1"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        createPlayer("reviewer1", "reviewer1")

        admin = getAdmin()
        admin.playerList.append('reviewer1')
        setAdmin(admin)

        service.getRandomScore("reviewer1")
        response = service.reviewScore("reviewer1", {'score':3, 'time': 0}, True)


        self.assertTrue('result' in response)

        playerKey = Key.from_path('Player', playerId)
        verifiedScoreWrapper = VerifiedScoreWrapper.get_by_key_name('verifiedScore', parent=playerKey)
        verifiedScore = verifiedScoreWrapper.verified
        self.assertEqual(verifiedScore.value, 3)
        self.assertEqual(verifiedScore.approvedByAdmin, True)

    def test_given_aAdminReviewerTryingToReviewAsAdmin_ItShouldSucceedAndDeclareNonAgreeingConflictingReviewerAsCheaters(self):

        setReviewTimeUnit(0)
        score = {'score' : 99, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, {'score':3, 'time': 0})

        createReviewerAndReview("test3", playerKey, {'score':999, 'time': 0})

        createReviewerAndReview("test4", playerKey, {'score':3, 'time': 0}, True)


        verifiedScore = VerifiedScore.get_by_key_name("verified", parent=playerKey)
        playerRecord = Record.get_by_key_name('record', parent=playerKey)

        self.assertTrue(verifiedScore is None or verifiedScore.value == 0)
        self.assertEqual(playerRecord.numCheat, 1)


        playerKey = Key.from_path('Player', 'test3')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

        playerKey = Key.from_path('Player', 'test2')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 0)

    def test_given_aAdminReviewerDisapprovingAnAlreadyVerifiedScore_ItShouldDeclareVerifierAsACheaterAndOtherAsNonCheaters(self):

        setReviewTimeUnit(0)
        score = {'score' : 99, 'proof' : "sdsd", 'time' : 0}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, {'score':3, 'time': 0})

        createReviewerAndReview("test3", playerKey, {'score':999, 'time': 0})

        createReviewerAndReview("test4", playerKey, {'score':99, 'time': 0}) # verified


        verifiedScoreWrapper = VerifiedScoreWrapper.get_by_key_name('verifiedScore', parent=playerKey)
        verifiedScore = verifiedScoreWrapper.verified
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertTrue(verifiedScore.value == 99)
        self.assertEqual(playerRecord.numCheat, 0)

        createPlayer('admin1', 'admin1')
        admin = getAdmin()
        admin.playerList.append('admin1')
        setAdmin(admin)
        service.getHighestNonApprovedScore('admin1')

        service.approveScore('admin1', {'score':3, 'time': 0})


        verifiedScoreWrapper = VerifiedScoreWrapper.get_by_key_name('verifiedScore', parent=playerKey)
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertTrue(verifiedScoreWrapper is None)
        self.assertEqual(playerRecord.numCheat, 1)

        playerKey = Key.from_path('Player', 'test3')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 0)

        playerKey = Key.from_path('Player', 'test2')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 0)

        playerKey = Key.from_path('Player', 'test4')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)



def assignScoreReview(reviewer, playerKey):
    pendingScore = PendingScore.get_by_key_name('pendingScore', parent=playerKey)
    scoreToReview = pendingScore.nonVerified
    reviewerSession = ReviewSession(key_name='reviewSession', currentScoreToReview=scoreToReview, parent=reviewer.key())
    reviewerSession.put()
    return scoreToReview

def createReviewerAndReview(reviewerId, playerKey, scoreValue, adminMode = False):
    reviewer = createPlayer(reviewerId, reviewerId)
    if adminMode:
        admin = getAdmin()
        admin.playerList.append(reviewerId)
        setAdmin(admin)
    scoreToReview = assignScoreReview(reviewer, playerKey)
    service.reviewScore(reviewerId, scoreValue, adminMode)
    return scoreToReview

if __name__ == "__main__":
    unittest.main()
