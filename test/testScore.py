import unittest
from google.appengine.ext import testbed, db
from score.model import Score
from score import service
from player.model import createPlayer, getPlayer, Player, ReviewSession,\
    PendingScore, Record
from google.appengine.api.datastore_types import Key

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()


    def test_given_score_and_approvingReviewer_then_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, 3)

        verifiedScore = Score.get_by_key_name("verified", parent=playerKey)
        self.assertEqual(verifiedScore.value, score['score'])


    def test_given_score_and_twoDisapprovingButAgreeingReviewers_then_playerIsCheater_and_verfiedScoreDoNotChange(self):
        score = {'score' : 99, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, 3)

        createReviewerAndReview("test3", playerKey, 3)

        verifiedScore = Score.get_by_key_name("verified", parent=playerKey)
        self.assertTrue(verifiedScore is None or verifiedScore.value == 0)

        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)


    def test_given_score_and_oneDisapprovingAndOneApprovingReviewer_then_firstReviewerIsCheater_and_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, 99)

        createReviewerAndReview("test3", playerKey, 3)

        verifiedScore = Score.get_by_key_name("verified", parent=playerKey)
        self.assertEqual(verifiedScore.value, 3)

        playerKey = Key.from_path('Player', 'test2')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

    def test_given_score_and_ThreeDisapprovingReviewerOfWhichTwoAgree_then_NonAgreeingReviewerAndPLayerAreCheater(self):
        score = {'score' : 99, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)

        createReviewerAndReview("test2", playerKey, 3)

        createReviewerAndReview("test3", playerKey, 999)

        createReviewerAndReview("test4", playerKey, 3)


        verifiedScore = Score.get_by_key_name("verified", parent=playerKey)
        playerRecord = Record.get_by_key_name('record', parent=playerKey)

        self.assertTrue(verifiedScore is None or verifiedScore.value == 0)
        self.assertEqual(playerRecord.numCheat, 1)


        playerKey = Key.from_path('Player', 'test3')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

    def test_given_score_and_TwoDisapprovingButNonAgreeingReviewerAndOneApprovingReviewer_then_NonApprovingReviewerAreCheater_and_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)
        createReviewerAndReview("test2", playerKey, 99)

        createReviewerAndReview("test3", playerKey, 999)

        createReviewerAndReview("test4", playerKey, 3)

        verifiedScore = Score.get_by_key_name("verified", parent=playerKey)
        self.assertEqual(verifiedScore.value, 3)

        playerKey = Key.from_path('Player', 'test2')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

        playerKey = Key.from_path('Player', 'test3')
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        self.assertEqual(playerRecord.numCheat, 1)

    def test_given_reviewerVerifyingScore_if_playerSetNewScoreInTheMeanTime_when_reviewerSetReviewItShouldBeDiscarded(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId)
        service.start(playerId)
        service.setScore(playerId, score)

        playerKey = Key.from_path('Player', playerId)
        reviewer = createPlayer("reviewer", "reviewer")
        assignScoreReview(reviewer, playerKey)


        reviewer2 = createPlayer("reviewer2", "reviewer2")
        scoreReviewKey = assignScoreReview(reviewer2, playerKey)

        score = {'score' : 4, 'actions' : "sdsd", 'numUpdates' : 3}
        service.start(playerId)
        service.setScore(playerId, score)

        service.reviewScore("reviewer", 4)
        service.reviewScore("reviewer2", 3)

        verifiedScore = Score.get_by_key_name("verified", parent=playerKey)
        self.assertEqual(verifiedScore, None)

        # TDO : move to another test?
        scoreToReview = db.get(scoreReviewKey.parent())
        self.assertEqual(scoreToReview, None)


    def test_newPlayerWithoutReviewAssigned_shouldGetNoReviews(self):
        playerId = "test"
        createPlayer(playerId, playerId)

        playerKey = Key.from_path('Player', playerId)
        reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
        self.assertEqual(reviewSession.currentScoreReviewKey, None)

    def test_newPlayerWithReviewAssigned_shouldGetReviewsAsOldAsRequested(self):

        for i in range(0,41):
            playerId = "playerTest" + str(i)
            createPlayer(playerId, playerId)
            service.start(playerId)
            service.setScore(playerId, {'score' : 4, 'actions' : "sdsd", 'numUpdates' : 3})
            playerKey = Key.from_path('Player', playerId)
            pendingScore = PendingScore.get_by_key_name('pendingScore', parent=playerKey)
            score = pendingScore.nonVerified
            if i == 10: # will be the 30th reviews
                oldReviewKey = Key.from_path('ScoreReview','review', parent=score.key())

        playerId = "test"
        createPlayer(playerId, playerId, 30)

        playerKey = Key.from_path('Player', playerId)
        reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
        self.assertEqual(ReviewSession.currentScoreReviewKey.get_value_for_datastore(reviewSession), oldReviewKey)

    # TODO : assign review on score creation
    def test_given_aCheaterPlayer_ItShouldNotBeAssignedAnyReview(self):

        playerId = "test"
        player =createPlayer(playerId, playerId, 30)

        # set the player as cheater
        player.numCheat = 1
        player.put()


        playerKey = Key.from_path('Player', playerId)
        reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
        self.assertEqual(ReviewSession.currentScoreReviewKey.get_value_for_datastore(reviewSession), None)

def assignScoreReview(reviewer, playerKey):
    pendingScore = PendingScore.get_by_key_name('pendingScore', parent=playerKey)
    scoreKey = PendingScore.nonVerified.get_value_for_datastore(pendingScore)
    scoreReviewKey = Key.from_path('ScoreReview','review', parent=scoreKey)
    reviewerSession = ReviewSession.get_by_key_name('reviewSession', parent=reviewer.key())
    reviewerSession.currentScoreReviewKey = scoreReviewKey
    reviewerSession.put()
    return scoreReviewKey

def createReviewerAndReview(reviewerId, playerKey, scoreValue):
    reviewer = createPlayer(reviewerId, reviewerId)
    scoreReviewKey = assignScoreReview(reviewer, playerKey)
    service.reviewScore(reviewerId, scoreValue)
    return scoreReviewKey

if __name__ == "__main__":
    unittest.main()
