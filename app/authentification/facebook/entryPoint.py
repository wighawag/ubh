#!/usr/bin/env python
# coding: utf-8
from google.appengine.dist import use_library
from google.appengine.api import urlfetch
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from django.utils import simplejson as json
from google.appengine.ext.webapp import template

from authentification.facebook.model import FacebookUser

from player.session import createPlayerSession

from player.model import createPlayer

import config

import base64
import hashlib
import hmac
import urllib

# yoctomata
FACEBOOK_APP_ID = "173860999314037"
FACEBOOK_APP_SECRET = "fa45b2d9686d77a3ceb6f1d48761fd53"
FACEBOOK_APP_API_KEY = "2114887b3cdc746e96b062d440bc4766"
FACEBOOK_CANVAS_PAGE_URL = 'http://apps.facebook.com/yoctomata/' # need to switch to https in case https was requested

class MainPage(webapp.RequestHandler):

    def post(self):
        data = parse_signed_request(self.request.get("signed_request"),FACEBOOK_APP_SECRET)
        if (not data.has_key("user_id")):
            args = {'client_id' : FACEBOOK_APP_ID , 'redirect_uri' : FACEBOOK_CANVAS_PAGE_URL}
            url = "https://www.facebook.com/dialog/oauth?" + urllib.urlencode(args)
            self.response.out.write('<script language="javascript">top.location.href="' + url + '"</script>')
            return

        userId = data['user_id']
        oauthToken = data['oauth_token']
        facebookUser = FacebookUser.get_by_key_name(userId)
        if facebookUser is not None:
            if facebookUser.oauthToken != oauthToken:
                facebookUser.oauthToken = oauthToken;
                facebookUser.put();
            playerId = facebookUser.playerId
        else:
            # if the facebook user has more than X friends, then he is allowed to verify old scores (if any) directly
            #friends = facebookApi(u'/me/friends', oauthToken)
            #enoughFriend = len(friends.data) > 5

            player = createPlayer('facebook_' + userId, "nickName" + userId)
            playerId = player.key().id_or_name()
            facebookUser = FacebookUser(key_name=userId, playerId=playerId, oauthToken=oauthToken)
            facebookUser.put();


        session = createPlayerSession(playerId)
        data = {}
        data[u'flashvars'] = json.dumps({u'sessionToken' : session.token, u'playerId' : playerId, u'facebookOauthToken': oauthToken})
        data[u'title'] = u'FJump (XJump remasterized)'
        data[u'facebookAppId'] = FACEBOOK_APP_ID
        self.response.out.write(template.render(
            config.templatesPath + 'facebookCanvas.html',
            data))


def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

def parse_signed_request(signed_request, secret):

    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]

    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))

    if data.get('algorithm').upper() != 'HMAC-SHA256':
        #log.error('Unknown algorithm')
        return None
    else:
        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

    if sig != expected_sig:
        return None
    else:
        #log.debug('valid signed request received..')
        return data

def facebookApi(path, access_token, params=None, method=u'GET', domain=u'graph'):
    """Make API calls"""
    if not params:
        params = {}
    params[u'method'] = method
    params[u'access_token'] = access_token
    data = urlfetch.fetch(
        url=u'https://' + domain + u'.facebook.com' + path,
        payload=urllib.urlencode(params),
        method=urlfetch.POST,
        headers={
            u'Content-Type': u'application/x-www-form-urlencoded'});
    result = json.loads(data.content)
    if isinstance(result, dict) and u'error' in result:
        raise FacebookApiError(result)
    return result

class FacebookApiError(Exception):
    def __init__(self, result):
        self.result = result

    def __str__(self):
        return self.__class__.__name__ + ': ' + json.dumps(self.result)

# allow webtest.TestApp to get application
def application(debug=False):
    return webapp.WSGIApplication([('.*', MainPage)], debug=debug)


def main():
    run_wsgi_app(application(True))

if __name__ == "__main__":
    main()
