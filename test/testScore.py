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

        score2 = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        player2Id = "test2"
        player2 = createPlayer(player2Id, player2Id, False)

        scoreKey = GqlQuery("SELECT __key__ FROM Score WHERE player = :player", player=player).get();
        scoreReviewKey = Key.from_path('ScoreReview','uniqueChild', parent=scoreKey)
        player2.currentScoreReviewKey = scoreReviewKey
        player2.put()

        service.reviewScore(player2Id, score2['score'])

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

        score2 = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        player2Id = "test2"
        player2 = createPlayer(player2Id, player2Id, False)

        scoreKey = GqlQuery("SELECT __key__ FROM Score WHERE player = :player", player=player).get();
        scoreReviewKey = Key.from_path('ScoreReview','uniqueChild', parent=scoreKey)
        player2.currentScoreReviewKey = scoreReviewKey
        player2.put()

        service.reviewScore(player2Id, score2['score'])

        score3 = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        player3Id = "test2"
        player3 = createPlayer(player3Id, player3Id, False)

        scoreKey = GqlQuery("SELECT __key__ FROM Score WHERE player = :player", player=player).get();
        scoreReviewKey = Key.from_path('ScoreReview','uniqueChild', parent=scoreKey)
        player3.currentScoreReviewKey = scoreReviewKey
        player3.put()

        service.reviewScore(player3Id, score3['score'])

        player = getPlayer(playerId)
        self.assertEqual(player.verifiedScore, 2) # old verified score did not change

        self.assertEqual(player.numCheat, 1)


if __name__ == "__main__":
    unittest.main()
