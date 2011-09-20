import fix_path

import sys
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from pyamf.remoting.gateway.google import WebAppGateway

from serviceUtils import getServices


# allow pyamf to test remote services
def gateway(debug=False):
    servicesEnabled = getServices(['secureService'])
    return WebAppGateway(servicesEnabled, logger=logging, debug=debug)

# allow webtest.TestApp to get application
def application(debug=False):
    application_paths = [('/', gateway(debug))]
    return webapp.WSGIApplication(application_paths, debug=debug)

def main():
    run_wsgi_app(application(True))


if __name__ == '__main__':
    main()
