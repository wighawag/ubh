from google.appengine.ext import db

class ScoreReview(db.Model):
    potentialReviewers = db.StringListProperty()
    dateTime = db.DateTimeProperty(auto_now_add=True)
    
def getOldScoreReview():
    return db.GqlQuery("SELECT __key__ FROM ScoreReview ORDER BY dateTime").get()

