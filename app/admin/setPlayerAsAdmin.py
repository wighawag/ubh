#!/usr/bin/env python
# coding: utf-8

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from admin.model import getAdmin, setAdmin

class MainPage(webapp.RequestHandler):

    def get(self):
        playerId = self.request.get("playerId")
        admin = getAdmin()
        try:
            admin.playerList.index(playerId)
        except ValueError:
            admin.playerList.append(playerId)
            setAdmin(admin)
            self.response.out.write(playerId + " is now admin")
        else:
            self.response.out.write(playerId + " was already admin")


# allow webtest.TestApp to get application
def application(debug=False):
    return webapp.WSGIApplication([('.*', MainPage)], debug=debug)


def main():
    run_wsgi_app(application(True))

if __name__ == "__main__":
    main()


