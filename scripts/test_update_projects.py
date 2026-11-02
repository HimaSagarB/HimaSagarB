import io
import json
import unittest
from unittest.mock import patch
from update_projects import fetch_repositories, render_projects, replace_projects, START, END


def repository(name, **overrides):
    repo = {'name': name, 'full_name': f'HimaSagarB/{name}',
            'html_url': f'https://github.com/HimaSagarB/{name}',
            'private': False, 'updated_at': '2026-01-01T00:00:00Z'}
    repo.update(overrides)
    return repo


class ProjectsTests(unittest.TestCase):
    def test_new_projects_appear_after_featured_without_private_or_profile(self):
        repos = [repository('brand-new-project', updated_at='2026-11-02T00:00:00Z'),
                 repository('older-project'), repository('JobAssist'),
                 repository('HimaSagarB'), repository('private-project', private=True)]
        rendered = render_projects(repos, 'HimaSagarB', 'HimaSagarB/HimaSagarB')
        self.assertLess(rendered.index('[JobAssist]'), rendered.index('[brand new project]'))
        self.assertLess(rendered.index('[brand new project]'), rendered.index('[older project]'))
        self.assertNotIn('private-project', rendered)
        self.assertNotIn('/HimaSagarB)', rendered)

    def test_removed_featured_project_is_not_invented(self):
        rendered = render_projects([repository('NewProject')], 'HimaSagarB', 'HimaSagarB/HimaSagarB')
        self.assertIn('[NewProject]', rendered)
        self.assertNotIn('JobAssist', rendered)

    def test_replacement_preserves_other_content_and_is_idempotent(self):
        original = f'Profile intro\n{START}\nOld list\n{END}\nToolkit and contact'
        updated = replace_projects(original, '- New project')
        self.assertTrue(updated.startswith('Profile intro\n'))
        self.assertTrue(updated.endswith('\nToolkit and contact'))
        self.assertEqual(updated, replace_projects(updated, '- New project'))
        with self.assertRaises(ValueError):
            replace_projects(original + START, '- New project')

    def test_failure_does_not_generate_an_empty_project_list(self):
        with self.assertRaises(ValueError):
            render_projects([], 'HimaSagarB', 'HimaSagarB/HimaSagarB')

    def test_pagination_fetches_projects_beyond_first_hundred(self):
        pages = [[repository(f'project-{i}') for i in range(100)], [repository('last-project')]]
        with patch('update_projects.urlopen', side_effect=[io.BytesIO(json.dumps(p).encode()) for p in pages]) as mocked:
            repos = fetch_repositories('HimaSagarB', 'test-token')
        self.assertEqual(len(repos), 101)
        self.assertIn('page=2', mocked.call_args.args[0].full_url)


if __name__ == '__main__':
    unittest.main()
