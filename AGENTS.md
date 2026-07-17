# 项目协作规则

- 这是 Windows 本机工具；业务运行时代码保持 Python 3.11+ 标准库零第三方依赖，发行版用 PyInstaller 自带解释器与 Tcl/Tk。
- 核心行为：IDM 视频无来源也导入；有可靠来源才写入 Eagle，禁止猜测网址。
- 网站关闭依赖 Chrome 明确的 `site_disabled`/`ignore` 事件，不能从无来源文件反推网站。
- 不移动、删除或修改下载文件，不直接修改 Eagle `.library` 内容。
- Eagle 导入与来源更新只调用官方本地 Web API。
- IDM hook 必须快速完成：只入队、合并活动任务和发送唤醒信号，不做哈希或网络调用。
- 系统托盘必须由 `launcher/Launcher.cs` 的 Windows Forms 宿主管理；禁止在 Python 中用 `ctypes` 替换窗口过程。
- 数据库结构迁移使用 SQLite `PRAGMA user_version`；不得用启动时反复执行的大范围更新代替版本迁移。
- `pyproject.toml`、`src/idm_eagle_bridge/constants.py` 和 `chrome-extension/manifest.json` 的版本必须一致。
- 安装器不得覆盖 IDM 已有的其他杀毒软件路径；备份、恢复和删除目录都必须校验归属。
- 发行包不得包含开发机 `data`、配对令牌、网站规则、任务记录或用户路径。
- 修改流程后同步 README、ACCEPTANCE、TASKS、STATUS 和相关 docs，完成项不能保留为未来计划。
- 自动测试入口见 `DEVELOPMENT.md`；提交前运行全部 unittest、扩展 JS 语法检查和清单 JSON 解析。
- 深入文档：架构见 `docs/ARCHITECTURE.md`，决策边界见 `docs/DECISIONS.md`，安装运维见 `docs/INSTALLATION_AND_ROLLBACK.md`。
