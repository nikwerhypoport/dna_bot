import json
import os
from typing import Dict
from github import Github, GithubException

from dna_bot.commons import _is_valid, _error, _ok, GithubEventType


def _is_issue_comment_created(event: Dict):
    return GithubEventType.ISSUE_COMMENT.value == event.get('headers', {}).get('X-GitHub-Event') and \
            event.get('body', {}).get('action') == 'created'


def _contains_command(content: str):
    return content.find('_cb_') >= 0


def _create_branch(content: Dict) -> str:
    issue_number: str = content.get('issue', {}).get('number')
    repository: str = content.get('repository', {}).get('name')
    branch_counter = 0
    branch_name = f'fix_issue_{issue_number}_{branch_counter}'

    g = Github(os.environ['GITHUB_ACCESS_TOKEN'])
    head = g.get_organization('hypoport').get_repo(repository).get_branch('master').commit.sha

    while True:
        try:
            g.get_organization('hypoport').get_repo(repository).create_git_ref(f'refs/heads/{branch_name}', head)
        except GithubException as e:
            branch_name, branch_counter = _rename_if_exists(e, issue_number, branch_counter)
        else:
            break

    return branch_name


def _rename_if_exists(e, issue_number, branch_counter):
    if e.status == 422 and e.data.get('message') == 'Reference already exists':
        branch_name = f'fix_issue_{issue_number}_{branch_counter}'
        branch_counter += 1
        print(branch_name)
        return branch_name, branch_counter
    else:
        raise e


def _update_comment(content: Dict, branch_name: str):
    repo_url = content.get('repository', {}).get('html_url')
    branch_html_url = f'{repo_url}/tree/{branch_name}'
    issue_number: str = int(content.get('issue', {}).get('number'))
    repository: str = content.get('repository', {}).get('name')
    g = Github(os.environ['GITHUB_ACCESS_TOKEN'])
    #g.get_organization('hypoport').get_repo(repository).get_issue(issue_number).create_comment(f'Created [branch]({branch_html_url})')

    comment_id = int(content.get('comment', {}).get('id'))
    comment = g.get_organization('hypoport').get_repo(repository).get_issue(issue_number).get_comment(comment_id)
    comment.edit(f'{comment.body} -> Created [branch]({branch_html_url})')
    comment.update()


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

    if not _is_issue_comment_created(event):
        return _ok('Nothing to do -event is not an issue comment')

    comment_body = content.get('comment', {}).get('body')
    if not comment_body:
        return _ok(f'No comment content found')

    if not _contains_command(comment_body):
        return _ok(f'No magic command in comment')

    branch_name = _create_branch(content)
    _update_comment(content, branch_name)
    return _ok(f'created branch {branch_name} on {content.get("repository", {}).get("html_url")}')
