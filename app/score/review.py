from google.appengine.ext import db

# Need to be child of a Score
class ScoreReview(db.Model):
    potentialReviewers = db.StringListProperty()
    dateTime = db.DateTimeProperty(auto_now_add=True)

def getOldScoreReviewKey(oldReviewNum):
    result = db.GqlQuery("SELECT __key__ FROM ScoreReview ORDER BY dateTime DESC").fetch(1,oldReviewNum)
    if len(result) == 0:
        return None
    return result[0]

