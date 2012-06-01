import fix_path

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import simplejson as json

from google.appengine.ext import ereporter
from service.secure import signedRequestCall

class JsonRequestHandler(webapp.RequestHandler):

    # only post for now
    def post(self):
        try:
            #self.request.
            data = json.loads(self.request.body)
        except Exception, e:
            output = json.dumps({'id' : 'unknown', 'error' : {'code' : 35, 'message' : 'cannot parse the request' + e}})
            self.response.out.write(output)
            return;
        requestId = data['id']
        methodName = data['method']
        params = data['params']

        if methodName == "signedRequestCall":
            result = signedRequestCall(params[0])
            result['id'] = requestId
            output =json.dumps(result)
        else:
            output = json.dumps({'id' : requestId, 'error' : {'code' : 34, 'message' : 'method not supported'}})

        self.response.out.write(output)

# allow webtest.TestApp to get application
def application(debug=False):
    return webapp.WSGIApplication([('.*', JsonRequestHandler)], debug=debug)


def main():
    ereporter.register_logger()
    run_wsgi_app(application(True))

if __name__ == "__main__":
    main()