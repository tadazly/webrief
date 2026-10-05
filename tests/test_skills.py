from pathlib import Path
import re
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


class SkillTests(unittest.TestCase):
    def test_skills_are_discoverable_and_local_references_resolve(self):
        skills = list((ROOT / '.agents/skills').glob('*/SKILL.md'))
        self.assertEqual(len(skills), 2)
        for path in skills:
            text = path.read_text(encoding='utf-8')
            self.assertTrue(text.startswith('---\n'))
            header = yaml.safe_load(text.split('---', 2)[1])
            self.assertEqual(header['name'], path.parent.name)
            self.assertTrue(header['description'])
            for reference in re.findall(r'\]\(([^)]+)\)', text):
                target = (path.parent / reference).resolve()
                self.assertTrue(target.is_relative_to(ROOT))
                self.assertTrue(target.exists(), reference)
            interface = yaml.safe_load((path.parent / 'agents/openai.yaml').read_text(encoding='utf-8'))['interface']
            self.assertIn('$' + header['name'], interface['default_prompt'])


if __name__ == '__main__':
    unittest.main()
