from serviceUtils import getServices
from pyamf.remoting.gateway import UnknownServiceMethodError

from player.session import getPlayerSession, deletePlayerSession

securedMethods = getServices(["score.service"])


class InvalidSessionError(Exception):
    pass

class NoActiveSessionError(Exception):
    pass


class SessionExpiredError(Exception):
    pass

def _getMethodFromName(methodName):
    if securedMethods.has_key(methodName):
        return securedMethods[methodName]
    return None
    
def sessionTokenCall(sessionToken, playerId, methodName, *args):
    playerSession = getPlayerSession(playerId)
    
    if playerSession is None:
        raise NoActiveSessionError("No Session Active for player: " + playerId) # session error
      
    if sessionToken == playerSession.token:
        if playerSession.isExpired():
            deletePlayerSession(playerId)
            raise SessionExpiredError("Session Expired")
        
        method = _getMethodFromName(methodName)
        if method:
            return method(playerId, *args)
        else:
            raise UnknownServiceMethodError(
                "Unknown method %s" % str(methodName))
    else:
        raise InvalidSessionError("Invalid Session Token") # session error
