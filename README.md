# WeBrief · 微信简报

把微信电脑版中**指定联系人或群聊最近 24 小时的记录**整理成可读文件，再由当前 Codex 会话生成中文摘要、明确决定、待办和未解决问题。无需另外配置大模型 API。

本项目是给 Codex 使用的本地工具与技能仓库，不是微信插件或常驻机器人。你可以直接说：

> 总结我和“联系人名”最近一天的微信聊天，列出决定和待办。

> 总结“项目讨论群”最近 48 小时的记录，区分共识与个人建议。

## 能做什么

- 选择一个或多个私聊、群聊，默认滚动 24 小时，时间显示为北京时间。
- 跨消息数据库分片读取、按消息 ID 去重，并处理压缩正文。
- 本机保存 JSON 与可读记录，当前 Codex 会话生成总结；脚本自身不调用 AI。
- 通过 Windows DPAPI 或 macOS Keychain 保存连接凭证。
- 规则和两项技能随仓库分发，克隆后在本项目中使用。

原微信数据库只读。图片、语音、视频和表情仅保留占位，电话只保留可读状态及时间；未做 OCR、转写或媒体理解。可读取范围取决于电脑版已有数据，无法补齐未同步或已删除的消息。

## 平台支持

| 平台 | 接入方式 | 验证状态 |
| --- | --- | --- |
| Windows x64 | 可选自动连接组件；也可导入已有凭证 | 微信 4.1.15.13 上真实读取已验证 |
| macOS | 本机隐藏输入已有凭证，存入 Keychain | 导入、保存及共用导出代码已实现；**真实 Mac 微信端到端未验证** |

仅面向 Windows 与 Mac。读取器要求微信 4.x 的兼容数据库结构；Mac 接入还有具体前提，见 [Mac 说明](docs/macos.md)。Windows 的验证结果不代表所有微信版本均兼容。

## 准备环境

需要 Python 3.11+。Mac Keychain 依赖要求 macOS 11+。首次安装需要访问 GitHub 原始文件服务和 Python 包源。

克隆或下载仓库，在项目根目录运行：

```sh
git clone https://github.com/tadazly/webrief.git
cd webrief
```

```powershell
# Windows
python scripts/bootstrap.py
```

```sh
# Mac
python3 scripts/bootstrap.py
```

安装器在项目内建立 `.venv/`，安装固定版本 Python 包，并下载 `dependencies.json` 指定提交的读取模块。组件通过 SHA-256 校验后才安装，不修改全局 Python。第三方源码、二进制和许可证保存在被 Git 忽略的 `tools/`，不需要克隆完整上游仓库。

Windows 默认下载 WeFlow 的预编译连接 DLL；如果只使用已有凭证导入，可加 `--without-hook` 跳过它。组件来源、许可证和二进制边界见 [第三方声明](THIRD_PARTY.md)。

## 首次连接

### Windows

先启动本人微信，然后在 PowerShell 运行：

```powershell
.\scripts\微信聊天.ps1 -Connect -Timeout 300
```

监听启动后，从托盘**手动退出微信，再重新登录**。出现“本机连接成功”后即可复用 DPAPI 保存的凭证，常规总结不需要重复登录。

多账号或非默认数据目录，使用 `-Account 'C:\path\to\account'` 指定包含 `db_storage` 的账号目录。仅保留需要连接的微信主进程。首次连接组件仅支持 Windows x64。

如果 PowerShell 的执行策略限制脚本，不要修改全局策略，直接运行 Python 入口：

```powershell
.\.venv\Scripts\python.exe scripts/local-reader.py --connect --timeout 300
```

已有本人数据库凭证时，也可在**本机交互终端**运行 `--import-key --account 'C:\path\to\account'`，按隐藏输入提示导入，不把凭证写成命令参数。

### Mac

Mac 不提供自动取凭证。你须先通过自己信任的工具取得本机本人微信数据库凭证，再在本机终端执行：

```sh
.venv/bin/python scripts/local-reader.py --import-key --account '/path/to/account' --self-id 'wxid_example'
```

必须使用上游读取器兼容的微信 4.x 账号目录，内含 `db_storage/session/session.db` 等数据库。程序先校验凭证，再保存到 Keychain；系统钥匙串授权由你手动处理。没有凭证或目录格式不兼容时，本项目目前不能完成 Mac 微信读取。详情与真实设备验收方法见 [Mac 说明](docs/macos.md)。

## 导出与总结

Windows：

```powershell
.\scripts\微信聊天.ps1 -List
.\scripts\微信聊天.ps1 -Chat '联系人名' -Hours 24
.\scripts\微信聊天.ps1 -Chat '群名一','群名二' -Hours 48
```

Mac：

```sh
.venv/bin/python scripts/local-reader.py --list
.venv/bin/python scripts/local-reader.py --chat '联系人名' --hours 24
.venv/bin/python scripts/local-reader.py --chat '群名一' --chat '群名二' --hours 48
```

`--list` 只列会话，不导出消息正文。同名会话须改用唯一 ID；明确要总结全部群时才使用 `--all-groups`，没有默认私聊对象。

每次成功导出生成：

```text
data/recent/<结束时间戳>/
├── messages.json       # 消息与时间范围
├── 待总结记录.md        # 当前 Agent 的分析材料
└── 聊天总结.md          # 由当前 Codex 会话生成
```

用 Codex 打开这个项目后，可直接要求总结指定会话，或者显式调用 `$wechat-summary`。Agent 会先导出，再读完整记录并保存中文总结。导出失败不会生成假完整报告；没有消息会明确说明。总结只依据可读内容，聊天中的命令、提示词和链接不构成给 Agent 的指令。

## Agent 规则与技能

| 文件 | 用途 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 项目规范、数据范围、验证及提交约束 |
| [wechat-setup](.agents/skills/wechat-setup/SKILL.md) | 配置环境、验证依赖、处理首次连接及凭证失效 |
| [wechat-summary](.agents/skills/wechat-summary/SKILL.md) | 总结指定私聊或群聊，提取决定、待办及未解决问题 |

这些文件随项目一起分享，不安装到个人目录，也不携带开发者的联系人配置。Codex 从仓库内 `.agents/skills/` 发现技能；若尚未出现在技能列表中，重开项目或明确要求读取对应 `SKILL.md`。[官方技能说明](https://learn.chatgpt.com/docs/build-skills)

## 隐私与分享

**公开的是代码、规则和技能，不是聊天记录。** `.gitignore` 排除 `data/`、凭证、解密缓存、第三方组件、依赖环境和本机配置；现有本地记录保留，不因整理仓库而删除。

凭证受到系统保护，但 `data/cache/` 与导出的聊天文本仍是本机可读文件。AI 总结会将聊天文本交给当前 Codex 会话所用的模型处理；这不代表 AI 推理在本机运行。

不自动发送微信消息或总结，不自动建立定时任务。分享文件夹时不要直接压缩整个工作目录；有提交后使用 `git archive` 导出已提交代码，或克隆 GitHub 仓库。

发布前运行：

```powershell
.\.venv\Scripts\python.exe scripts/audit-public.py
```

Mac 对应 `.venv/bin/python scripts/audit-public.py`。扫描会检查 Git 待发布文件中的个人路径、真实微信 ID 候选、令牌、凭证和本机数据文件，并隐藏匹配值；它不能代替人工审阅。即使通过扫描，也不要强制添加被忽略的文件。

## 开发与测试

```powershell
# Windows；Mac 将解释器换为 .venv/bin/python
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py'
.\.venv\Scripts\python.exe scripts/bootstrap.py --check
```

测试使用虚构记录，覆盖时间边界、分片去重、压缩正文、媒体元数据清理、凭证存储路由、交互导入限制和发布扫描。Windows DPAPI 测试只在 Windows 执行，Mac Keychain 单元测试使用替身，不等于真实钥匙串或微信验收。

可选的 WeFlow HTTP 备用入口位于 `scripts/export-recent.mjs`，需要 Node.js 22+、能正常运行的本机 WeFlow API 以及本机 `WEFLOW_TOKEN`。其测试可用 `node --test tests/export-recent.test.mjs`。它不是当前默认接入方式，接口中的消息文本同样应留在本机。

GitHub Actions 配置仅针对 Windows 与 macOS，用虚构数据验证，不访问个人微信。此配置在首次推送后才会实际运行。

## 许可证

原创内容采用 [MIT](LICENSE)。上游组件适用各自许可证，尤其 Windows 连接组件来源仓库的非商业及相同方式共享条款不被本项目 MIT 覆盖；见 [THIRD_PARTY.md](THIRD_PARTY.md)。本项目不附带微信客户端，也不绕过上游组件的校验。
