import json
import os
from typing import Dict
from hmac import compare_digest, new
import hashlib


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


def _is_valid(request_signature: str, payload: str):
    secret = os.environ['SECRET']
    signature = f'sha1={new(key=secret.encode(), msg=payload, digestmod=hashlib.sha1)}'
    return compare_digest(signature, request_signature)


def branch_creation_handler(event: Dict, context):

    content = event.get('body')
    if not content:
        return _error(400, 'payload empty or missing')

    body_as_str = json.dumps(content, indent=None)
    if not body_as_str:
        return _error(400, 'payload empty or missing')

    signature = event.get('headers', {}).get('X-Hub-Signature')
    if not signature:
        return _error(400, 'X-Hub-Signature missing')

    if not _is_valid(signature, body_as_str):
        return _error(403, 'X-Hub-Signature is invalid')

    return _ok('alles klar')

    # print(event)
    #print(json.dumps(event, indent=False))