import unittest
from google.appengine.ext import testbed
from score.model import Score
from score import service
from player.model import createPlayer, getPlayer, Player
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
        createPlayer(playerId, playerId, False)
        service.start(playerId)
        service.setScore(playerId, score)

        player = getPlayer("test")

        createReviewerAndReview("test2", player, 3)

        player = getPlayer(playerId)
        verifiedScore = Score.get_by_key_name("verified", parent=player)
        self.assertEqual(verifiedScore.value, score['score'])


    def test_given_score_and_twoDisapprovingButAgreeingReviewers_then_playerIsCheater_and_verfiedScoreDoNotChange(self):
        score = {'score' : 99, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId, False)
        service.start(playerId)
        service.setScore(playerId, score)

        player = getPlayer("test")

        createReviewerAndReview("test2", player, 3)

        createReviewerAndReview("test3", player, 3)

        player = getPlayer(playerId)
        verifiedScore = Score.get_by_key_name("verified", parent=player)
        self.assertTrue(verifiedScore is None or verifiedScore.value == 0)

        self.assertEqual(player.numCheat, 1)


    def test_given_score_and_oneDisapprovingAndOneApprovingReviewer_then_firstReviewerIsCheater_and_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId, False)
        service.start(playerId)
        service.setScore(playerId, score)

        player = getPlayer("test")

        createReviewerAndReview("test2", player, 99)

        createReviewerAndReview("test3", player, 3)

        player = getPlayer(playerId)
        verifiedScore = Score.get_by_key_name("verified", parent=player)
        self.assertEqual(verifiedScore.value, 3)

        player2 = getPlayer("test2")
        self.assertEqual(player2.numCheat, 1)

    def test_given_score_and_ThreeDisapprovingReviewerOfWhichTwoAgree_then_NonAgreeingReviewerAndPLayerAreCheater(self):
        score = {'score' : 99, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId, False)
        service.start(playerId)
        service.setScore(playerId, score)

        player = getPlayer("test")

        createReviewerAndReview("test2", player, 3)

        createReviewerAndReview("test3", player, 999)

        createReviewerAndReview("test4", player, 3)

        player = getPlayer(playerId)
        verifiedScore = Score.get_by_key_name("verified", parent=player)

        self.assertTrue(verifiedScore is None or verifiedScore.value == 0)
        self.assertEqual(player.numCheat, 1)


        player = getPlayer("test3")
        self.assertEqual(player.numCheat, 1)

    def test_given_score_and_TwoDisapprovingButNonAgreeingReviewerAndOneApprovingReviewer_then_NonApprovingReviewerAreCheater_and_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId, False)
        service.start(playerId)
        service.setScore(playerId, score)

        player = getPlayer("test")
        createReviewerAndReview("test2", player, 99)

        createReviewerAndReview("test3", player, 999)

        createReviewerAndReview("test4", player, 3)

        player = getPlayer(playerId)
        verifiedScore = Score.get_by_key_name("verified", parent=player)
        self.assertEqual(verifiedScore.value, 3)

        player = getPlayer("test2")
        self.assertEqual(player.numCheat, 1)

        player = getPlayer("test3")
        self.assertEqual(player.numCheat, 1)

    def test_given_reviewerVerifyingScore_if_playerSetNewScoreInTheMeanTime_when_reviewerSetReviewItShouldBeDiscarded(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId, False)
        service.start(playerId)
        service.setScore(playerId, score)

        player = getPlayer("test")
        reviewer = createPlayer("reviewer", "reviewer", False)
        assignScoreReview(reviewer, player)


        reviewer2 = createPlayer("reviewer2", "reviewer2", False)
        assignScoreReview(reviewer2, player)

        score = {'score' : 4, 'actions' : "sdsd", 'numUpdates' : 3}
        service.start(playerId)
        service.setScore(playerId, score)

        service.reviewScore("reviewer", 4)
        service.reviewScore("reviewer2", 3)

        player = getPlayer(playerId)
        verifiedScore = Score.get_by_key_name("verified", parent=player)
        self.assertEqual(verifiedScore, None)

     def test_newPlayerWithoutFriends_shouldGetVeryOldReviews(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        createPlayer(playerId, playerId, False)# False means to not assign old reviews

        player = getPlayer("test")
        oldReview = None
        self.assertEqual(player.currentScoreReviewKey, oldReview)


def assignScoreReview(reviewer, playerToCheck):
    #scoreKey = Key.from_path('Score', 'nonVerified', parent=playerToCheck)
    #scoreReviewKey = Key.from_path('ScoreReview','uniqueChild', parent=scoreKey)
    scoreKey = Player.nonVerifiedScore.get_value_for_datastore(playerToCheck)
    scoreReviewKey = Key.from_path('ScoreReview','review', parent=scoreKey)
    reviewer.currentScoreReviewKey = scoreReviewKey
    reviewer.put()

def createReviewerAndReview(reviewerId, player, scoreValue):
    reviewer = createPlayer(reviewerId, reviewerId, False)
    assignScoreReview(reviewer, player)
    service.reviewScore(reviewerId, scoreValue)

if __name__ == "__main__":
    unittest.main()
