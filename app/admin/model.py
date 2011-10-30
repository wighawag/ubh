from google.appengine.ext import db
from google.appengine.api import memcache

class Admin(db.Model):
    playerList = db.StringListProperty()

def createAdmin():
    admin = Admin(key_name='admin')

    admin.put()
    protobuf = db.model_to_protobuf(admin)
    memcache.set('admin', protobuf)
    return admin

def getAdmin():
    protobuf = memcache.get('admin')

    if protobuf is not None:
        return db.model_from_protobuf(protobuf)
    else:
        admin = Admin.get_by_key_name('admin')
        if admin is not None:
            protobuf = db.model_to_protobuf(admin)
            memcache.set('admin', protobuf)
            return admin

    return createAdmin()

def setAdmin(admin):
    admin.put()
    protobuf = db.model_to_protobuf(admin)
    memcache.set('admin', protobuf)
