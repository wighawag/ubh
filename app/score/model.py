from google.appengine.ext import db

from score.review import ScoreReview

class Score(db.Model):
    value = db.IntegerProperty(default=0)
    numUpdates = db.IntegerProperty()
    actions = db.BlobProperty()
    seed = db.IntegerProperty()
    dateTime = db.DateTimeProperty(auto_now_add=True)


def createScore(player, value, actions, numUpdates, seed, reviewers):
    # TODO : transaction  ?

    verifiedScore = Score.get_by_key_name("verified", parent=player)

    if verifiedScore is None or value > verifiedScore.value:
        nonVerifiedScore = Score.get_or_insert("nonVerified", parent=player)
        if value > nonVerifiedScore.value:
            nonVerifiedScore.value = value
            nonVerifiedScore.actions = actions
            nonVerifiedScore.numUpdates = numUpdates
            nonVerifiedScore.seed = seed
            nonVerifiedScore.put()

    scoreReview = ScoreReview(key_name="uniqueChild",parent=nonVerifiedScore, potentialReviewers=reviewers)
    scoreReview.put();
    #return nonVerifiedScore

def setScoreVerified(score):
    verifiedScore = Score(key_name="verified", parent=score.parent(), value=score.value, actions=score.actions, numUpdates=score.numUpdates, seed=score.seed)
    #verifiedScore = Score.get_or_insert("verified", score.parent())
    #verifiedScore.value = score.value
    #verifiedScore.actions = score.actions
    #verifiedScore.numUpdates = score.numUpdates
    #verifiedScore.seed = score.seed
    verifiedScore.put()
    score.delete()

def getScoreReviewKeyForReviewer(playerId):
    scoreReview = db.GqlQuery("SELECT __key__ FROM ScoreReview WHERE potentialReviewers = :playerId", playerId=playerId).get()
    return scoreReview
