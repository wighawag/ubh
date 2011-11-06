from google.appengine.ext import db

# Need to be child of a Player
#  - a verified score whose key never change it has "verified" as key_name : might be None if no score has been verified. Its values are overriden when a score is verfied
class VerifiedScore(db.Model):
    value = db.IntegerProperty(required=True)
    time = db.IntegerProperty(required=True) # seconds ?
    proof = db.BlobProperty(required=True)
    seed = db.ByteStringProperty(required=True)
    version = db.IntegerProperty(required=True)
    dateTime = db.DateTimeProperty(auto_now_add=True)
    conflictingReviewers = db.StringListProperty()
    verifier = db.StringProperty(required=True)
    approvedByAdmin = db.BooleanProperty(required=True)

# Need to be child of a Player
#  - a nonVerified score which is store as a reference in PendingScore.nonVerifiedScore  (might be None if no score has been submited)
class NonVerifiedScore(db.Model):
    value = db.IntegerProperty(required=True)
    time = db.IntegerProperty(required=True) # seconds ?
    proof = db.BlobProperty(required=True)
    seed = db.ByteStringProperty(required=True)
    version = db.IntegerProperty(required=True)
    dateTime = db.DateTimeProperty(auto_now_add=True)
    conflictingReviewers = db.StringListProperty()