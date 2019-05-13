import json
from typing import Dict

import requests

from dna_bot.commons import _is_valid, _error, _ok, GithubEventType




def _is_issue_comment(event: Dict):
    return GithubEventType.ISSUE_COMMENT.value() == event.get('headers', {}).get('X-GitHub-Event')


def _exists(repository_url: str, branch_name: str):
    print(f'{repository_url}/git/refs/{branch_name}')
    response = requests.get(f'{repository_url}/git/refs/{branch_name}')
    print(response.status_code)
    print(response.content)
    print(response.status_code == 200)
    return response.status_code == 200


def _create_new_branch(issue_number: int, repository_url: str):

    branch_name = f'fix_{issue_number}'
    branch_subsequent_number = 1
    while _exists(repository_url, branch_name):
        branch_name = f'fix_{issue_number}_{branch_subsequent_number}'
        branch_subsequent_number += 1
    return branch_name
    #head = _get_head_to_branch_from(repository_url)
    #payload = {
    #    'ref': f'refs/heads/{branch_name}',
    #    'sha': head
    #
    # }
    # requests.post(f'{repository_url}/git/refs', json=payload)


def _create_branch(content: Dict):
    issue_number: str = content.get('issue', {}).get('number')
    comment_body: str = content.get('comment', {}).get('body', '')
    repository_url: str = content.get('issue', {}).get('repository_url')

    branch_name = _create_new_branch(issue_number)

    if not comment_body:
        _ok(f'No comment content found')

    return _ok(f'created branch {branch_name} on {repository_url}')


def branch_creation_handler(event: Dict, context):

    content = event.get('body')
    if not content:
        return _error(400, 'payload empty or missing')

    body_as_str = json.dumps(content, sort_keys=False, ensure_ascii=True, separators=(',', ':'))
    if not body_as_str:
        return _error(400, 'payload empty or missing')

    signature = event.get('headers', {}).get('X-Hub-Signature')
    if not signature:
        return _error(400, 'X-Hub-Signature missing')

    if not _is_valid(signature, body_as_str):
        return _error(403, 'X-Hub-Signature is invalid')

    if not _is_issue_comment(event):
        return _ok('Nothing to do - event is not an issue comment')

    return _create_branch(content)

    return _ok('alles klar')