from google.appengine.ext import db
from google.appengine.api import memcache

class Stats(db.Model):
    reviewTimeUnit = db.IntegerProperty(required=True) #milliseconds
    reviewTimeUnitWeight = db.IntegerProperty(default=1)


def setDefaultStats():
    stats = getStats()
    stats.reviewTimeUnit = 30 * 24 * 3600 * 1000
    stats.reviewTimeUnitWeight = 0
    setStats(stats)
    return stats

def createStats():
    stats = Stats(key_name='stats', reviewTimeUnit = 30 * 24 * 3600 * 1000)

    stats.put()
    protobuf = db.model_to_protobuf(stats)
    memcache.set('stats', protobuf)
    return stats

def getStats():
    protobuf = memcache.get('stats')

    if protobuf is not None:
        return db.model_from_protobuf(protobuf)
    else:
        stats = Stats.get_by_key_name('stats')
        if stats is not None:
            protobuf = db.model_to_protobuf(stats)
            memcache.set('stats', protobuf)
            return stats
    return createStats()

def setStats(stats):
    stats.put()
    protobuf = db.model_to_protobuf(stats)
    memcache.set('stats', protobuf)

def getReviewTimeUnit():
    stats = getStats()
    return stats.reviewTimeUnit

def setReviewTimeUnit(value):
    stats = getStats()
    stats.reviewTimeUnit = value
    setStats(stats)
