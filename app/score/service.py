#######################################
## Test purpose #######################
#######################################
from admin.model import getAdmin
def echo(playerId, data):
    return {'result' : str(playerId) + ":" + data }
#######################################
#######################################
#######################################

from google.appengine.api.datastore_errors import TransactionFailedError
from error import getErrorResponse, TOO_MANY_REVIEWS, NOTHING_TO_REVIEW, CHEATER_BLOCKED, SCORE_TOO_SMALL, NO_PLAYER_SESSION, NOT_ENOUGH_TIME, TOO_MUCH_TIME, TRANSACTION_FAILURE,\
    ADMIN_ONLY

import random
import datetime

from google.appengine.api.datastore_types import Key

from score.model import VerifiedScore, NonVerifiedScore
from player.model import PlaySession, PendingScore, Record, ReviewSession,\
    ApproveSession, VerifiedScoreWrapper

from google.appengine.ext import db

from score.reviewconflict import ReviewConflict

from stats.model import getReviewTimeUnit

from math import ceil

import struct

import config


MAX_AS3_UINT_VALUE = 4294967295;

MINIMUM_TIME = 10000 # margin in seconds to send the data across

def start(playerId):

    def _start():
        playerKey = Key.from_path('Player', playerId)

        rand = random.SystemRandom()
        seed = struct.pack("4L", rand.randint(1, MAX_AS3_UINT_VALUE), rand.randint(1, MAX_AS3_UINT_VALUE), rand.randint(1, MAX_AS3_UINT_VALUE), rand.randint(1, MAX_AS3_UINT_VALUE))

        playSession = PlaySession(key_name='playSession', seed=seed, version=config.currentGameMechanicVersion, seedDateTime=datetime.datetime.now(), parent=playerKey)
        playSession.put()

        today = datetime.date.today()
        playerRecord = Record.get_by_key_name('record', parent=playerKey)
        if playerRecord.lastDayPlayed != today:
            playerRecord.numDaysPlayed += 1
            playerRecord.lastDayPlayed = today
            playerRecord.put()

        seedList = struct.unpack("4L", playSession.seed)
        return {'result' : { 'seed' : seedList, 'version': playSession.version } }

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
    version = playSession.version
    seedDateTime = playSession.seedDateTime

    now = datetime.datetime.now()

    # TODO : investigate: should we consider the player as cheater for this two exception  ?
    if seedDateTime + datetime.timedelta(milliseconds=scoreTime) > now:
        return getErrorResponse(NOT_ENOUGH_TIME)

    maxScoreTime = scoreTime + MINIMUM_TIME
    if seedDateTime + datetime.timedelta(milliseconds=maxScoreTime) < now:
        return getErrorResponse(TOO_MUCH_TIME)


    def _setScore():
        playSession.delete()

        verifiedScore = None
        verifiedScoreWrapper = VerifiedScoreWrapper.get_by_key_name("verifiedScore", parent=playerKey)
        if verifiedScoreWrapper is not None:
            verifiedScore = verifiedScoreWrapper.verified

        if verifiedScore is None or scoreValue > verifiedScore.value:
            pendingScore = PendingScore.get_by_key_name("pendingScore", parent=playerKey)
            if pendingScore is not None:
                nonVerifiedScore = pendingScore.nonVerified
            else:
                nonVerifiedScore = None

            if nonVerifiedScore is None or scoreValue > nonVerifiedScore.value:

                try:
                    proofBlob = db.Blob(proof)
                except Exception:
                    proofText = str(proof)
                    proofBlob = db.Blob(proofText)

                nonVerifiedScore = NonVerifiedScore(value=scoreValue,time=scoreTime,proof=proofBlob,seed=seed,version=version, parent=playerKey)
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

                return {'result' : {'message' : 'success'} }
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


    def _updateLastReviewAttemptDateTime():
        playerRecord = Record.get_by_key_name('record', parent=playerKey)

        if playerRecord.lastReviewAttemptDateTime is not None and playerRecord.lastReviewAttemptDateTime > oldEnoughTime:
            # TODO : check whethe rthis randomize stuff is good or not:
            return getErrorResponse(TOO_MANY_REVIEWS, 2000 + random.random() * 5000  + ceil(reviewTimeUnitMilliseconds * (1 + random.random() * 2)))
            # could be 2 * reviewTimeUnit / config.nbPlayerPerTimeUnit

        playerRecord.lastReviewAttemptDateTime = datetime.datetime.now()
        playerRecord.put()
        return None

    reviewSession = ReviewSession.get_by_key_name('reviewSession', parent=playerKey)
    if reviewSession is None:

        try:
            result = db.run_in_transaction(_updateLastReviewAttemptDateTime)
        except TransactionFailedError:
            result = getErrorResponse(TRANSACTION_FAILURE, 0)

        if result is not None:
            return result

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
            return {'result' : {'message' : 'Nothing to review for now'} }


        reviewSession = ReviewSession(key_name='reviewSession', currentScoreToReview=scoreToReview, parent=playerKey)
        reviewSession.put()
    else:
        scoreToReview = reviewSession.currentScoreToReview

    # in case score has been approved just now, it could have been removed
    if scoreToReview is not None:
        seedList = struct.unpack("4L", scoreToReview.seed)
        return {'result' : { 'proof' : scoreToReview.proof, 'seed' : seedList, 'version' : scoreToReview.version} }

    return {'result' : {'message' : 'Nothing to review for now'} }


def reviewScore(playerId, score, adminMode=False):

    if adminMode:
        admin = getAdmin()
        try:
            admin.playerList.index(playerId)
        except ValueError:
            return getErrorResponse(ADMIN_ONLY)

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
        playerRecord.put()
    db.run_in_transaction(_increaseNumScoreReviewed)

    try:
        cheaters = db.run_in_transaction(_checkConflicts, scoreToReviewKey, scoreValue, scoreTime, playerId, adminMode)
    except TransactionFailedError:
        return getErrorResponse(TRANSACTION_FAILURE, 0)

    if cheaters:
        def _cheaterUpdate(cheaterKey):
            cheaterRecord = Record.get_by_key_name('record', parent=cheaterKey)
            cheaterRecord.numCheat+=1
            cheaterRecord.put()

        for cheaterKey in cheaters:
            db.run_in_transaction(_cheaterUpdate,cheaterKey)

    return {'result' : {'message' : 'review submited'} }

def _checkConflicts(scoreToReviewKey, scoreValue, scoreTime, playerId, adminMode):
    playerKey = Key.from_path('Player', playerId)

    scoreToReview = db.get(scoreToReviewKey)
    if scoreToReview is None:
        return []

    cheaters = []
    conflictResolved = False
    if scoreToReview.value == scoreValue and scoreToReview.time == scoreTime:
        # delete the score (unverified) and reset a verifiedScore
        reviewedPlayerKey = scoreToReview.parent_key()
        verifiedScore = VerifiedScore(parent=reviewedPlayerKey, value=scoreToReview.value, proof=scoreToReview.proof, time=scoreToReview.time, seed=scoreToReview.seed, version=scoreToReview.version, conflictingReviewers=scoreToReview.conflictingReviewers, verifier=playerId, approvedByAdmin=adminMode)
        verifiedScore.put()
        verifiedScoreWrapper = VerifiedScoreWrapper.get_by_key_name("verifiedScore", parent=reviewedPlayerKey)
        if verifiedScoreWrapper is None:
            verifiedScoreWrapper = VerifiedScoreWrapper(key_name='verifiedScore', parent=reviewedPlayerKey, verified=verifiedScore)
        else:
            verifiedScoreWrapper.verified.delete()
            verifiedScoreWrapper.verified = verifiedScore
        verifiedScoreWrapper.put()
        reviewedPlayerRecord = Record.get_by_key_name('record', parent=reviewedPlayerKey)
        reviewedPlayerRecord.numScoreVerified += 1
        reviewedPlayerRecord.put()
        db.delete(Key.from_path('PendingScore', 'pendingScore', parent = reviewedPlayerKey))
        #delete conflicts and set conflicting reviewers as cheater
        conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :score", score=scoreToReview).fetch(100) # shoud not be more than 2
        for conflict in conflicts:
            if ReviewConflict.player.get_value_for_datastore(conflict) == playerKey and not adminMode:
                pass #TODO : raise Exception("this player has been able to review two times the same score!")
            if conflict.scoreValue != scoreValue or conflict.scoreTime != scoreTime:
                cheaters.append(ReviewConflict.player.get_value_for_datastore(conflict))
            conflict.delete()
        scoreToReview.delete()
        conflictResolved = True
    else:
        #check whether a conflict exist with the same score value, if that is the case, player has cheated
        conflicts = ReviewConflict.gql("WHERE ANCESTOR IS :score", score=scoreToReview).fetch(100) # should not be more than 3

        if adminMode:
            conflictResolved = True # player is cheater no need to check anything else
        else:
            for conflict in conflicts:
                if ReviewConflict.player.get_value_for_datastore(conflict) == playerKey:
                    pass #TODO : raise Exception("this player has been able to review two times the same score!")
                elif conflict.scoreValue == scoreValue and conflict.scoreTime == scoreTime:
                    conflictResolved = True
                    break

        #player is a cheater
        if conflictResolved:
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

        else:
            scoreToReview.conflictingReviewers.append(playerId)
            scoreToReview.put()
            newConflict = ReviewConflict(player=playerKey,scoreValue=scoreValue,scoreTime=scoreTime, parent=scoreToReview)
            newConflict.put()


    return cheaters

def getHighestNonApprovedScore(playerId):
    admin = getAdmin()
    try:
        admin.playerList.index(playerId)
    except ValueError:
        return getErrorResponse(ADMIN_ONLY)


    scoreToApprove = db.GqlQuery("SELECT FROM VerifiedScore WHERE approvedByAdmin = False ORDER BY value DESC").get()

    if scoreToApprove is not None:
        playerKey = Key.from_path('Player', playerId)
        approveSession = ApproveSession(key_name='approveSession', currentScoreToApprove=scoreToApprove, parent=playerKey)
        approveSession.put()

        seedList = struct.unpack("4L", scoreToApprove.seed)
        return {'result' : { 'proof' : scoreToApprove.proof, 'seed' : seedList} }


    return {'result' : { 'message' : 'Nothing to approve for now'} }

def approveScore(playerId, score):
    admin = getAdmin()
    try:
        admin.playerList.index(playerId)
    except ValueError:
        return getErrorResponse(ADMIN_ONLY)

    scoreValue = score['score']
    scoreTime = score['time']
    playerKey = Key.from_path('Player', playerId)
    approveSession = ApproveSession.get_by_key_name('approveSession', parent=playerKey)

    if approveSession is None:
        return getErrorResponse(NOTHING_TO_REVIEW)

    scoreToApproveKey = ApproveSession.currentScoreToApprove.get_value_for_datastore(approveSession)
    # We are done with it
    approveSession.delete()

    def _approveScore():
        scoreToApprove = db.get(scoreToApproveKey)
        if scoreToApprove is None:
            return {'cheater' : None, 'nonCheaters': []}

        approvedPlayerKey = scoreToApprove.parent_key()

        cheater = None
        nonCheaters = []
        if scoreToApprove.value == scoreValue and scoreToApprove.time == scoreTime:
            scoreToApprove.approvedByAdmin = True
            scoreToApprove.put()
        else:
            approvedPlayerRecord = Record.get_by_key_name('record', parent=approvedPlayerKey)
            approvedPlayerRecord.numCheat += 1
            approvedPlayerRecord.put()
            cheater = Key.from_path('Player', scoreToApprove.verifier)
            for nonCheaterId in scoreToApprove.conflictingReviewers:
                nonCheaters.append(Key.from_path('Player', nonCheaterId))
            scoreToApprove.delete()
            db.delete(Key.from_path('VerifiedScoreWrapper', 'verifiedScore', parent = approvedPlayerKey))

        return {'cheater' : cheater, 'nonCheaters': nonCheaters}

    try:
        result = db.run_in_transaction(_approveScore)
    except TransactionFailedError:
        return getErrorResponse(TRANSACTION_FAILURE, 0)

    cheater = result['cheater']
    nonCheaters = result['nonCheaters']

    if cheater is not None:
        cheaterRecord = Record.get_by_key_name('record', parent=cheater)
        cheaterRecord.numCheat+=1
        cheaterRecord.put()

    if nonCheaters:
        def _nonCheaterUpdate(nonCheaterKey):
            cheaterRecord = Record.get_by_key_name('record', parent=nonCheaterKey)
            cheaterRecord.numCheat-=1
            cheaterRecord.put()

        for nonCheaterKey in nonCheaters:
            db.run_in_transaction(_nonCheaterUpdate,nonCheaterKey)

    return {'result' : { 'message' : 'approvement submited'} }


def getOwnHighScore(playerId):

    def _getOwnHighScore():
        score = None
        playerKey = Key.from_path('Player', playerId)
        bestScore = PendingScore.get_by_key_name("pendingScore", parent=playerKey)
        if bestScore is None:
            bestScore = VerifiedScoreWrapper.get_by_key_name("verifiedScore", parent=playerKey)
            if bestScore is not None:
                score = bestScore.verified
        else:
            score = bestScore.nonVerified

        if score is None:
            return {'result' : { 'message' : 'you have no score yet'} }

        return {'result' : { 'score' : score.value, 'time' : score.time} }

    try:
        return db.run_in_transaction(_getOwnHighScore)
    except TransactionFailedError:
        return getErrorResponse(TRANSACTION_FAILURE, 0)

