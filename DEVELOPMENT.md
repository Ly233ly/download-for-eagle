# 开发、测试与发行

## 技术约束

- Windows 10/11；源码开发需要 Python 3.11+。
- 应用运行时代码只使用 Python 标准库；SQLite、Tk 和 Eagle HTTP 调用均不引入第三方业务依赖。
- Chrome 扩展为 Manifest V3；Eagle 只通过官方本地 Web API 访问。
- 发行后端使用 PyInstaller 6.21.0 `onedir` 打包，包含 Python 3.14.4 和 Tcl/Tk。

## 1.2.7 实现边界

1.0.0 曾按 [cat-catch 迁移总计划](docs/CAT_CATCH_MIGRATION_PLAN.md) 和 [功能对照矩阵](docs/FEATURE_PARITY_MATRIX.md) 完成研究与迁移。固定上游源码保存在 `third_party/cat-catch/source/` 作为 GPL 对应源码；1.2.7 活动浏览器载荷不再复制完整上游工具箱。YouTube MSE/SABR 页面由 `youtube-content.js` 注入主世界适配器读取播放器格式目录；通用 blob/MSE 页面从每个播放器最近内容容器提供稳定永久链接、标题与预览，同页无法关联具体内容的播放请求只进入技术区。信息流扫描使用不可饿死的合并调度，popup 会恢复扩展重载后保持打开页面的发现脚本。浏览器只负责发现和提交；无直链候选由桌面固定 yt-dlp/Deno 解析，FFmpeg 继续执行实际下载。

- 浏览器捕获层只负责发现资源、形成媒体候选组、展示选择并经认证回环接口提交计划；专用 bridge 不调用 `chrome.downloads`。
- 本机后端负责所有普通直链、分轨、HLS/DASH 下载，以及持久状态、FFmpeg/ffprobe、输出验证和现有 Eagle 导入。
- 普通直链、HLS 和 DASH 共用候选、`route=desktop` 计划与最终媒体状态机，不为单站点复制下载流程。
- 独立音视频默认使用本机 FFmpeg streamcopy；仅在容器或编码不兼容且用户明确选择时才允许转码。
- 新版不提供浏览器 FFmpeg/WASM、自动下载、录制、移动 UA、密钥面板、旧预览/直链/清单解析页或外部下载目标；唯一 popup 直接发送本机计划。
- Cookie、Authorization、Referer 等下载上下文仅按任务最小化使用；DRM 只检测和阻断，不实现绕过。
- 只有程序在 `下载中转站/临时/<planId>` 中创建的明确中间文件可以自动清理；用户原文件始终不动。
- 任何 GPL-3.0 源码复用必须先完成任务 01 的许可和来源门禁。

## 入口

- 桌面助手：`src/idm_eagle_bridge/main.py`
- IDM 接收器：`src/idm_eagle_bridge/hook.py`
- Chrome 扩展：`chrome-extension/`
- Windows 托盘宿主与启动器：`launcher/Launcher.cs`
- 一键安装器：`installer/Setup.cs`
- PyInstaller 统一入口：`launcher/assistant.pyw`；`--receive` 进入 IDM 接收模式。
- PyInstaller 公开构建配置：`packaging/DownloadTransferStation.spec`。

## 验证

把 `src` 加入 `PYTHONPATH` 后运行 `python -m unittest discover -s tests -p "test_*.py" -v`。当前 105 项 Python 测试覆盖原有后端/安装/安全能力，以及候选归组、默认隐藏播放分片、信息流内容绑定/未关联资源降噪、最新项定位、强身份与预览、SABR 全画质目录、`bytestart/byteend` 重建、跨站内容永久链接矩阵、桌面页面解析、长登录 Cookie 和临时文件清理、统一下载、任务恢复、`completed_local` 补导 Eagle、旧浏览器工具载荷删除和 GPL 来源归档。另运行 `node tests/js/test_youtube.js`、`node tests/js/test_popup_logic.js`、`node tests/js/test_candidate_presentation.js`、`node tests/js/test_auth_race.js` 与 `node tests/js/test_bilibili.js` 验证 YouTube/B 站格式目录、候选、页面链接、信息流分区和认证纯逻辑。

扩展的 JavaScript 使用 `node --check` 检查；`manifest.json` 需通过 JSON 解析。`constants.py`、`pyproject.toml`、扩展清单、弹窗版本、托盘菜单和安装器版本必须同步。

公开媒体复验使用 `packaging/Verify-PublicMedia.py`，当前证据覆盖 Apple HLS 与 B 站非 DRM DASH。安装器使用 `packaging/Test-Installer.ps1`，冻结运行时使用 `packaging/Test-FrozenRuntime.ps1`。Chrome 工具栏视觉、默认分片隐藏、最新项定位和补导动作需要最终人工点验。

## 发行结构

`release/下载中转站-1.2.7-Windows-x64/下载中转站-1.2.7` 包含：

- `一键安装.exe`：接收者唯一需要运行的入口；
- `app/`：安装器载荷，包括两个 C# 启动器、Chrome/Firefox 扩展、FFmpeg/ffprobe、yt-dlp/Deno 和独立后端；
- `source/`、`third_party/`、`licenses/` 与 `THIRD_PARTY_NOTICES.txt`：对应源码、固定 cat-catch 上游快照、构建脚本及全部第三方许可信息；
- `使用说明.txt`：非技术用户说明。

发行前必须在隔离目录验证安装器复制结果、测试注册表、独立后端健康接口、冻结版 `--receive`、一次性自动配对凭据消费、ZIP 解压完整性和 SHA-256。

更新发布还需要使用不进入 Git 的 `secrets/update-signing-private.xml` 对 `update.json` 签名，并把签名清单与完整 ZIP 一起上传到 GitHub Release。任何缺少签名、SHA-256 不符或大小不符的更新都会被客户端拒绝。

构建入口是 `powershell -ExecutionPolicy Bypass -File packaging/Build-Release.ps1`。它固定 PyInstaller 6.21.0、FFmpeg 8.1.2、yt-dlp 2026.06.09 和 Deno 2.8.1，先跑全量测试/JavaScript/清单门禁，再构建载荷、对应源码、二进制哈希清单、ZIP 和同名 SHA-256 文件。`Fetch-YouTube-Resolver.ps1` 同时校验并归档 yt-dlp 对应源码与第三方许可总表。
