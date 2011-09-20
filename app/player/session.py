from google.appengine.ext import db

from google.appengine.api import memcache

import hashlib
import os

import datetime

DEFAULT_MAX_SESSION_LIFE_TIME = datetime.timedelta(minutes=30) # need to be regenerated so that the player is able to share its score after 30 minutes while playing

namespace = "PlayerSession"

def createPlayerSession(playerId, datetime=None):
    if datetime is None:
        session = PlayerSession(key_name=playerId, token=hashlib.md5(os.urandom(16)).hexdigest())
    else:
        session = PlayerSession(key_name=playerId, token=hashlib.md5(os.urandom(16)).hexdigest(), creationDateTime=datetime)

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
            memcache.set(playerId, protobuf, DEFAULT_MAX_SESSION_LIFE_TIME.seconds, namespace=namespace)
            return session
    return None

class PlayerSession(db.Model):
    token = db.StringProperty(required=True)
    creationDateTime = db.DateTimeProperty(auto_now_add=True)

    def isExpired(self):
        now = datetime.datetime.now()
        return (now - self.creationDateTime > DEFAULT_MAX_SESSION_LIFE_TIME)
