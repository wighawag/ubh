#!/usr/bin/env python
# coding: utf-8


from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import config
from stats.model import  getStats, setStats
from player.model import Record
import datetime

class MainPage(webapp.RequestHandler):

    def get(self):
        stats = getStats()

        lastPlayerRecords = Record.gql("WHERE lastReviewDateTime > :firstDate ORDER BY lastReviewDateTime DESC", firstDate=datetime.datetime.min).fetch(1, config.nbPlayerPerTimeUnit - 1)

        if lastPlayerRecords is None or len(lastPlayerRecords) == 0:
            stats.reviewTimeUnit = 24 * 3600 * 1000
            stats.reviewTimeUnitWeight = 0
        else:
            lastPlayerRecordConsidered = lastPlayerRecords[0]
            now = datetime.datetime.now()

            timedelta = now - lastPlayerRecordConsidered.lastReviewDateTime

            #milliseconds
            newReviewTimeUnit = (timedelta.microseconds + (timedelta.seconds + timedelta.days * 24 * 3600) * 10**6) / 10**3

            reviewTimeUnitWeight = stats.reviewTimeUnitWeight
            stats.reviewTimeUnit = (reviewTimeUnitWeight * stats.reviewTimeUnit + newReviewTimeUnit) / (reviewTimeUnitWeight + 1)
            stats.reviewTimeUnitWeight = reviewTimeUnitWeight + 1

        setStats(stats)

        self.response.out.write(str(stats.reviewTimeUnit))


# allow webtest.TestApp to get application
def application(debug=False):
    return webapp.WSGIApplication([('.*', MainPage)], debug=debug)


def main():
    run_wsgi_app(application(True))

if __name__ == "__main__":
    main()


