from google.appengine.ext import db

from player.model import Player

class ReviewConflict(db.Model):
    player = db.ReferenceProperty(Player)
    scoreValue = db.IntegerProperty()

