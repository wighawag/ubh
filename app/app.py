import fix_path

import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from pyamf.remoting.gateway.google import WebAppGateway

from service.secure import sessionTokenCall, signedRequestCall

from google.appengine.ext import ereporter


# allow pyamf to test remote services
def gateway(debug=False):
    servicesEnabled = {'sessionTokenCall' :sessionTokenCall, 'signedRequestCall' : signedRequestCall}
    return WebAppGateway(servicesEnabled, logger=logging, debug=debug)

# allow webtest.TestApp to get application
def application(debug=False):
    application_paths = [('/', gateway(debug))]
    return webapp.WSGIApplication(application_paths, debug=debug)

def main():
    ereporter.register_logger()
    run_wsgi_app(application(True))


if __name__ == '__main__':
    main()
