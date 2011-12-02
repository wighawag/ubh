import simplejson as json

from crypto.signature import create_HMACSHA256_Signature, create_CUSTOM_SHA1_Signature
import base64

def createSignedRequest(playerId, secret, methodName, *args):
    jsonData = json.dumps({u'playerId' : playerId, u'methodName' : methodName, u'args' : args} )
    payload = base64.b64encode(jsonData)

    signature = create_CUSTOM_SHA1_Signature(payload, secret)
    encoded_signature = base64.b64encode(signature)

    return encoded_signature + u'.' + payload