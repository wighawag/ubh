#!/usr/bin/env python
# coding: utf-8

import hashlib
import hmac
import base64

def decode_signedRequest(signedRequest):
    l = signedRequest.split('.', 2)
    encoded_signature = l[0]
    signature = base64_url_decode(encoded_signature)
    payload = l[1]

    return signature, payload

def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor
    return base64.b64decode(unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))


def verifySignature(signature, payload, secret, algorithm = 'HMAC-SHA256'):

    if algorithm != 'HMAC-SHA256':
        #log.error('Unknown algorithm')
        return None
    else:
        expected_sig = create_HMACSHA256_Signature(payload, secret)

    return signature == expected_sig

def create_HMACSHA256_Signature(payload, secret):
    return hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()