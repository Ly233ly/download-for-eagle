# 开发、测试与发行

## 技术约束

- Windows 10/11；源码开发需要 Python 3.11+。
- 应用运行时代码只使用 Python 标准库；SQLite、Tk 和 Eagle HTTP 调用均不引入第三方业务依赖。
- Chrome 扩展为 Manifest V3；Eagle 只通过官方本地 Web API 访问。
- 发行后端使用 PyInstaller 6.21.0 `onedir` 打包，包含 Python 3.14.4 和 Tcl/Tk。

## 入口

- 桌面助手：`src/idm_eagle_bridge/main.py`
- IDM 接收器：`src/idm_eagle_bridge/hook.py`
- Chrome 扩展：`chrome-extension/`
- Windows 托盘宿主与启动器：`launcher/Launcher.cs`
- 一键安装器：`installer/Setup.cs`
- PyInstaller 统一入口：`launcher/assistant.pyw`；`--receive` 进入 IDM 接收模式。
- PyInstaller 公开构建配置：`packaging/DownloadTransferStation.spec`。

## 验证

把 `src` 加入 `PYTHONPATH` 后运行 `unittest discover -s tests -v`。测试覆盖无来源导入、来源匹配、同页重复来源合并、网站关闭、重复内容、Eagle 离线与等待上限、旧数据迁移、自动重试竞态与次数上限、普通配对、安装器自动配对、托盘控制、URL 清理、助手自启动、签名更新校验和完整端到端流程。

扩展的 JavaScript 使用 `node --check` 检查；`manifest.json` 需通过 JSON 解析。`constants.py`、`pyproject.toml`、扩展清单、弹窗版本、托盘菜单和安装器版本必须同步。

## 发行结构

`release/下载中转站-0.6.0` 包含：

- `一键安装.exe`：接收者唯一需要运行的入口；
- `app/`：安装器载荷，包括两个 C# 启动器、Chrome 扩展和独立后端；
- `licenses/` 与 `THIRD_PARTY_NOTICES.txt`：Python、PyInstaller 和 Tcl/Tk 许可信息；
- `使用说明.txt`：非技术用户说明。

发行前必须在隔离目录验证安装器复制结果、测试注册表、独立后端健康接口、冻结版 `--receive`、一次性自动配对凭据消费、ZIP 解压完整性和 SHA-256。

更新发布还需要使用不进入 Git 的 `secrets/update-signing-private.xml` 对 `update.json` 签名，并把签名清单与完整 ZIP 一起上传到 GitHub Release。任何缺少签名、SHA-256 不符或大小不符的更新都会被客户端拒绝。
