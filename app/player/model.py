from google.appengine.ext import db

from score.review import ScoreReview, getOldScoreReviewKey
from score.model import Score

class Player(db.Model):
    nickname = db.StringProperty(required=True)
    #gameFriends = db.ListProperty()

# child of Player with key_name='pendingScore'
class PendingScore(db.Model):
    nonVerified = db.ReferenceProperty(Score,required=True)

# child of Player with key_name='record'
class Record(db.Model):
    numCheat = db.IntegerProperty(default=0)
    numScoreReviewed = db.IntegerProperty(default=0)
    numScoreVerified = db.IntegerProperty(default=0)
    creationDateTime = db.DateTimeProperty(auto_now_add=True)

# child of Player with key_name='playSession'
class PlaySession(db.Model):
    seed = db.IntegerProperty(required=True)
    seedDateTime = db.DateTimeProperty(required=True)

# child of Player with key_name='reviewSession'
class ReviewSession(db.Model):
    currentScoreReviewKey = db.ReferenceProperty(ScoreReview,required=True)


def createPlayer(userId, nickname, oldReviewNum = 0):

    player = Player(key_name=userId, nickname=nickname)
    player.put()

    record = Record(key_name='record', parent=player)
    record.put()

    if oldReviewNum > 0:
        # will work since the player has never played before (he will not get his own score)
        scoreReviewKey = getOldScoreReviewKey(oldReviewNum)
        if scoreReviewKey is not None:
            reviewSession = ReviewSession(key_name='reviewSession', currentScoreReviewKey=scoreReviewKey, parent=player)
            reviewSession.put()

    return player

def getPlayer(playerId):
    player = Player.get_by_key_name(playerId)
    return player
