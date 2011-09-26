from google.appengine.ext import db

from player.model import Player

# Need to be child of a ScoreReview
class ReviewConflict(db.Model):
    player = db.ReferenceProperty(Player)
    scoreValue = db.IntegerProperty()

