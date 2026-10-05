---
name: wechat-setup
description: 配置本项目 Windows 或 macOS 的微信读取环境、验证固定依赖、建立或修复本机连接；用于首次安装、连接失效和平台迁移，不用于日常聊天总结。
---

# 配置微信读取环境

先定位包含 `dependencies.json` 的项目根目录，阅读根目录 README 的平台支持和首次连接部分。技能随仓库分发，不安装到个人技能目录，也不改写全局 Agent 配置。

使用 Python 3.11+ 运行 `scripts/bootstrap.py`，在项目内创建 `.venv/` 并获取固定提交、SHA-256 校验的读取组件。已有环境时可用 `--check` 离线检查组件；它不代表真实微信已连通。安装失败可核对环境和网络后重试一次，再根据具体阻塞处理，不自行换到未经核验的二进制。

- **Windows x64**：使用 `.venv/Scripts/python.exe scripts/local-reader.py --connect --timeout 300`。监听后提示用户手动退出并重新登录微信；检测到成功再继续。不要自动退出微信、代替登录或扩大到其他账号。已有 DPAPI 凭证且读取正常时跳过连接。多账号用 `--account` 指定本人目录。
- **macOS**：先阅读 [Mac 接入说明](../../../docs/macos.md)。不自动扫描用户目录或调用 Windows DLL。用户须在本机交互终端执行 `.venv/bin/python scripts/local-reader.py --import-key --account '/path/to/account' --self-id 'wxid_example'`，隐藏输入已有的本机数据库凭证，保存到 Keychain。不要要求把凭证发到聊天。当前不提供自动提取，真实 Mac 兼容性仍需设备验证。

安装或接入修复的验证以明确授权范围为限：组件校验、命令帮助、虚构数据测试；只有用户已授权实际会话读取时才做真实导出。完成后报告已验证内容与未验证的平台条件，给出下一条具体使用命令。

Linux 不支持。不能因钥匙串失败改成明文存储，也不能关闭系统安全保护、绕过上游校验或把连接凭证写入日志。
