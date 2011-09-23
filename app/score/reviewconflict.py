from google.appengine.ext import db

from player.model import Player
from score.review import ScoreReview

class ReviewConflict(db.Model):
    player = db.ReferenceProperty(Player)
    review = db.ReferenceProperty(ScoreReview)
    scoreValue = db.IntegerProperty()

