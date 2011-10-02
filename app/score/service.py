#######################################
## Test purpose #######################
#######################################
from score.review import ScoreReview
from google.appengine.api.datastore_types import Key
def echo(playerId, data):
    return "player " + playerId + " : " + data

#######################################
#######################################
#######################################

import random
import datetime
from score.model import Score
from player.model import PlaySession, PendingScore, Record, ReviewSession

from google.appengine.ext import db

from score.reviewconflict import ReviewConflict

MAX_AS3_UINT_VALUE = 4294967295;

UPDATE_DELTA_MILISECOND = 31 # update rate on flash player
PAUSE_MULTIPLIER = 1.5 # quantity of pause allowed
MINIMUM_TIME = 10 # margin in seconds to send the data across


def start(playerId):

    def _start():
        # TODO : investigate what if user wait for a particular seed (that it trained with)
        # solution : start should be followed by setScore most of the time and for low score, the seed is not regenerated (or loop through a finite set of seed) within the time limit required to have significant highscore?
        # TODO : investigate what if user wait for a seed that has already a high score from another player?
        # solution :: block highest score seeds

        playSession = PlaySession.get_by_key_name('playSession', parent=Key.from_path('Player', playerId))
        playSession.seed = random.randint(1, MAX_AS3_UINT_VALUE)
        playSession.seedDateTime = datetime.datetime.now()
        playSession.put() # TODO : transaction and/or isolation : player might have been changed in the mean time
        return playSession.seed

    return db.run_in_transaction(_start) # Should not be needed since start and setScore should never be called at the same time an they are the only one who modify playSession

def setScore(playerId, score):

    playerKey = Key.from_path('Player', playerId)

    playSession = PlaySession.get_by_key_name('playSession', parent=playerKey)
    if playSession.seed is None:
        raise Exception("Seed not set while trying to set a new score. start need to be called before setScore")

    seed = playSession.seed

    # RENABLE THIS CHECKS + ALLOW TESTS TO DEAL WITH TIME

    #minScoreTime = datetime.timedelta(milliseconds=(score['numUpdates'] * UPDATE_DELTA_MILISECOND))
    #if player.seedDate + minScoreTime > datetime.datetime.now():
    #    raise Exception("player would not had enough time to play such score")

    #maxScoreTime = minScoreTime * PAUSE_MULTIPLIER + datetime.timedelta(seconds=MINIMUM_TIME)
    #if player.seedDate + maxScoreTime < datetime.datetime.now():
    #    raise Exception("player has spend too much time to play such score")

    # TODO : investigate: should we consider the player as cheater for this two exception above ?


    playSession.seed = None
    playSession.seedDate = None
    playSession.put()


    value = score['score']
    actions = score['actions']
    numUpdates = score['numUpdates']


    # TODO : fetch potential reviewers :
    # - cheaters should be excluded
    # players having already reviewed and played should be prioritised
    # players playing frequently should also be prioritised if we limit the number of potential reviewers
    # of course the reviewer should not be the player itself
    # if friend's information is available, might not want player to review their friends ?
    # new players should be anti-prioritised (might be not necessary if other stuff are done)
    reviewers = []

    # TODO : transaction  ?


    verifiedScore = Score.get_by_key_name("verified", parent=playerKey)

    if verifiedScore is None or value > verifiedScore.value:
        pendingScore = PendingScore.get_by_key_name("pendingScore", parent=playerKey)
        if pendingScore is not None:
            nonVerifiedScore = pendingScore.nonVerified
        else:
            nonVerifiedScore = None

        if nonVerifiedScore is None or value > nonVerifiedScore.value:
            nonVerifiedScore = Score(value=value,actions=actions,numUpdates=numUpdates,seed=seed, parent=playerKey)
            nonVerifiedScore.put()
            if pendingScore is None:
                pendingScore = PendingScore(key_name='pendingScore', parent=playerKey)
            if pendingScore.nonVerified is not None:
                pendingScore.nonVerified.delete() # TODO : delete reviews and conflicts as well!
            pendingScore.nonVerified = nonVerifiedScore
            pendingScore.put() # TODO : transaction and/or isolation : player might have been changed in the mean time

            scoreReview = ScoreReview(key_name="review",parent=nonVerifiedScore, potentialReviewers=reviewers)
            scoreReview.put();
            return nonVerifiedScore
        else:
            pass # TODO : are you trying to cheat?
    else:
        pass # TODO : are you trying to cheat?

    return None


def getRandomScore(playerId):

    playerKey = Key.from_path('Player', playerId)
    playerRecord = Record.get_by_key_name('record', parent=playerKey)

    if playerRecord.numCheat > 0:
        # this could happen even if reviewer has been  assigned a review since at that time it was maybe not considered a cheater
        return {} # TODO : if player is considered cheater, should we give him/her some reviews?


    reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
    scoreReviewKey = ReviewSession.currentScoreReviewKey.get_value_for_datastore(reviewSession)

    if scoreReviewKey is None:
        scoreReviewKey = db.GqlQuery("SELECT __key__ FROM ScoreReview WHERE potentialReviewers = :playerId", playerId=playerId).get()
        if scoreReviewKey is None:
            return {}
        reviewSession.currentScoreReviewKey = scoreReviewKey # TODO : transaction and/or isolation : player might have been changed in the mean time
        reviewSession.put()

    score = db.get(scoreReviewKey.parent())
    # in case score has been approved just now, it could have been removed
    if score is not None:
        return {'score' : score.value, 'actions' : score.actions, 'numUpdates' : score.numUpdates, 'seed' : score.seed}

    return {}

def reviewScore(playerId, scoreValue):
    playerKey = Key.from_path('Player', playerId)
    reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
    scoreReviewKey = ReviewSession.currentScoreReviewKey.get_value_for_datastore(reviewSession)

    if scoreReviewKey is None:
        # TODO :nothing to review (should throw Exception) and potentially consider the player as cheater
        return

    # We are done with it
    reviewSession.currentScoreReviewKey = None # TODO : transaction and/or isolation : player might have been changed in the mean time
    reviewSession.put()

    # The above could have potentially be put in a transaction but since there is only one player concerned, it should not matter


    scoreKey = scoreReviewKey.parent()

    cheaters = db.run_in_transaction(_checkConflicts, scoreKey, scoreValue, scoreReviewKey, playerKey)

    if cheaters:
        def cheaterUpdate(cheaterKey):
            cheaterRecord = Record.get_by_key_name('record', parent=cheaterKey)
            cheaterRecord.numCheat+=1
            cheaterRecord.put()

        for cheaterKey in cheaters:
            db.run_in_transaction(cheaterUpdate,cheaterKey)



def _checkConflicts(scoreKey, scoreValue, scoreReviewKey, playerKey):
    score = Score.get(scoreKey)

    # if score is None (and we implemented score as reference stored in Player it probably means score has changed in the mean time (approved for example)
    if score is None:
        # too late
        return [];

    cheaters = []
    conflictResolved = False
    if score.value == scoreValue:
        # delete the score (unverified) and reset a verfiedscore
        reviewedPlayerKey = scoreKey.parent()
        verifiedScore = Score(key_name="verified", parent=reviewedPlayerKey, value=score.value, actions=score.actions, numUpdates=score.numUpdates, seed=score.seed)
        verifiedScore.put()
        score.delete()
        db.delete(Key.from_path('PendingScore', 'pendingScore', parent = reviewedPlayerKey))
        #delete conflicts and set conflicting reviewers as cheater
        conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :review", review=scoreReviewKey).fetch(5) # shoud not be more than 2
        for conflict in conflicts:
            if ReviewConflict.player.get_value_for_datastore(conflict) == playerKey:
                raise Exception("this player has been able to review two times the same score!")
            if conflict.scoreValue != scoreValue:
                cheaters.append(ReviewConflict.player.get_value_for_datastore(conflict))
                conflict.delete()
        db.delete(scoreReviewKey)
        conflictResolved = True
        #TODO : deal with no more existing review and conflicts when reviewScore is called after getRandomScore was already called with the review being deleted (?)
    else:
        #check whether a conflict exist with the same score value, if that is the case, player has cheated
        conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :review", review=scoreReviewKey).fetch(100) # should not be more than 3
        for conflict in conflicts:
            if ReviewConflict.player.get_value_for_datastore(conflict) == playerKey:
                raise Exception("this player has been able to review two times the same score!") # TODO : set reviewer as cheater (but this should not happen)
            if conflict.scoreValue == scoreValue:
                #player is a cheater
                reviewedPlayerKey = scoreKey.parent()
                reviewedPlayerRecord = Record.get_by_key_name('record', parent=reviewedPlayerKey)
                reviewedPlayerRecord.numCheat+=1
                reviewedPlayerRecord.put()

                #remove stuffs and assign cheater status to reviewer
                for conflict in conflicts:
                    if conflict.scoreValue != scoreValue:
                        cheaters.append(ReviewConflict.player.get_value_for_datastore(conflict))
                        conflict.delete()
                score.delete()
                db.delete(Key.from_path('PendingScore', 'pendingScore', parent = reviewedPlayerKey))
                db.delete(scoreReviewKey)
                conflictResolved = True
                break
            else:
                #TODO : deal with : if too many different we cannot really deal with them, it should not happen though
                pass
        if not conflictResolved:
            newConflict = ReviewConflict(player=playerKey,scoreValue=scoreValue, parent=scoreReviewKey)
            newConflict.put()

        # TODO : remove reviewer from ScoreReview.potentialReviewers ( costly but necessary ? need to do that only if the ScoreReview need to be kept (conflict present)

    return cheaters
