# 第三方组件

本仓库的原创脚本、规则和技能采用 MIT 许可证。下载到本机的第三方模块、组件及 Python 包仍适用各自许可证；本仓库的 MIT 授权不替代它们的条款。

## 固定版本组件

| 来源 | 使用内容 | 固定提交 | 上游许可证 |
| --- | --- | --- | --- |
| [wx-assist](https://github.com/MaleleStudySpace/wx-assist) | `db_crypto.py`、`db_reader.py`、`content_codec.py`，保持文件原样 | `49ec2fe5ff56ad490cbdb548322aa496a6be30fa` | MIT，copyright cancelGuMu |
| [WeFlow（iminc 分支）](https://github.com/iminc/WeFlow) | 可选的 Windows x64 `wx_key.dll` 自动连接组件 | `93d46a3183b98bfe5073ea89ecaa32a4f80f79d3` | 仓库 LICENSE 为 CC BY-NC-SA 4.0，含非商业及相同方式共享条款 |

`dependencies.json` 保存来源 URL、提交和文件 SHA-256。安装器会下载并保留上游 LICENSE，分别放在 `tools/wx-reader/LICENSE` 和 `tools/WeFlow/LICENSE`，不重新分发这些组件到 Git。

Windows 自动连接 DLL 是上游预编译二进制，本项目没有审核其内部实现。自行选择是否下载和运行；使用 `bootstrap.py --without-hook` 可以只安装读取模块，之后在本机交互终端导入已有凭证。

## Python 包

依赖版本见 `requirements.txt`。pycryptodome、zstandard、keyring 及其传递依赖安装在本机 `.venv/`，不随仓库发布。打包或分发安装环境时，应另外保留这些包的许可证与声明。
