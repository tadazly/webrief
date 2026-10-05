# macOS 接入与验证

## 当前支持范围

macOS 使用和 Windows 相同的时间筛选、消息合并及导出代码，凭证由系统 Keychain 保存。提供本机交互导入，不提供微信进程自动提取。

**尚未完成真实 Mac 微信端到端验证。** Windows 上的 Mac 分支单元测试只能验证逻辑，不能证明某个 Mac 微信版本可连接。当前读取器要求账号目录中存在 `db_storage/session/session.db`、`db_storage/contact/contact.db` 和对应消息库，并使用上游支持的微信 4.x 数据库结构及加密方式。旧版微信或不同目录、表结构不在已支持范围内。

## 首次使用

1. 使用 macOS 11 或更高版本，以及 Python 3.11 或更高版本；Python 架构需与系统和 Keychain 依赖兼容。
2. 在项目根目录运行 `python3 scripts/bootstrap.py`。依赖装在本项目 `.venv/`；不需要管理员权限，不修改全局 Python。
3. 自行使用可信工具取得**本人当前 Mac 微信账号**的数据库凭证。本项目不负责这一提取步骤，也不要求关闭 SIP、降级微信或修改微信程序。
4. 在本机终端执行下面命令，按提示输入凭证。参数填写包含 `db_storage` 的账号目录和本人微信 ID；禁止把凭证写入命令、聊天或文档。

```sh
.venv/bin/python scripts/local-reader.py --import-key --account '/path/to/account' --self-id 'wxid_example'
```

输入默认隐藏；没有交互终端或无法隐藏输入时，程序会停止。首页数据库验证成功后才写入 Keychain。系统弹出的钥匙串授权需要用户自行处理，Agent 不应代替点击授权。

```sh
.venv/bin/python scripts/local-reader.py --list
.venv/bin/python scripts/local-reader.py --chat '联系人名' --hours 24
.venv/bin/python scripts/local-reader.py --chat '群名一' --chat '群名二'
```

移动项目目录会改变 Keychain 服务名，此时需要重新导入。Windows DPAPI 文件不能移到 Mac 使用，凭证也不能在不同微信账号之间复用。

## 真实 Mac 验收

在宣称某个 Mac 微信版本已验证前，需在该设备上完成以下检查，记录系统、架构、Python 与微信版本以及结果，记录中不要包含真实账号和聊天正文：

- 新目录执行安装，固定文件校验通过；非交互导入明确拒绝。
- 虚构或其他账号的凭证被拒绝，正确凭证成功写入 Keychain；重开终端可以复用。
- 对一个明确授权的会话导出最近 24 小时，与微信界面核对若干消息时间、发送方向、群聊发送者和边界；不要用其他人的记录做样例。
- 新收到一条消息后重新导出，确认缓存更新而非复用旧消息。
- 导出没有媒体传输密钥，数据库异常时明确报错；`audit-public.py` 不包含任何本机数据。

如果目录或数据结构不兼容，停止并记录错误类别，不应声称成功。可以将可信工具导出的可读记录交给当前 Codex 会话总结；这是文件总结，不等于本项目完成了 Mac 微信读取。
