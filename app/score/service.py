#######################################
## Test purpose #######################
#######################################
def echo(playerId, data):
    return "player " + playerId + " : " + data

#######################################
#######################################
#######################################

import random
import datetime
from score.model import createScore, getScoreForReviewer, Score
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

    scoreReview = Player.scoreToVerify.get_value_for_datastore(player)

    if scoreReview is None:
        scoreReview = getScoreForReviewer(playerId)
        if scoreReview is None:
            return {}
        player.scoreToVerify = scoreReview
        player.put()

    score = db.get(scoreReview.parent())

    return {'score' : score.value, 'actions' : score.actions, 'numUpdates' : score.numUpdates, 'seed' : score.seed}


def reviewScore(playerId, scoreValue):
    player = _getPlayerFromId(playerId)
    scoreReviewKey = Player.scoreToVerify.get_value_for_datastore(player)
    scoreKey = scoreReviewKey.parent()
    score = Score.get(scoreKey)
    if score is not None and score.value == scoreValue:
        score.player.verifiedScore = score.value # maybe set verifiedScore to actual score model? or delete score ? and scoreReview?
        score.player.put()
    else:
        pass


