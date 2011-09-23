#######################################
## Test purpose #######################
#######################################
from score.reviewconflict import ReviewConflict
def echo(playerId, data):
    return "player " + playerId + " : " + data

#######################################
#######################################
#######################################

import random
import datetime
from score.model import createScore, getScoreReviewKeyForReviewer, Score
from player.model import getPlayer, Player

from google.appengine.ext import db

MAX_AS3_UINT_VALUE = 4294967295;

UPDATE_DELTA_MILISECOND = 30 # updat rate on flash player
PAUSE_MULTIPLIER = 1.5 # quantity of pause allowed
MINIMUM_TIME = 10 # margin in seconds to send the data accrros

def _getPlayerFromId(playerId):
    player = getPlayer(playerId)
    if player is None:
        raise Exception('Player %s could not be fetched' % playerId)
    return player

def start(playerId):
    player = _getPlayerFromId(playerId)
    player.seed = random.randint(1, MAX_AS3_UINT_VALUE)
    player.seedDateTime = datetime.datetime.now()
    player.put()
    return player.seed

def setScore(playerId, score):
    player = _getPlayerFromId(playerId)
    if player.seed is None:
        raise Exception("Seed not set while trying to set a new score. start need to be called before setScore")


    # RENABLE THIS CHECKS + ALLOW TESTS TO DEAL WITH TIME

    #minScoreTime = datetime.timedelta(milliseconds=(score['numUpdates'] * UPDATE_DELTA_MILISECOND))
    #if player.seedDate + minScoreTime > datetime.datetime.now():
    #    raise Exception("player would not have enough time to play such score")

    #maxScoreTime = minScoreTime * PAUSE_MULTIPLIER + datetime.timedelta(seconds=MINIMUM_TIME)
    #if player.seedDate + maxScoreTime < datetime.datetime.now():
    #    raise Exception("player has spend too much time to play such score")

    # TODO : fetch potential reviewers
    reviewers = []

    createScore(player, score['score'], score['actions'], score['numUpdates'], player.seed, reviewers)

    player.seed = None
    player.seedDate = None
    player.put()


def getRandomScore(playerId):
    player = _getPlayerFromId(playerId)

    scoreReviewKey = Player.currentScoreReviewKey.get_value_for_datastore(player)

    if scoreReviewKey is None:
        scoreReviewKey = getScoreReviewKeyForReviewer(playerId)
        if scoreReviewKey is None:
            return {}
        player.currentScoreReviewKey = scoreReviewKey
        player.put()

    score = db.get(scoreReviewKey.parent())

    return {'score' : score.value, 'actions' : score.actions, 'numUpdates' : score.numUpdates, 'seed' : score.seed}


def reviewScore(playerId, scoreValue):
    player = _getPlayerFromId(playerId)
    scoreReviewKey = Player.currentScoreReviewKey.get_value_for_datastore(player)
    if scoreReviewKey is None:
        #nothing to review (should throw Exception)
        return
    scoreKey = scoreReviewKey.parent()
    score = Score.get(scoreKey)

    if score.value == scoreValue:
        score.player.verifiedScore = score.value # maybe set verifiedScore to actual score model? or delete score ?
        score.player.put()

        #delete conflicts and set conflicting reviewers as cheater
        conflicts = ReviewConflict.gql("WHERE review=:review", review=scoreReviewKey).fetch(3) # shoud not be more than 2
        for conflict in conflicts:
            if conflict.scoreValue != scoreValue:
                conflict.player.numCheat+=1
                conflict.player.put()
                conflict.delete()
        db.delete(scoreReviewKey)
        #TODO : deal with no more existing review and conflicts when reviewScore is called after getRandomScore was already called with the review being deleted (?)
    else:
        #check whether a conflict exist with the same score value, if that is the case, player has cheated
        conflicts = ReviewConflict.gql("WHERE review=:review", review=scoreReviewKey).fetch(3) # shoud not be more than 2
        for conflict in conflicts:
            if conflict.scoreValue == scoreValue:
                #player is a cheater
                score.player.numCheat+=1
                score.player.put()

                #remove stuffs and assign cheater status to reviewer
                for conflict in conflicts:
                    if conflict.scoreValue != scoreValue:
                        conflict.player.numCheat+=1
                        conflict.player.put()
                        conflict.delete()
                db.delete(scoreReviewKey)
                return
            else:
                #TODO : deal with : if too many different we cannot really deal with them, it should not happen though
                pass
        newConflict = ReviewConflict(player=player,review=scoreReviewKey,scoreValue=scoreValue)
        newConflict.put()


