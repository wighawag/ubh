import unittest
from google.appengine.ext import testbed
from score.model import Score
from score import service
from player.model import createPlayer, getPlayer
from score.review import ScoreReview

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

    def test_given_honestScore_then_honestReviewer_should_approve(self):
        score = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        playerId = "test"
        player = createPlayer(playerId, playerId, False)
        service.start(playerId)
        service.setScore(playerId, score)

        score2 = {'score' : 3, 'actions' : "sdsd", 'numUpdates' : 3}
        player2Id = "test2"
        player2 = createPlayer(player2Id, player2Id, False)
        scoreToVerify = Score.gql("WHERE player = :player", player=player).get()
        scoreReview = ScoreReview.get_by_key_name(scoreToVerify.key().id_or_name(), scoreToVerify)
        player2.scoreToVerify = scoreReview
        player2.put()
        service.reviewScore(player2Id, score2['score'])

        player = getPlayer(playerId)
        self.assertEqual(player.verifiedScore, score['score'])


if __name__ == "__main__":
    unittest.main()
