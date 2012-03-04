import logging

CHEATER_BLOCKED = {'code': 3002, 'message' : 'You already tried to cheat, you are not trusted anymore'}
SCORE_TOO_SMALL = {'code': 3001, 'message': "should not reach here except you are trying to post a smaller score (maybe to hide an earlier cheat)"}
TOO_MANY_REVIEWS = {'code': 3003, 'message': 'You already posted enough reviews, retry later'}
NO_PLAYER_SESSION = {'code' : 1001, 'message' : "No play session started. start need to be called before setScore"}
NOT_ENOUGH_TIME =  {'code' : 2001, 'message' : "you would not had enough time to play such score"}
TOO_MUCH_TIME =  {'code' : 2002, 'message' : "you have spend too much time to play such score"}
NOTHING_TO_REVIEW = {'code':300 , 'message' : 'Nothing to review (reviewed already)'}
ADMIN_ONLY = {'code':4001 , 'message' : 'Only admin are allowed here'}

START_TRANSACTION_FAILURE = {'code': 1, 'message': 'start transaction failure, try again'}
SETSCORE_TRANSACTION_FAILURE = {'code': 2, 'message': 'setScore transaction failure, try again'}
LASTREVIEWUPDATE_TRANSACTION_FAILURE = {'code': 3, 'message': 'last review date update transaction failure, try again'}
CHECKCONFLICT_TRANSACTION_FAILURE = {'code': 4, 'message': 'check conflicts transaction failure, try again'}
APPROVESCORE_TRANSACTION_FAILURE = {'code': 5, 'message': 'approveScore transaction failure, try again'}
OWNHIGHSCORE_TRANSACTION_FAILURE = {'code': 6, 'message': 'ownHighscore transaction failure, try again'}



NO_ACTIVE_SESSION_ERROR = {'code': 6001, 'message' : 'You do not have any active session'}
TOKEN_METHOD_ERROR = {'code':6002, 'message' : "the session was not initialized with token method "}
SIGNED_REQUEST_METHOD_ERROR = {'code':6003, 'message' : "the session was not initialized with signedRequest method "}
SESSION_EXPIRED_ERROR = {'code':6004, 'message':"Session Expired"}
UNKNOW_SERVICE_CALL_ERROR = {'code':6005, 'message':"Unknown method call"}
INVALID_SESSION_TOKEN_ERROR = {'code':6006, 'message' : "Invalid session token"}
INVALID_SIGNATURE_ERROR = {'code' : 6007, 'message':'Invalid Signature'}

def getErrorResponse(error, retry = -1):
    return {'error' : {'code': error['code'], 'message' : error['message'], 'retry': retry } }


# Decorator :
def logError(function):
    def wrapper(*args, **kwargs):
        result = function(*args, **kwargs)
        if 'error' in result:
            try:
                raise Exception(result['error']['code'], result['error']['message'], result['error']['retry'])
            except (Exception):
                logging.exception('Error ' + str(result['error']['code']))
        return result
    return wrapper
