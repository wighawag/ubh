#######################################
## Test purpose #######################
#######################################
def echo(playerId, data):
    return "player " + playerId + " : " + data
#######################################
#######################################
#######################################

from google.appengine.api.datastore_errors import TransactionFailedError
from score.errors import getErrorResponse, TOO_MANY_REVIEWS, NOTHING_TO_REVIEW, CHEATER_BLOCKED, SCORE_TOO_SMALL, NO_PLAYER_SESSION, NOT_ENOUGH_TIME, TOO_MUCH_TIME, TRANSACTION_FAILURE

import random
import datetime

from google.appengine.api.datastore_types import Key

from score.model import VerifiedScore, NonVerifiedScore
from player.model import PlaySession, PendingScore, Record, ReviewSession

from google.appengine.ext import db

from score.reviewconflict import ReviewConflict

from stats.model import getReviewTimeUnit

from math import ceil


MAX_AS3_UINT_VALUE = 4294967295;

MINIMUM_TIME = 10 # margin in seconds to send the data across

def start(playerId):

    def _start():
        # TODO : investigate what if user wait for a particular seed (that it trained with)
        # solution : start should be followed by setScore most of the time and for low score, the seed is not regenerated (or loop through a finite set of seed) within the time limit required to have significant highscore?
        # TODO : investigate what if user wait for a seed that has already a high score from another player?
        # solution :: block highest score seeds

        playerKey = Key.from_path('Player', playerId)

        playSession = PlaySession(key_name='playSession', seed=random.randint(1, MAX_AS3_UINT_VALUE), seedDateTime=datetime.datetime.now(), parent=playerKey)
        playSession.put()

        today = datetime.date.today()
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        if playerRecord.lastDayPlayed != today:
            playerRecord.numDaysPlayed += 1
            playerRecord.lastDayPlayed = today
            playerRecord.put()

        return {'success' : True, 'seed' : playSession.seed}

    try:
        return db.run_in_transaction(_start)
    except TransactionFailedError:
        return getErrorResponse(TRANSACTION_FAILURE, 0)

def setScore(playerId, score):

    scoreValue = score['score']
    scoreTime = score['time']
    proof = score['proof']

    playerKey = Key.from_path('Player', playerId)

    playSession = PlaySession.get_by_key_name('playSession', parent=playerKey)
    if playSession is None:
        return getErrorResponse(NO_PLAYER_SESSION)

    seed = playSession.seed
    seedDateTime = playSession.seedDateTime


    # TODO : investigate: should we consider the player as cheater for this two exception  ?
    if seedDateTime + datetime.timedelta(seconds=scoreTime) > datetime.datetime.now():
        return getErrorResponse(NOT_ENOUGH_TIME)

    maxScoreTime = scoreTime + MINIMUM_TIME
    if seedDateTime + datetime.timedelta(seconds=maxScoreTime) < datetime.datetime.now():
        return getErrorResponse(TOO_MUCH_TIME)


    def _setScore():
        playSession.delete()
        verifiedScore = VerifiedScore.get_by_key_name("verified", parent=playerKey)

        if verifiedScore is None or scoreValue > verifiedScore.value:
            pendingScore = PendingScore.get_by_key_name("pendingScore", parent=playerKey)
            if pendingScore is not None:
                nonVerifiedScore = pendingScore.nonVerified
            else:
                nonVerifiedScore = None

            if nonVerifiedScore is None or scoreValue > nonVerifiedScore.value:
                nonVerifiedScore = NonVerifiedScore(value=scoreValue,time=scoreTime,proof=proof,seed=seed, parent=playerKey)
                nonVerifiedScore.put()
                if pendingScore is None:
                    pendingScore = PendingScore(key_name='pendingScore', parent=playerKey, nonVerified=nonVerifiedScore)
                else:
                    conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :score", score=pendingScore.nonVerified.key()).fetch(100) # shoud not be more than 2
                    for conflict in conflicts:
                        conflict.delete()
                    pendingScore.nonVerified.delete()
                    pendingScore.nonVerified = nonVerifiedScore
                pendingScore.put()

                return {'success' : True}
            else:
                pass # TODO : are you trying to cheat?
        else:
            pass # TODO : are you trying to cheat?

        return getErrorResponse(SCORE_TOO_SMALL)

    try:
        return db.run_in_transaction(_setScore)
    except TransactionFailedError:
        return getErrorResponse(TRANSACTION_FAILURE, 0)


def getRandomScore(playerId):

    playerKey = Key.from_path('Player', playerId)
    playerRecord = Record.get_by_key_name('record', parent=playerKey)

    # do not review if you are a cheater
    if playerRecord.numCheat > 0:
        return getErrorResponse(CHEATER_BLOCKED)

    reviewTimeUnitMilliseconds = getReviewTimeUnit()
    reviewTimeUnit = datetime.timedelta(milliseconds=reviewTimeUnitMilliseconds)
    now =datetime.datetime.now()
    oldEnoughTime = now - reviewTimeUnit

    if playerRecord.lastReviewDateTime is not None and playerRecord.lastReviewDateTime > oldEnoughTime:
        # TODO : check whethe rthis randomize stuff is good or not:
        return getErrorResponse(TOO_MANY_REVIEWS, 2000 + random.random() * 5000  + ceil(reviewTimeUnitMilliseconds * (1 + random.random() * 2)))
        # could be 2 * reviewTimeUnit / config.nbPlayerPerTimeUnit

    reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
    if reviewSession is None:
        # do not allow reviewer to jump on a just posted review. basically the reviewer should have lots of potential review to take from and other reviewer shoudl compete with
        potentialScoresToReview = db.GqlQuery("SELECT FROM NonVerifiedScore WHERE dateTime < :oldEnoughTime ORDER BY dateTime ASC", oldEnoughTime=oldEnoughTime).fetch(5)

        scoreToReview = None
        for score in potentialScoresToReview:
            if score.parent_key() != playerKey:
                try:
                    score.conflictingReviewers.index(playerId)
                except ValueError: # the current reviewer did not review this score yet
                    scoreToReview = score
                    break

        if scoreToReview is None:
            return {'success' : True, 'message' : 'Nothing to review for now'}

        reviewSession = ReviewSession(key_name='reviewSession', currentScoreToReview=scoreToReview, parent=playerKey)
        reviewSession.put()
    else:
        scoreToReview = reviewSession.currentScoreToReview

    # in case score has been approved just now, it could have been removed
    if scoreToReview is not None:
        return {'success' : True, 'proof' : scoreToReview.proof, 'seed' : scoreToReview.seed}

    return {'success' : True, 'message' : 'Nothing to review for now'}


def reviewScore(playerId, score):
    scoreValue = score['score']
    scoreTime = score['time']
    playerKey = Key.from_path('Player', playerId)
    reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)

    if reviewSession is None:
        return getErrorResponse(NOTHING_TO_REVIEW)

    scoreToReviewKey = ReviewSession.currentScoreToReview.get_value_for_datastore(reviewSession)
    # We are done with it
    reviewSession.delete()

    # The above could have potentially be put in a transaction but since there is only one player concerned, it should not matter

    def _increaseNumScoreReviewed():
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        playerRecord.numScoreReviewed += 1
        playerRecord.lastReviewDateTime = datetime.datetime.now()
        playerRecord.put()
    db.run_in_transaction(_increaseNumScoreReviewed)

    try:
        cheaters = db.run_in_transaction(_checkConflicts, scoreToReviewKey, scoreValue, scoreTime, playerId)
    except TransactionFailedError:
        return getErrorResponse(TRANSACTION_FAILURE, 0)

    if cheaters:
        def _cheaterUpdate(cheaterKey):
            cheaterRecord = Record.get_by_key_name('record', parent=cheaterKey)
            cheaterRecord.numCheat+=1
            cheaterRecord.put()

        for cheaterKey in cheaters:
            db.run_in_transaction(_cheaterUpdate,cheaterKey)

    return {'success' : True, 'message' : 'review submited'}

def _checkConflicts(scoreToReviewKey, scoreValue, scoreTime, playerId):
    playerKey = Key.from_path('Player', playerId)

    scoreToReview = db.get(scoreToReviewKey)
    if scoreToReview is None:
        return []

    cheaters = []
    conflictResolved = False
    if scoreToReview.value == scoreValue and scoreToReview.time == scoreTime:
        # delete the score (unverified) and reset a verifiedScore
        reviewedPlayerKey = scoreToReview.parent_key()
        verifiedScore = VerifiedScore(key_name="verified", parent=reviewedPlayerKey, value=scoreToReview.value, proof=scoreToReview.proof, time=scoreToReview.time, seed=scoreToReview.seed, conflictingReviewers=scoreToReview.conflictingReviewers, verifier=playerId)
        verifiedScore.put()
        reviewedPlayerRecord = Record.get_by_key_name('record', parent=reviewedPlayerKey)
        reviewedPlayerRecord.numScoreVerified += 1
        reviewedPlayerRecord.put()
        db.delete(Key.from_path('PendingScore', 'pendingScore', parent = reviewedPlayerKey))
        #delete conflicts and set conflicting reviewers as cheater
        conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :score", score=scoreToReview).fetch(100) # shoud not be more than 2
        for conflict in conflicts:
            if ReviewConflict.player.get_value_for_datastore(conflict) == playerKey:
                pass #TODO : raise Exception("this player has been able to review two times the same score!")
            if conflict.scoreValue != scoreValue or conflict.scoreTime != scoreTime:
                cheaters.append(ReviewConflict.player.get_value_for_datastore(conflict))
            conflict.delete()
        scoreToReview.delete()
        conflictResolved = True
    else:
        #check whether a conflict exist with the same score value, if that is the case, player has cheated
        conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :score", score=scoreToReview).fetch(100) # should not be more than 3
        for conflict in conflicts:
            if ReviewConflict.player.get_value_for_datastore(conflict) == playerKey:
                pass #TODO : raise Exception("this player has been able to review two times the same score!")
            elif conflict.scoreValue == scoreValue and conflict.scoreTime == scoreTime:
                #player is a cheater
                reviewedPlayerKey = scoreToReview.parent_key()
                reviewedPlayerRecord = Record.get_by_key_name('record', parent=reviewedPlayerKey)
                reviewedPlayerRecord.numCheat+=1
                reviewedPlayerRecord.put()

                #remove stuffs and assign cheater status to reviewer
                for conflict in conflicts:
                    if conflict.scoreValue != scoreValue or conflict.scoreTime != scoreTime:
                        cheaters.append(ReviewConflict.player.get_value_for_datastore(conflict))
                    conflict.delete()
                scoreToReview.delete()
                db.delete(Key.from_path('PendingScore', 'pendingScore', parent = reviewedPlayerKey))
                conflictResolved = True
                break

        if not conflictResolved:
            scoreToReview.conflictingReviewers.append(playerId)
            scoreToReview.put()
            newConflict = ReviewConflict(player=playerKey,scoreValue=scoreValue,scoreTime=scoreTime, parent=scoreToReview)
            newConflict.put()


    return cheaters
