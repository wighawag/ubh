from google.appengine.ext import db

from score.review import ScoreReview

# Need to be child of a Player
# two score per player :
#  - a nonVerified score which is store as a reference in Player.nonVerifiedScore  (might be None if no score has been submited)
#  - a verified score whose key never change it has "verified" as key_name : might be None if no score has been verified. Its values are overriden when a score is verfied
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
        nonVerifiedScore = player.nonVerifiedScore
        if nonVerifiedScore is None or value > nonVerifiedScore.value:
            nonVerifiedScore = Score(value=value,actions=actions,numUpdates=numUpdates,seed=seed, parent=player)
            nonVerifiedScore.put()
            if player.nonVerifiedScore is not None:
                player.nonVerifiedScore.delete()
            player.nonVerifiedScore = nonVerifiedScore
            player.put()

            scoreReview = ScoreReview(key_name="review",parent=nonVerifiedScore, potentialReviewers=reviewers)
            scoreReview.put();
            return nonVerifiedScore
    return None

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
    # get any review assigned to the player
    # TODO : add priority to reviews (for example when cheater are identified?)
    scoreReview = db.GqlQuery("SELECT __key__ FROM ScoreReview WHERE potentialReviewers = :playerId", playerId=playerId).get()
    return scoreReview
