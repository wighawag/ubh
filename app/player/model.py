from google.appengine.ext import db

from score.review import ScoreReview, getOldScoreReview

class Player(db.Model):
    nickname = db.StringProperty(required=True)
    creationDateTime = db.DateTimeProperty(auto_now_add=True)
    seed = db.IntegerProperty()
    seedDateTime = db.DateTimeProperty()
    scoreToVerify = db.ReferenceProperty(ScoreReview)
    verifiedScore = db.IntegerProperty() # should be db.BlobProperty() do deal with any kind of score/state data ?
    #gameFriends = db.ListProperty()

def createPlayer(userId, nickname, linkOldReview = False):
    player = Player(key_name=userId, nickname=nickname)

    if linkOldReview:
        # will work since the player has never played before (he will not get his own score)
        scoreReview = getOldScoreReview()
        if scoreReview is not None:
            player.scoreToVerify = scoreReview

    player.put()
    return player

def getPlayer(playerId):
    player = Player.get_by_key_name(playerId)
    return player
