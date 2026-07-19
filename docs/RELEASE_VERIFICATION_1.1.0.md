# 下载中转站 1.1.0 验证报告

更新时间：2026-07-18

## 结论

方案 2 单界面、本机统一下载、schema 5、桌面媒体任务页和安装健康门已组成新的 1.1.0 发行候选，并覆盖安装到当前电脑。普通直链、受保护分轨、AES-128 HLS、“仅下载”和 Eagle 导入分别有真实 FFmpeg/HTTP 自动回归；冻结运行时、隔离安装、覆盖升级、故障回滚、卸载、安装文件哈希和桌面 UI 实机检查均通过。

Chrome 专用控制连接在本次验收中不可用，因此没有伪造工具栏 popup 截图。A101 的最终视觉对照以及缓存/录制的真实授权内容点验仍保留为人工门禁，不影响本机统一下载代码、安装和自动证据的通过结论。

## 本次下载链路变化

- 扩展只负责发现、归组、预览和提交；普通直链、分离音视频、HLS/DASH、“下载并导入”和“仅下载”全部创建 `route=desktop` 计划。
- 删除专用 bridge 的 Chrome 下载记录、DNR 请求头规则、组件完成/失败回传、浏览器进度聚合与 `/api/media/component`、`/api/media/fail`。
- 删除旧自动下载快捷键、右键项、标签状态、捕获后 Chrome 下载和捕获后自动 send2local；popup、预览页、独立直链页及清单解析页的可达下载动作统一提交本机计划。
- “仅下载”以 `completed_local/100` 结束且不创建 Eagle job；导入任务在媒体验证完成后保持 90%，关联 job 成功后才进入 `imported/100`。
- 完整签名 URL 和白名单请求头只存在软件任务内存；数据库只保存脱敏地址。进程重启后未完成任务明确提示回来源页重建。
- `blob:` 与 DRM 在创建任务前明确阻断，不静默恢复浏览器路线。

## 自动验证

- 81 项 Python 测试通过，包含旧 IDM/Eagle 工作流、Eagle 4 新旧健康接口、API 认证、schema 5 迁移、本机任务、敏感上下文、字幕 sidecar、停止/重试、普通直链、受 Referer/User-Agent 保护的双轨下载、AES-128 HLS、ffprobe、扩展结构、跨站内容图、首次快照、统一计数和固定上游运行时对照。
- `tests/js/test_popup_logic.js` 通过：普通媒体和清单都固定为 `desktop`；“仅下载”也要求软件在线；任务阶段、字节、完成/错误状态映射有断言。
- 全部扩展 JavaScript 通过 `node --check`；Chrome/Firefox 清单可解析且版本均为 1.1.0。
- 发行脚本再次执行同一 81 项测试后构建；`git diff --check` 无空白错误。

## 冻结运行时与安装器

- [`frozen-runtime-1.1.0-schema5.json`](evidence/frozen-runtime-1.1.0-schema5.json)：冻结后台报告 `version=1.1.0`、扩展协议 1、schema 5、`downloadEngine=desktop_ffmpeg`、媒体工具就绪；冻结 `--receive` 只创建一个任务。
- [`installer-1.1.0-schema5.json`](evidence/installer-1.1.0-schema5.json)：隔离全新安装、成功覆盖、故障注入回滚和卸载全部通过；扩展 1.1.0、FFmpeg/ffprobe 和配对 bootstrap 均存在。
- 安装器健康门同步校验 schema 5 和 `desktop_ffmpeg`。验证过程曾发现公共 `/health` 未透出下载引擎；修复并增加回归断言后重新冻结、重新验证。
- 证据使用相对或占位路径；发行源码包不包含开发机用户目录、运行数据、配对令牌或任务数据库。

## 当前电脑覆盖安装

- [`installed-1.1.0.json`](evidence/installed-1.1.0.json)：当前电脑 `/health` 返回 `version=1.1.0`、`databaseSchema=5`、`extensionProtocol=1`、`downloadEngine=desktop_ffmpeg`、`mediaReady=true`。
- 发布载荷与安装目录的启动器、IDM hook、冻结后台和四个关键扩展文件 SHA-256 逐项一致。
- Eagle 4.0.0 Build 20250917 实际连接成功；V2 健康接口不可用时继续使用官方 V1 回退。
- 桌面窗口实际显示“媒体下载 / IDM 导入记录”双标签；已有媒体任务在覆盖安装、进程重启和标签切换后仍保留，已导入任务显示 100%，来源和输出路径可见。

## 发行物

- 路径：`release/下载中转站-1.1.0-Windows-x64/下载中转站-1.1.0-Windows-x64.zip`
- 大小与 SHA-256 以同目录构建后生成的 `.zip.sha256.txt` 为准。哈希不写回 ZIP 内的对应源码，以避免包对自身哈希产生不可自洽循环。
- 包含 Windows 启动器、冻结后台、Chrome/Edge/Firefox 扩展、FFmpeg/ffprobe、许可证、第三方通知、固定上游快照和对应源码。

## 尚需人工确认

- [`design-qa.md`](../design-qa.md) 的 Chrome 工具栏 popup 最终视觉对照仍为 `blocked`：需在 Chrome 重新加载解压扩展后，截取真实 660×574 popup，与选定方案 2 检查字体、间距、颜色、内容图、文案、滚动和焦点。
- 用自己有权处理的内容点验一次缓存捕获或录制模式；不把自动化测试生成的媒体当作授权内容证据。
