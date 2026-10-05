import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bootstrap = load('bootstrap', 'scripts/bootstrap.py')
audit = load('audit', 'scripts/audit-public.py')


class ProjectTests(unittest.TestCase):
    def test_dependency_write_is_scoped_and_hash_mismatch_does_not_install(self):
        base = ROOT / '.cache/tests'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as folder:
            root = Path(folder)
            with self.assertRaises(RuntimeError):
                bootstrap.destination(root, '../escape.py')
            with self.assertRaises(RuntimeError):
                bootstrap.verify_bytes(b'changed', '0' * 64)
            path = root / 'tools/module.py'
            path.parent.mkdir()
            path.write_bytes(b'changed')
            entry = {'path': 'tools/module.py', 'sha256': '0' * 64}
            with self.assertRaisesRegex(RuntimeError, '已变化'):
                bootstrap.install_file(root, entry, check=True)
            self.assertEqual(path.read_bytes(), b'changed')

    def test_public_audit_detects_private_paths_secrets_and_tracked_ignored_files(self):
        self.assertTrue(audit.inspect_file('data/messages.json', b'{}'))
        self.assertTrue(audit.inspect_file('docs/example.md', ('ghp_' + 'a' * 30).encode()))
        self.assertTrue(audit.inspect_file('scripts/example.py', ('wxid_' + 'a' * 15).encode()))
        self.assertTrue(audit.inspect_file('docs/example.md', ('C:' + '/Users/' + 'someone/private').encode()))
        self.assertTrue(audit.inspect_file('docs/example.md', ('key=' + 'f' * 64).encode()))
        self.assertFalse(audit.inspect_file('dependencies.json', ('"sha256": "' + 'f' * 64 + '"').encode()))
        self.assertFalse(audit.inspect_file('README.md', '使用指定联系人名。'.encode()))

    def test_both_platforms_use_fixed_manifest_commits(self):
        data = json.loads((ROOT / 'dependencies.json').read_text(encoding='utf-8'))
        for entry in data['files']:
            self.assertIn('/' + entry['commit'] + '/', entry['url'])
            self.assertEqual(len(entry['sha256']), 64)
            self.assertFalse(set(entry['platforms']) - {'win32', 'darwin'})

    def test_chinese_cli_output_in_non_utf8_windows_environment(self):
        environment = {**os.environ, 'PYTHONIOENCODING': 'cp1252'}
        commands = [
            (['scripts/bootstrap.py', '--check', '--without-hook'], '读取组件'),
            (['scripts/local-reader.py', '--help'], '本机微信'),
            (['scripts/audit-public.py'], '检查'),
        ]
        for args, expected in commands:
            with self.subTest(script=args[0]):
                result = subprocess.run([sys.executable, *args], cwd=ROOT, env=environment, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8', errors='replace'))
                self.assertIn(expected, result.stdout.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
