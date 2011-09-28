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
from score.model import createScore, getScoreReviewKeyForReviewer, Score,\
    setScoreVerified
from player.model import getPlayer, Player

from google.appengine.ext import db

from score.reviewconflict import ReviewConflict

MAX_AS3_UINT_VALUE = 4294967295;

UPDATE_DELTA_MILISECOND = 31 # update rate on flash player
PAUSE_MULTIPLIER = 1.5 # quantity of pause allowed
MINIMUM_TIME = 10 # margin in seconds to send the data across

def _getPlayerFromId(playerId):
    player = getPlayer(playerId)
    if player is None:
        raise Exception('Player %s could not be fetched' % playerId)
    return player

def start(playerId):
    # TODO : investigate what if user wait for a particular seed (that it trained with)
    # solution : start should be followed by setScore most of the time and for low score, the seed is not regenerated (or loop through a finite set of seed) within the time limit required to have significant highscore?
    # TODO : investigate what if user wait for a seed that has already a high score from another player?
    # solution :: block highest score seeds
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
    #    raise Exception("player would not had enough time to play such score")

    #maxScoreTime = minScoreTime * PAUSE_MULTIPLIER + datetime.timedelta(seconds=MINIMUM_TIME)
    #if player.seedDate + maxScoreTime < datetime.datetime.now():
    #    raise Exception("player has spend too much time to play such score")

    # TODO : investigate: should we consider the player as cheater for this two exception above ?



    # TODO : fetch potential reviewers :
    # - cheaters should be excluded
    # players having already reviewed and played should be prioritised
    # players playing frequently should also be prioritised if we limit the number of potential reviewers
    # of course the reviewer should not be the player itself
    # if friend's information is available, might not want player to review their friends ?
    # new players should be anti-prioritised (might be not necessary if other stuff are done)
    reviewers = []

    createScore(player, score['score'], score['actions'], score['numUpdates'], player.seed, reviewers)

    player.seed = None
    player.seedDate = None
    player.put()


def getRandomScore(playerId):
    player = _getPlayerFromId(playerId)

    scoreReviewKey = Player.currentScoreReviewKey.get_value_for_datastore(player)

    if scoreReviewKey is None:
        # TODO : if player is considered cheater, should we give him/her some reviews?
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
        # TODO :nothing to review (should throw Exception) and potentially consider the player as cheater
        return
    scoreKey = scoreReviewKey.parent()
    score = Score.get(scoreKey)

    # if score is None (and we implemented score as reference stored in Player it probably means score has changed in the mean time (approved for example)
    if score is None:
        # too late
        player.currentScoreReviewKey = None
        return;

    if score.value == scoreValue:
        # delete the score (unverified) and reset a verfiedscore
        setScoreVerified(score)
        #delete conflicts and set conflicting reviewers as cheater
        conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :review", review=scoreReviewKey).fetch(5) # shoud not be more than 2
        for conflict in conflicts:
            if ReviewConflict.player.get_value_for_datastore(conflict) == player.key():
                raise Exception("this player has been able to review two times the same score!")
            if conflict.scoreValue != scoreValue:
                conflict.player.numCheat+=1
                conflict.player.put()
                conflict.delete()
        db.delete(scoreReviewKey)
        player.currentScoreReviewKey = None
        player.put()
        #TODO : deal with no more existing review and conflicts when reviewScore is called after getRandomScore was already called with the review being deleted (?)
    else:
        #check whether a conflict exist with the same score value, if that is the case, player has cheated
        conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :review", review=scoreReviewKey).fetch(5) # should not be more than 2
        for conflict in conflicts:
            if ReviewConflict.player.get_value_for_datastore(conflict) == player.key():
                raise Exception("this player has been able to review two times the same score!") # TODO : set reviewer as cheater (but this should not happen)
            if conflict.scoreValue == scoreValue:
                #player is a cheater
                reviewedPlayer = score.parent()
                reviewedPlayer.numCheat+=1
                reviewedPlayer.put()

                #remove stuffs and assign cheater status to reviewer
                for conflict in conflicts:
                    if conflict.scoreValue != scoreValue:
                        conflict.player.numCheat+=1
                        conflict.player.put()
                        conflict.delete()
                db.delete(scoreReviewKey)
                player.currentScoreReviewKey = None # TODO : check : does deleting entity set references to None ?
                player.put()
                return
            else:
                #TODO : deal with : if too many different we cannot really deal with them, it should not happen though
                pass
        newConflict = ReviewConflict(player=player,scoreValue=scoreValue, parent=scoreReviewKey)
        newConflict.put()
        # TODO : remove reviewer from ScoreReview.potentialReviewers ( costly but necessary ? need to do that only if the ScoreReview need to be kept (conflict present)

