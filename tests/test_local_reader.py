"""验证本机凭证保护，以及跨分片读取的时间边界和压缩消息。"""
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('local_reader', ROOT / 'scripts/local-reader.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReaderTests(unittest.TestCase):
    def test_media_transport_secrets_not_exported(self):
        media = '<msg><img aeskey="synthetic-secret" /></msg>'
        self.assertEqual(module.readable_content(media, 3), '[图片，未识别内容]')
        self.assertNotIn('synthetic-secret', module.readable_content(media, 3))
        location = '<msg><location poiname="测试咖啡店" label="测试路1号" x="1" y="2" /></msg>'
        self.assertEqual(module.readable_content(location, 48), '[位置] 测试咖啡店；测试路1号')
        self.assertEqual(module.readable_content('<voipmsg><VoIPBubbleMsg><msg>通话时长 01:49</msg><roomkey>secret</roomkey></VoIPBubbleMsg></voipmsg>', 50), '[通话] 通话时长 01:49')

    def test_dpapi_roundtrip(self):
        if sys.platform != 'win32':
            self.skipTest('DPAPI 仅 Windows')
        sample = b'non-secret-synthetic-test-credential'
        encrypted = module.protect(sample)
        self.assertNotIn(sample, encrypted)
        self.assertEqual(module.protect(encrypted, decrypt=True), sample)

    def test_mac_keychain_route_and_no_plaintext_file(self):
        store = {}
        class FakeKeychain:
            def set_password(self, service, name, value): store[(service, name)] = value
            def get_password(self, service, name): return store.get((service, name))
        base = ROOT / '.cache/tests'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as folder:
            root = Path(folder)
            with patch.object(module.sys, 'platform', 'darwin'), patch.object(module, 'ROOT', root), patch.object(module, 'PRIVATE', root / 'data/connection'), patch.object(module, 'mac_keychain', return_value=FakeKeychain()):
                config = {'account': '/path/to/account', 'key': 'synthetic-placeholder', 'selfId': 'wxid_self'}
                module.save_credentials(config)
                self.assertEqual(module.read_credentials(), config)
                self.assertFalse((root / 'data').exists())
                with patch.object(module, 'mac_keychain', side_effect=RuntimeError('private-error-detail')):
                    with self.assertRaisesRegex(RuntimeError, '^无法读取 macOS Keychain'):
                        module.read_credentials()

    def test_import_requires_interactive_terminal_and_known_self(self):
        with patch.object(module.sys.stdin, 'isatty', return_value=False):
            with self.assertRaisesRegex(RuntimeError, '本机交互终端'):
                module.import_key(Path('unused'), None)
        self.assertEqual(module.infer_self_id(Path('wxid_self_e3d4')), 'wxid_self')
        with self.assertRaisesRegex(RuntimeError, '--self-id'):
            module.infer_self_id(Path('opaque-account'))

    def test_unknown_platform_is_rejected(self):
        with patch.object(module.sys, 'platform', 'linux'):
            with self.assertRaisesRegex(RuntimeError, '仅支持'):
                module.require_platform()

    def test_actual_sql_range_across_shards_and_zstd(self):
        import hashlib
        import zstandard
        base = ROOT / '.cache/tests'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as folder:
            root = Path(folder)
            self.assertTrue(root.resolve().is_relative_to(base.resolve()))
            table = 'Msg_' + hashlib.md5(b'test@chatroom').hexdigest()
            connections = {}
            for number in (0, 1):
                source = root / f'message_{number}.db'
                conn = sqlite3.connect(source)
                conn.row_factory = sqlite3.Row
                conn.execute(f'CREATE TABLE [{table}] (local_id INTEGER, server_id INTEGER, local_type INTEGER, real_sender_id INTEGER, create_time INTEGER, message_content BLOB, compress_content BLOB)')
                connections[source] = conn
            first, second = connections.values()
            first.executemany(f'INSERT INTO [{table}] VALUES (?, ?, 1, 1, ?, ?, NULL)', [(1, 1, 113599, b'outside'), (2, 2, 113600, b'edge'), (3, 3, 200001, b'future')])
            compressed = zstandard.ZstdCompressor().compress('wxid_sender:\n明天交付'.encode())
            second.executemany(f'INSERT INTO [{table}] VALUES (?, ?, 1, 1, ?, ?, NULL)', [(2, 2, 113600, b'edge'), (4, 4, 200000, compressed)])
            class FakeReader:
                _my_wxid = 'wxid_self'
                def _message_dbs(self): return list(connections)
                def _tables_of(self, source): return {table}
                def _connect(self, source): return connections[source]
                def _sender_map(self, source): return {1: 'wxid_sender'}
                def get_display_names(self, usernames): return {'wxid_sender': '测试成员'}
            try:
                with patch.object(module, 'ROOT', root), patch.object(module.time, 'time', return_value=200000):
                    module.export(FakeReader(), [{'username': 'test@chatroom', 'displayName': '测试群'}], 24, [])
                data = json.loads((root / 'data/recent/200000/messages.json').read_text(encoding='utf-8'))
                messages = data['chats'][0]['messages']
                self.assertEqual([m['serverId'] for m in messages], ['2', '4'])
                self.assertEqual(messages[-1]['content'], '明天交付')
                self.assertEqual(messages[-1]['senderName'], '测试成员')
            finally:
                for connection in connections.values(): connection.close()


if __name__ == '__main__':
    unittest.main()
