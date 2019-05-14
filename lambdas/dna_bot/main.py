import json
import os
from typing import Dict
from github import Github, GithubException, GitRef

from dna_bot.commons import _is_valid, _error, _ok, GithubEventType


def _is_issue_comment(event: Dict):
    return GithubEventType.ISSUE_COMMENT.value == event.get('headers', {}).get('X-GitHub-Event')


def _contains_command(content: str):
    return content.find('_cb_') >= 0


def _create_branch(content: Dict) -> GitRef:
    issue_number: str = content.get('issue', {}).get('number')
    repository: str = content.get('repository', {}).get('name')
    branch_counter = 0
    branch_name = f'fix_issue_{issue_number}_{branch_counter}'

    g = Github(os.environ['GITHUB_ACCESS_TOKEN'])
    head = g.get_organization('hypoport').get_repo(repository).get_branch('master').commit.sha

    while True:
        try:
            ref = g.get_organization('hypoport').get_repo(repository).create_git_ref(f'refs/heads/{branch_name}', head)
        except GithubException as e:
            branch_name, branch_counter = _rename_if_exists(e, issue_number, branch_counter)
        else:
            break

    return ref


def _rename_if_exists(e, issue_number, branch_counter):
    if e.status == 422 and e.data.get('message') == 'Reference already exists':
        branch_name = f'fix_issue_{issue_number}_{branch_counter}'
        branch_counter += 1
        print(branch_name)
        return branch_name, branch_counter
    else:
        raise e


def _create_comment(content: Dict, branch_url: str):
    issue_number: str = int(content.get('issue', {}).get('number'))
    repository: str = content.get('repository', {}).get('name')
    g = Github(os.environ['GITHUB_ACCESS_TOKEN'])
    g.get_organization('hypoport').get_repo(repository).get_issue(issue_number).create_comment(f'Created [branch]({branch_url})')


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
        return _ok('Nothing to do -event is not an issue comment')

    comment_body = content.get('comment', {}).get('body')
    if not comment_body:
        _ok(f'No comment content found')

    if not _contains_command(comment_body):
        _ok(f'No magic command in comment')

    # return _ok('Nothing to do - event is not an issue comment')
    ref = _create_branch(content)
    _create_comment(content, ref.url)
    return _ok(f'created branch {ref.ref} on {content.get("repository", {}).get("html_url")}')
