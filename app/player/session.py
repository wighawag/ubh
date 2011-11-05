from google.appengine.ext import db

from google.appengine.api import memcache

import hashlib
import os

import datetime as datetimeModule

DEFAULT_MAX_SESSION_LIFE_TIME = datetimeModule.timedelta(minutes=30) # need to be regenerated so that the player is able to share its score after 30 minutes while playing

namespace = "PlayerSession"

def createPlayerSession(playerId, method, datetime = None):
    #TODO add signedRequest SECRET to use signedRequestCall instead of sessionTokenCall : str(random.getrandbits(32)) # should be more than 32 (we want 32 charecter, not bit)
    # use token for now
    if datetime is None:
        datetime = datetimeModule.datetime.now()

    if method == 'token':
        session = PlayerSession(key_name=playerId, method=method, token=hashlib.md5(os.urandom(16)).hexdigest(), creationDateTime=datetime)
    elif method == 'signedRequest':
        session = PlayerSession(key_name=playerId, method=method, secret=hashlib.md5(os.urandom(16)).hexdigest(), creationDateTime=datetime)

    session.put()
    protobuf = db.model_to_protobuf(session)
    memcache.set(playerId, protobuf, DEFAULT_MAX_SESSION_LIFE_TIME.seconds, namespace=namespace)
    return session

def deletePlayerSession(playerId):
    db.delete(db.Key.from_path('PlayerSession', playerId))
    memcache.delete(playerId, namespace=namespace)

def getPlayerSession(playerId):
    protobuf = memcache.get(playerId, namespace=namespace)

    if protobuf is not None:
        return db.model_from_protobuf(protobuf)
    else:
        session = PlayerSession.get_by_key_name(playerId)
        if session is not None:
            protobuf = db.model_to_protobuf(session)
            memcache.set(playerId, protobuf, DEFAULT_MAX_SESSION_LIFE_TIME.seconds, namespace=namespace) # TODO : set expiry time depending of creationDateTime
            return session
    return None

# key_name need to be the same as player key_name (could use parent relationship instead ?)
class PlayerSession(db.Model):
    # need to have one token or one secret
    method = db.StringProperty(required = True)
    token = db.StringProperty()
    secret = db.StringProperty()
    creationDateTime = db.DateTimeProperty(auto_now_add=True)

    def isExpired(self):
        now = datetimeModule.datetime.now()
        return (now - self.creationDateTime > DEFAULT_MAX_SESSION_LIFE_TIME)
