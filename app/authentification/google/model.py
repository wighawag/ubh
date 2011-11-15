from google.appengine.ext import db

# playerId refer to a Player entity (might use reference or even parent relationship ?)
class GoogleUser(db.Model):
    creationDateTime = db.DateTimeProperty(auto_now_add=True)
    playerId = db.StringProperty(required=True)
