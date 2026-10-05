"""配置项目内 Python 环境并下载固定版本的读取组件，仅支持 Windows 和 macOS。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def destination(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to((root / 'tools').resolve()):
        raise RuntimeError('依赖目标必须位于项目 tools 目录。')
    return path


def verify_bytes(content, expected):
    if hashlib.sha256(content).hexdigest() != expected:
        raise RuntimeError('依赖 SHA-256 校验失败，未安装该文件。')


def install_file(root, entry, check=False):
    path = destination(root, entry['path'])
    if path.is_file():
        try:
            verify_bytes(path.read_bytes(), entry['sha256'])
            return
        except RuntimeError:
            if check:
                raise RuntimeError(f"依赖文件已变化：{entry['path']}") from None
    if check:
        raise RuntimeError(f"缺少依赖：{entry['path']}；请先运行 bootstrap.py。")
    url = entry['url']
    if not url.startswith('https://raw.githubusercontent.com/') or entry['commit'] not in url:
        raise RuntimeError('只下载清单中固定 GitHub 提交的依赖。')
    print(f"下载并校验：{entry['path']}", flush=True)
    with urlopen(Request(url, headers={'User-Agent': 'wechat-chat-summary-setup'}), timeout=60) as response:
        if not response.geturl().startswith('https://raw.githubusercontent.com/'):
            raise RuntimeError('依赖下载重定向到了未允许的来源。')
        content = response.read(16 * 1024 * 1024 + 1)
    if len(content) > 16 * 1024 * 1024:
        raise RuntimeError('依赖文件超过允许大小。')
    verify_bytes(content, entry['sha256'])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.download')
    temporary.write_bytes(content)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='仅离线核对读取组件，不安装或联网')
    parser.add_argument('--fetch-only', action='store_true', help='仅下载组件；用于已有环境和 CI')
    parser.add_argument('--without-hook', action='store_true', help='不下载 Windows 自动连接组件')
    args = parser.parse_args()
    if sys.platform not in ('win32', 'darwin'):
        parser.error('仅支持 Windows 和 macOS。')
    if sys.version_info < (3, 11):
        parser.error('需要 Python 3.11 或更高版本。')
    if sys.platform == 'win32' and platform.machine().lower() not in ('amd64', 'x86_64') and not args.without_hook:
        parser.error('自动连接组件仅支持 Windows x64；其他架构使用 --without-hook 和 --import-key。')
    manifest = json.loads((ROOT / 'dependencies.json').read_text(encoding='utf-8'))
    if manifest['version'] != 1:
        raise RuntimeError('依赖清单版本不支持。')
    for entry in manifest['files']:
        if sys.platform in entry['platforms'] and not (args.without_hook and entry['project'] == 'WeFlow'):
            install_file(ROOT, entry, args.check)
    package = ROOT / 'tools/wx-reader/wx_reader/__init__.py'
    if not args.check:
        package.parent.mkdir(parents=True, exist_ok=True)
        package.write_text('"""固定版本的上游数据库读取模块，许可证见父目录 LICENSE。"""\n', encoding='utf-8')
    elif not package.is_file():
        raise RuntimeError('缺少读取模块包入口，请重新运行 bootstrap.py。')
    if args.check:
        print('读取组件离线校验通过；此检查不证明凭证有效或真实微信兼容。')
        return
    if not args.fetch_only:
        venv = ROOT / '.venv'
        interpreter = venv / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        if not interpreter.is_file():
            subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
        subprocess.run([str(interpreter), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(ROOT / 'requirements.txt')], check=True)
        print('环境已配置：使用 .venv 中的 Python 运行 scripts/local-reader.py。')
    else:
        print('读取组件已配置；Python 包需在当前环境单独安装。')


if __name__ == '__main__':
    try:
        main()
    except RuntimeError as error:
        print(f'配置未完成：{error}', file=sys.stderr)
        sys.exit(1)
    except Exception:
        # 网络/子进程异常可能含代理地址或本机路径，不输出原始异常。
        print('配置未完成：请检查 Python 版本、网络和依赖 SHA-256；组件已校验部分可保留重试。', file=sys.stderr)
        sys.exit(1)
