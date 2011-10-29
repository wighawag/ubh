from google.appengine.ext import db

from score.model import NonVerifiedScore

class Player(db.Model):
    nickname = db.StringProperty(required=True)
    #gameFriends = db.ListProperty()

# child of Player with key_name='pendingScore'
class PendingScore(db.Model):
    nonVerified = db.ReferenceProperty(NonVerifiedScore,required=True)

# child of Player with key_name='record'
class Record(db.Model):
    numCheat = db.IntegerProperty(default=0)
    numScoreVerified = db.IntegerProperty(default=0)
    creationDateTime = db.DateTimeProperty(auto_now_add=True)

    numScoreReviewed = db.IntegerProperty(default=0)
    numScoreReviewedToday = db.IntegerProperty(default=0)

    numDaysPlayed = db.IntegerProperty(default=0)
    lastDayPlayed = db.DateProperty()
    maxWaitingDateTime = db.DateTimeProperty()

# child of Player with key_name='playSession'
class PlaySession(db.Model):
    seed = db.IntegerProperty(required=True)
    seedDateTime = db.DateTimeProperty(required=True)

# child of Player with key_name='reviewSession'
class ReviewSession(db.Model):
    currentScoreToReview = db.ReferenceProperty(NonVerifiedScore,required=True)


def createPlayer(userId, nickname):

    player = Player(key_name=userId, nickname=nickname)
    player.put()

    record = Record(key_name='record', parent=player)
    record.put()

    return player

def getPlayer(playerId):
    player = Player.get_by_key_name(playerId)
    return player
