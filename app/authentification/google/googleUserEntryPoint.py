#!/usr/bin/env python
# coding: utf-8
from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson as json
from google.appengine.ext.webapp import template

from google.appengine.api import users

from authentification.google.model import GoogleUser

from player.session import createPlayerSession

from player.model import createPlayer

import config

class MainPage(webapp.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if user is None :
            self.error(403)
            return

        userId = user.user_id()
        googleUser = GoogleUser.get_by_key_name(userId)
        if googleUser is not None:
            playerId = googleUser.playerId
        else:
            player = createPlayer('googleUser_' + userId, "nickName" + userId, 80)
            playerId = player.key().id_or_name()
            googleUser = GoogleUser(key_name=userId, playerId=playerId)
            googleUser.put();

        session = createPlayerSession(playerId)
        name = "googleUser"
        data = {}
        data[u'flashvars'] = json.dumps({u'sessionToken' : session.token, u'playerId' : playerId})
        data[u'title'] = u'FJump (XJump remasterized)'
        self.response.out.write(template.render(
            config.templatesPath + name + '.html',
            data))


# allow webtest.TestApp to get application
def application(debug=False):
    return webapp.WSGIApplication([('.*', MainPage)], debug=debug)


def main():
    run_wsgi_app(application(True))

if __name__ == "__main__":
    main()


