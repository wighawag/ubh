from google.appengine.ext import db

from player.model import Player
from score.review import ScoreReview

class Score(db.Model):
    player = db.ReferenceProperty(Player)
    value = db.IntegerProperty()
    numUpdates = db.IntegerProperty()
    actions = db.BlobProperty()
    seed = db.IntegerProperty()
    dateTime = db.DateTimeProperty(auto_now_add=True)
    numValidation = db.IntegerProperty()


def createScore(player, value, actions, numUpdates, seed, reviewers):

    # TODO : transaction  ?

    score = Score(key_name=""+str(seed),player=player, value=value, actions=actions, numUpdates=numUpdates, seed=seed)
    score.put()

    scoreReview = ScoreReview(key_name=score.key().id_or_name(),parent=score, potentialReviewers=reviewers)
    scoreReview.put();
    return score

def getScoreById(scoreId):
    return Score.get_by_id(scoreId)

def getScoreForReviewer(playerId):
    scoreReview = db.GqlQuery("SELECT __key__ FROM ScoreReview WHERE potentialReviewers = :playerId", playerId=playerId).get()
    return scoreReview
