#!/usr/bin/env python
# coding: utf-8

from authentification.password.model import PasswordUser

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json



from player.session import createPlayerSession

from player.model import createPlayer

import config

class MainPage(webapp.RequestHandler):

    def post(self):
        userId = self.request.get('userId')

        if config.passwordUserAllowed is None or userId not in config.passwordUserAllowed:
            self.error(403);
            return;

        password = self.request.get('password')
        method = self.request.get('method');

        passwordUser = PasswordUser.get_by_key_name(userId)
        if passwordUser is not None:
            if passwordUser.password != password:
                self.error(403);
                return;
            playerId = passwordUser.playerId
        else:
            player = createPlayer('passwordUser' + userId, "nickName" + userId)
            playerId = player.key().id_or_name()
            passwordUser = PasswordUser(key_name=userId, playerId=playerId, password=password)
            passwordUser.put();

        if method is None:
            if self.request.scheme == 'https':
                method = 'signedRequest'
            else:
                method = 'token'

        session = createPlayerSession(playerId, method)
        if method == 'token':
            data = {u'method' : 'token', u'sessionToken' : session.token, u'playerId' : playerId}
        elif method == 'signedRequest':
            data = {u'method' : 'signedRequest', u'secret' : session.secret, u'playerId' : playerId}


        data = json.dumps(data)

        self.response.out.write(data)


# allow webtest.TestApp to get application
def application(debug=False):
    return webapp.WSGIApplication([('.*', MainPage)], debug=debug)


def main():
    run_wsgi_app(application(True))

if __name__ == "__main__":
    main()


