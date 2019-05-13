import json
from typing import Dict

from lambdas.dna_bot.commons import _is_valid, _error, _ok


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