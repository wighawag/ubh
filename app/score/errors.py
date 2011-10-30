CHEATER_BLOCKED = {'code': 3002, 'message' : 'You already tried to cheat, you are not trusted anymore'}
SCORE_TOO_SMALL = {'code': 3001, 'message': "should not reach here except you are trying to post a smaller score (maybe to hide an earlier cheat)"}
TOO_MANY_REVIEWS = {'code': 2, 'message': 'You already posted enough reviews, retry later'}
NO_PLAYER_SESSION = {'code' : 1001, 'message' : "No play session started. start need to be called before setScore"}
NOT_ENOUGH_TIME =  {'code' : 2001, 'message' : "you would not had enough time to play such score"}
TOO_MUCH_TIME =  {'code' : 2002, 'message' : "you have spend too much time to play such score"}
TRANSACTION_FAILURE = {'code': 1, 'message': 'transaction failure, try again'}
NOTHING_TO_REVIEW = {'code':300 , 'message' : 'Nothing to review for now'}
ADMIN_ONLY = {'code':4001 , 'message' : 'Only admin are allowed here'}

def getErrorResponse(error, retry = -1):
    return {'success' : False, 'error': error['code'], 'message' : error['message'], 'retry': retry}