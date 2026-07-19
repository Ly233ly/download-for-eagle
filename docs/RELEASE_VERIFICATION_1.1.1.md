# 下载中转站 1.1.1 验证报告

日期：2026-07-19  
状态：发行构建与当前电脑覆盖安装已通过；仅 Chrome 工具栏 popup 最终视觉对照待人工点验

## 目标

本补丁解决三个相互关联的问题：候选图不是视频内容、嵌入播放器播放时签名 URL/分片持续制造卡片、旧隐藏 popup 运行时让入口和状态重复。所有远程媒体下载仍固定提交本机 `desktop` 计划。

## 实现证据

- `content-script.js` 优先从 `video` canvas 抓取当前 JPEG 帧，并返回稳定播放器键与可见矩形；跨域 canvas 失败时，`background.js` 使用当前活动标签页截图裁剪播放器区域。
- 帧只保存在 `mediaFramePreviewCache` 与 popup 的 `framePreviews`，不进入 `MediaData`、任务 API、SQLite 或 Eagle。
- `eagle-bridge-ui-logic.js` 在组内折叠相同媒体路径的签名 URL；清单/完整媒体存在时删除普通 `.m4s`/`.ts` 分片，仅分片组阻止提交。
- `popup.html` 只加载新版 UI；上游 `js/popup.js`、`js/media-control.js` 和隐藏 DOM 删除。高级捕获集中在设置，主导航只有媒体与任务。
- 安装器在复制新载荷后定点删除旧版本可能遗留的根 `background.js`、`js/popup.js` 和 `js/media-control.js`，避免覆盖安装继续运行废弃代码。
- Chrome/Firefox 清单删除旧右键菜单权限与非主动作快捷命令；后台相应旁路和设置项删除。

## 自动验证

- `python -m unittest discover -s tests -p "test_*.py" -v`：83 项。
- `node tests/js/test_popup_logic.js`：覆盖 Behance 式同播放器签名轮换、清单 + 分片和仅分片阻断。
- `node tests/js/test_candidate_presentation.js`：覆盖安全帧 data URL 与稳定视觉键。
- 所有扩展 JavaScript 通过 `node --check`；Chrome/Firefox 清单通过 JSON 解析且版本为 1.1.1。

## 实机验证

- 来源页：Behance `Song of the Stars - TXT`，播放状态截图保存在 `.scratch/ui-audit-2026-07-19/`。
- 冻结后台独立启动通过：`version=1.1.1`、`extensionProtocol=1`、`databaseSchema=5`、`downloadEngine=desktop_ffmpeg`、`mediaReady=true`，IDM 接收器退出码为 0，FFmpeg/ffprobe 均已随包提供。
- 当前电脑已通过 `--install-silent` 覆盖安装到 `%LOCALAPPDATA%\IDM-Eagle自动导入助手`；安装器正常退出，健康端点与扩展清单均报告 1.1.1。
- 覆盖安装后根 `chrome-extension/background.js`、`chrome-extension/js/popup.js`、`chrome-extension/js/media-control.js` 均不存在，确认旧运行时不是只从源码移除。
- Chrome 扩展内部 URL 受控制工具安全策略限制，不能用替代浏览器或内部 URL 绕过；工具栏 popup 的最终真实截图需在重新加载 1.1.1 后从用户当前 Chrome 获取。

## 发布物

- 目录：`release/下载中转站-1.1.1-Windows-x64/下载中转站-1.1.1`
- ZIP：`release/下载中转站-1.1.1-Windows-x64/下载中转站-1.1.1-Windows-x64.zip`
- 大小：93,305,651 字节
- SHA-256：`2c5650163ebb6b758486f28ef7e34b1640fcb3205b95673e109e7d6f4fdecc14`
- PyInstaller：6.21.0；FFmpeg：8.1.2。

发行物、冻结运行时和覆盖安装已签字；GitHub Release 上传仍由项目所有者决定。A101 的 Chrome popup 同视口视觉证据不由自动测试代替。
