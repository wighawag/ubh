import simplejson as json
import string

def getFlashVarsFromResponse(response):
    startFlashvarsPosition = string.find(response.body, 'flashvars = ') + 11
    endFlashvarsPosition = string.find(response.body, '}', startFlashvarsPosition) + 1
    flashvars = response.body[startFlashvarsPosition : endFlashvarsPosition]
    return json.loads(flashvars)
