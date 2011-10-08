from google.appengine.ext import db

# Need to be child of a Player
# two score per player :
#  - a nonVerified score which is store as a reference in Player.nonVerifiedScore  (might be None if no score has been submited)
#  - a verified score whose key never change it has "verified" as key_name : might be None if no score has been verified. Its values are overriden when a score is verfied
class Score(db.Model):
    value = db.IntegerProperty(required=True)
    time = db.IntegerProperty(required=True) # seconds ?
    actions = db.BlobProperty(required=True)
    seed = db.IntegerProperty(required=True)
    dateTime = db.DateTimeProperty(auto_now_add=True)
