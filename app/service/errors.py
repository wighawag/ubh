NO_ACTIVE_SESSION_ERROR = {'code': 6001, 'message' : 'You do not have any active session'}
TOKEN_METHOD_ERROR = {'code':6002, 'message' : "the session was not initialized with token method "}
SIGNED_REQUEST_METHOD_ERROR = {'code':6003, 'message' : "the session was not initialized with signedRequest method "}
SESSION_EXPIRED_ERROR = {'code':6004, 'message':"Session Expired"}
UNKNOW_SERVICE_CALL_ERROR = {'code':6005, 'message':"Unknown method call"}
INVALID_SESSION_TOKEN_ERROR = {'code':6006, 'message' : "Invalid session token"}
INVALID_SIGNATURE_ERROR = {'code' : 6007, 'message':'Invalid Signature'}

def getErrorResponse(error, retry = -1):
    return {'success' : False, 'error': error['code'], 'message' : error['message'], 'retry': retry}