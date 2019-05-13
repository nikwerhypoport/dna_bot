import hashlib
import os
from hmac import new, compare_digest


def _is_valid(request_signature: str, payload: str):
    secret = os.environ['SECRET']
    signature = f'sha1={new(key=secret.encode(), msg=payload, digestmod=hashlib.sha1)}'
    return compare_digest(signature, request_signature)


def _response(status:int, message:str):
    return {
        'isBase64Encoded': False,
        'headers': {},
        'statusCode': status,
        'body': '{"message" : "%s" }' % message.replace('"', '\\"').replace('\n', '\\n')  # json escape
    }


def _error(status=400, message='Could not perform request'):
    return _response(status, message)


def _ok(message: str):
    return _response(200, message)
