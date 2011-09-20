from google.appengine.ext import db

class FacebookUser(db.Model):
    creationDateTime = db.DateTimeProperty(auto_now_add=True)
    playerId = db.StringProperty()
    oauthToken = db.StringProperty()