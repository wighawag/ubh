#!/usr/bin/env python
# coding: utf-8


from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from stats.model import setStats, getStats

class MainPage(webapp.RequestHandler):

    def get(self):
        stats = getStats()
        stats.reviewTimeUnitWeight = 0
        setStats(stats)

        self.response.out.write(str(stats.reviewTimeUnitWeight))


# allow webtest.TestApp to get application
def application(debug=False):
    return webapp.WSGIApplication([('.*', MainPage)], debug=debug)


def main():
    run_wsgi_app(application(True))

if __name__ == "__main__":
    main()


