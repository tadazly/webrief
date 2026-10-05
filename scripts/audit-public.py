"""检查 Git 可发布文件，不读取被忽略的个人聊天目录，不输出敏感匹配值。"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PRIVATE_PARTS = {'data', 'tools', '.deps', '.cache', '.venv', 'local', 'dist', 'node_modules'}
PRIVATE_SUFFIXES = {'.db', '.sqlite', '.sqlite3', '.dpapi', '.dll', '.dylib', '.pem', '.key', '.p12'}
PATTERNS = {
    '个人 Windows 路径': re.compile(r'[A-Z]:[\\/]Users[\\/][^\s"\'<>]+', re.I),
    '个人 macOS 路径': re.compile('/' + r'Users/[^\s/"\'<>]+/'),
    '真实微信账号候选': re.compile(r'wxid_[a-zA-Z0-9]{12,}'),
    '媒体传输密钥': re.compile(r'aeskey=["\'][a-zA-Z0-9]{16,}'),
    '访问令牌': re.compile(r'(?:gh[pousr]_[a-zA-Z0-9]{20,}|github_pat_[a-zA-Z0-9_]{20,}|sk-[a-zA-Z0-9_-]{24,})'),
    '私钥': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    '数据库凭证候选': re.compile(r'(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])'),
}


def inspect_file(relative, content):
    path = Path(relative)
    findings = []
    if any(part in PRIVATE_PARTS for part in path.parts) or path.suffix.lower() in PRIVATE_SUFFIXES or (path.name.startswith('.env') and path.name != '.env.example'):
        return [(relative, 0, '禁止发布的本机文件')]
    if b'\x00' in content:
        return [(relative, 0, '待人工确认的二进制文件')]
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        return [(relative, 0, '非 UTF-8 文本')]
    if any(ord(character) < 32 and character not in '\n\r\t' for character in text):
        findings.append((relative, 0, '文本包含异常控制字符'))
    for number, line in enumerate(text.splitlines(), 1):
        for label, pattern in PATTERNS.items():
            if relative == 'dependencies.json' and label == '数据库凭证候选' and '"sha256"' in line:
                continue
            if pattern.search(line):
                findings.append((relative, number, label))
    return findings


def main():
    result = subprocess.run(['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'], cwd=ROOT, capture_output=True)
    if result.returncode:
        print('请先在项目根目录初始化 Git 仓库。', file=sys.stderr)
        return 1
    paths = sorted(set(p.decode('utf-8') for p in result.stdout.split(b'\x00') if p))
    findings = []
    for relative in paths:
        path = ROOT / relative
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            findings.append((relative, 0, '不发布指向其他位置的文件'))
        elif path.is_file():
            findings.extend(inspect_file(relative, path.read_bytes()))
    for relative, number, label in findings:
        print(f'{relative}:{number}：{label}（未显示匹配值）')
    print(f'检查 {len(paths)} 个 Git 可发布文件；发现 {len(findings)} 项。')
    if findings:
        return 1
    print('基础检查通过。仍需人工检查文档及待发布文件；正则扫描不能保证不存在敏感信息。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
