from service.utils import getServices
from pyamf.remoting.gateway import UnknownServiceMethodError

from player.session import getPlayerSession, deletePlayerSession

import simplejson as json

from crypto.signature import verifySignature, base64_url_decode, decode_signedRequest

from error import getErrorResponse, INVALID_SESSION_TOKEN_ERROR, INVALID_SIGNATURE_ERROR, NO_ACTIVE_SESSION_ERROR, SESSION_EXPIRED_ERROR, SIGNED_REQUEST_METHOD_ERROR, TOKEN_METHOD_ERROR, UNKNOW_SERVICE_CALL_ERROR

securedMethods = getServices(["score.service"])


def _getMethodFromName(methodName):
    if securedMethods.has_key(methodName):
        return securedMethods[methodName]
    return None

def sessionTokenCall(sessionToken, playerId, methodName, *args):
    playerSession = getPlayerSession(playerId)

    if playerSession is None:
        return getErrorResponse(NO_ACTIVE_SESSION_ERROR)

    if playerSession.method != 'token' or playerSession.token is None:
        return getErrorResponse(TOKEN_METHOD_ERROR);

    if sessionToken == playerSession.token:
        if playerSession.isExpired():
            deletePlayerSession(playerId)
            return getErrorResponse(SESSION_EXPIRED_ERROR)

        method = _getMethodFromName(methodName)
        if method:
            if args is None or len(args) == 0:
                return method(playerId)
            else:
                return method(playerId, *args)

        else:
            return getErrorResponse(UNKNOW_SERVICE_CALL_ERROR)
    else:
        return getErrorResponse(INVALID_SESSION_TOKEN_ERROR)

def signedRequestCall(signedRequest):

    signature, payload = decode_signedRequest(signedRequest)
    data = json.loads(base64_url_decode(payload))

    playerId = data['playerId']
    methodName = data['methodName']
    if 'args' in data:
        args = data['args']
    else:
        args = None

    playerSession = getPlayerSession(playerId)

    if playerSession is None:
        return getErrorResponse(NO_ACTIVE_SESSION_ERROR)

    if playerSession.method != 'signedRequest' or playerSession.secret is None:
        return getErrorResponse(SIGNED_REQUEST_METHOD_ERROR)

    verified = verifySignature(signature, payload, playerSession.secret, 'SHA1') # TODO decide which algorithm to use (haxe need to support SHA256

    if not verified:
        return getErrorResponse(INVALID_SIGNATURE_ERROR)

    if playerSession.isExpired():
        deletePlayerSession(playerId)
        return getErrorResponse(SESSION_EXPIRED_ERROR)

    method = _getMethodFromName(methodName)
    if method:
        if args is None or len(args) == 0:
            return method(playerId)
        else:
            return method(playerId, *args)
    else:
        return getErrorResponse(UNKNOW_SERVICE_CALL_ERROR)

