from google.appengine.ext import db
from player.model import Player


class GoogleUser(db.Model):
    creationDateTime = db.DateTimeProperty(auto_now_add=True)
    playerId = db.StringProperty()
