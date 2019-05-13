import json
import os
from typing import Dict

import requests

from dna_bot.commons import _is_valid, _error, _ok, GithubEventType


def _is_issue_comment(event: Dict):
    return GithubEventType.ISSUE_COMMENT.value == event.get('headers', {}).get('X-GitHub-Event')


def _exists(branch_name: str, repository_url: str, session: requests.Session):
    print(f'{repository_url}/git/refs/{branch_name}')
    response = session.get(f'{repository_url}/git/refs/{branch_name}')
    print(response.status_code)
    print(response.content)
    print(response.status_code == 200)
    return response.status_code == 200

def _get_head_to_branch_from(repository_url: str, session: requests.Session):
    print(f'{repository_url}/git/refs/heads/master')
    response = session.get(f'{repository_url}/git/refs/heads/master')
    print(response.status_code)
    print(response.content)
    print(response.status_code == 200)
    return response.content.get('object', {}).get('sha')

def _create_new_branch(session, issue_number: int, repository_url: str):
    branch_name = f'fix_{issue_number}'
    branch_subsequent_number = 1
    while _exists(branch_name, repository_url, session):
        branch_name = f'fix_{issue_number}_{branch_subsequent_number}'
        branch_subsequent_number += 1

    head = _get_head_to_branch_from(repository_url, session)
    print(head)
    payload = {
       'ref': f'refs/heads/{branch_name}',
       'sha': head

    }
    requests.post(f'{repository_url}/git/refs', json=payload)

    return branch_name

def _contains_command(content: str):
    return content.find('_cb_') >= 0

def _create_branch(session, content: Dict):
    comment_body: str = content.get('comment', {}).get('body', '')

    if not comment_body:
        _ok(f'No comment content found')

    if not _contains_command(comment_body):
        _ok(f'No magic word in comment')

    issue_number: str = content.get('issue', {}).get('number')
    repository_url: str = content.get('issue', {}).get('repository_url')

    branch_name = _create_new_branch(session, issue_number, repository_url)



    return _ok(f'created branch {branch_name} on {repository_url}')


def _authenticate():
    github_access_token = os.environ['GITHUB_ACCESS_TOKEN']
    session = requests.Session()
    session.headers.update({'Authorization': f'token {github_access_token}'})
    session.get('https://api.github.com/user')
    return session

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

    with _authenticate() as session:
        return _create_branch(session, content)
