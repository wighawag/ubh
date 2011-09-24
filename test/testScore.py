import unittest
from google.appengine.ext import testbed
from score.model import Score
from score import service
from player.model import createPlayer, getPlayer
from google.appengine.ext.db import GqlQuery
from google.appengine.api.datastore_types import Key

class Test(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def testInsertEntity(self):
        Score().put()
        self.assertEqual(1, len(Score.all().fetch(2)))

    def test_given_score_and_approvingReviewer_then_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        player = createPlayer(playerId, playerId, False)
        service.start(playerId)
        service.setScore(playerId, score)

        createReviewerAndReview("test2", player, 3)

        player = getPlayer(playerId)
        self.assertEqual(player.verifiedScore, score['score'])

    def test_given_score_and_twoDisapprovingReviewers_then_playerIsCheater_and_verfiedScoreDoNotChange(self):
        score = {'score' : 99, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        player = createPlayer(playerId, playerId, False)
        player.verifiedScore = 2 # old score
        player.put()
        service.start(playerId)
        service.setScore(playerId, score)

        createReviewerAndReview("test2", player, 3)

        createReviewerAndReview("test3", player, 3)

        player = getPlayer(playerId)
        self.assertEqual(player.verifiedScore, 2) # old verified score did not change

        self.assertEqual(player.numCheat, 1)


    def test_given_score_and_oneDisapprovingAndOneApprovingReviewer_then_firstReviewerIsCheater_and_playerVerifiedScoreIsUpdated(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        player = createPlayer(playerId, playerId, False)
        player.verifiedScore = 2 # old score
        player.put()
        service.start(playerId)
        service.setScore(playerId, score)

        createReviewerAndReview("test2", player, 99)

        createReviewerAndReview("test3", player, 3)

        player = getPlayer(playerId)
        self.assertEqual(player.verifiedScore, 3) # old verified score did not change

        player2 = getPlayer("test2")
        self.assertEqual(player2.numCheat, 1)

def assignScoreReview(reviewer, playerToCheck):
    scoreKey = GqlQuery("SELECT __key__ FROM Score WHERE player = :player", player=playerToCheck).get();
    scoreReviewKey = Key.from_path('ScoreReview','uniqueChild', parent=scoreKey)
    reviewer.currentScoreReviewKey = scoreReviewKey
    reviewer.put()

def createReviewerAndReview(reviewerId, player, scoreValue):
    reviewer = createPlayer(reviewerId, reviewerId, False)
    assignScoreReview(reviewer, player)
    service.reviewScore(reviewerId, scoreValue)

if __name__ == "__main__":
    unittest.main()
