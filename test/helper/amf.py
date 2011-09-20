from pyamf.remoting import amf3
from pyamf.flex import messaging
from pyamf import remoting


def executeService(gw, service, *args):
    rp = amf3.RequestProcessor(gw)
    message = messaging.RemotingMessage(body=args, operation='secureService.sessionTokenCall')
    request = remoting.Request('null', body=[message])

    response = rp(request)
    return response

def isResponseOk(response):
    return (
            isinstance(response, remoting.Response)
            and response.status == remoting.STATUS_OK
            and isinstance(response.body, messaging.AcknowledgeMessage)
            )

def isResponseBad(response):
    return (
            isinstance(response, remoting.Response)
            and response.status == remoting.STATUS_ERROR 
            )

def getMessageFromResponse(response):
    return response.body.body
