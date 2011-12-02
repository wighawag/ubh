#!/usr/bin/env python
# coding: utf-8

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json
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
            player = createPlayer('googleUser_' + userId, "nickName" + userId)
            playerId = player.key().id_or_name()
            googleUser = GoogleUser(key_name=userId, playerId=playerId)
            googleUser.put();

        method = self.request.get("method", default_value=None)
        if method is None:
            if self.request.scheme == 'https':
                method = 'signedRequest'
            else:
                method = 'token'

        session = createPlayerSession(playerId, method)
        if method == 'token':
            flashvars = {u'method' : 'token', u'sessionToken' : session.token, u'playerId' : playerId}
        elif method == 'signedRequest':
            flashvars = {u'method' : 'signedRequest', u'secret' : session.secret, u'playerId' : playerId}


        name = "googleUser"
        data = {}
        data[u'flashvars'] = json.dumps(flashvars)
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


