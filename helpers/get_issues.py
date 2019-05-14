import os
from _ast import List

from github import Github, Label
import csv
from collections import Counter

if __name__ == '__main__':

    all_labels: List = []

    g = Github(os.environ['GITHUB_ACCESS_TOKEN'])


    with open('github_issues.csv', 'w', newline='') as csvfile:
        fieldnames = ['issue_id', 'title','body', 'joined_labels']
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        csv_writer.writeheader()
        # TODO: use search_issues() instead of
        for r in g.get_organization('hypoport').get_repos():
            print(r.name)
            for i in g.get_organization('hypoport').get_repo(r.name).get_issues(state='all'):
                label_names = [l.name for l in i.labels]
                if not label_names:
                    continue
                all_labels += label_names

                csv_writer.writerow({'issue_id': i.id, 'title': i.title, 'body': i.body, 'joined_labels':"**".join(label_names)})

    for label, count in Counter(all_labels).items():
        print(f'{label}={count}')


