"""Refresh only the marked project list using the owner's public GitHub repositories."""
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

START = '<!-- PROJECTS:START -->'
END = '<!-- PROJECTS:END -->'
FEATURED = [
    ('Software_Community-PrioApp', 'CivicPriority'),
    ('AI_ProductsReccomendation', 'Smart Product Advisor'),
    ('JobAssist', 'JobAssist'),
    ('NNDL_Waste-Classification', 'Waste Classification'),
]


def fetch_repositories(owner, token=None):
    if not re.fullmatch(r'[A-Za-z0-9-]+', owner):
        raise ValueError('Invalid GitHub owner')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'profile-project-list'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    repositories = []
    page = 1
    while True:
        request = Request(
            f'https://api.github.com/users/{owner}/repos?type=owner&sort=updated&per_page=100&page={page}',
            headers=headers,
        )
        with urlopen(request, timeout=30) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise ValueError('Expected a repository list from GitHub')
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def render_projects(repositories, owner, profile_repository):
    public = {}
    for repo in repositories:
        full_name = repo.get('full_name', '')
        if repo.get('private') or full_name.casefold() == profile_repository.casefold():
            continue
        if full_name.partition('/')[0].casefold() != owner.casefold():
            continue
        if not repo.get('html_url', '').startswith(f'https://github.com/{owner}/'):
            raise ValueError('Unexpected repository destination')
        public[repo['name']] = repo
    if not public:
        raise ValueError('No public projects returned; preserving the current README')
    ordered = []
    for name, label in FEATURED:
        if name in public:
            ordered.append((public.pop(name), label))
    for repo in sorted(public.values(), key=lambda r: (r.get('updated_at', ''), r['name']), reverse=True):
        ordered.append((repo, repo['name'].replace('_', ' ').replace('-', ' ')))
    lines = [f"- [{label}]({repo['html_url']})" for repo, label in ordered]
    lines += ['', f'[View all repositories →](https://github.com/{owner}?tab=repositories&sort=updated)']
    return '\n'.join(lines)


def replace_projects(readme, projects):
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError('README must contain exactly one pair of project markers')
    before, remainder = readme.split(START)
    _, after = remainder.split(END)
    return before + START + '\n\n' + projects + '\n\n' + END + after


def main():
    owner = os.environ.get('PROFILE_OWNER', 'HimaSagarB')
    profile_repository = os.environ.get('GITHUB_REPOSITORY', f'{owner}/{owner}')
    path = Path(__file__).resolve().parents[1] / 'README.md'
    repos = fetch_repositories(owner, os.environ.get('GITHUB_TOKEN'))
    updated = replace_projects(path.read_text(), render_projects(repos, owner, profile_repository))
    if updated != path.read_text():
        path.write_text(updated)
        print('Updated the public project list.')
    else:
        print('The public project list is already current.')


if __name__ == '__main__':
    main()
