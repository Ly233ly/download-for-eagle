# 17 本机统一下载与桌面任务 UI

- Status: `done`
- Labels: `ready-for-human`
- Acceptance: A25、A48、A57、A60、A67、A73、A75、A80–A84、A99–A112
- Evidence: `tests/test_media.py`、`tests/test_extension.py`、`tests/js/test_popup_logic.js`、全量 unittest 81/81、schema 5 冻结/安装证据和当前电脑桌面 UI 实机检查

## 目标

扩展只负责发现、归组、展示和提交媒体方案。普通直链、分离音视频、HLS/DASH、“下载并导入”和“仅下载”全部由本机软件下载；删除本项目新增的 Chrome 组件下载、DNR 请求头规则、完成/失败路径回传和浏览器进度聚合代码。

桌面软件成为任务事实源，持续展示用户正在下载的内容和从下载到 Eagle 的完整阶段，窗口关闭再打开不得丢任务。

## 已完成实现

- `eagle-bridge.js` 的媒体方案固定为 `route=desktop`，所有选择都经认证回环接口发送最小请求上下文；专用 bridge 不再调用 `chrome.downloads`。
- 删除 `eagle-bridge-download-logic.js`、`component_ready/component_failed`、`/api/media/component`、`/api/media/fail`、浏览器下载记录恢复与 `planDownloads` 聚合。
- “仅下载”创建 `import_to_eagle=0` 方案，完成为 `completed_local/100`，不创建 Eagle job。
- 本机 FFmpeg 统一处理普通直链、受保护分轨和 HLS/DASH；字幕由本机软件下载为 sidecar，ffprobe 校验后才交付。
- 任务记录下载字节、预计总量、阶段说明、最终路径和本机生成的视频预览；Eagle 导入前保持 90%，关联 job 成功后才进入 `imported/100`。
- schema 5 删除旧 `component_files` 表。旧活动方案因签名 URL 从未落盘而标记 `download_context_expired`，要求回来源页重新创建。
- 桌面窗口分为“媒体下载”和“IDM 导入记录”；前者提供标题、来源、进度、错误、预览、停止、重试、打开文件与来源。
- 可见扩展 UI 移除浏览器 FFmpeg、完整浏览器下载器、自动下载和外部下载目标入口，避免绕开统一状态机。
- 删除旧自动下载快捷键、右键菜单、标签状态和捕获后自动执行逻辑，并取消捕获后自动 send2local；旧配置不能在不可见状态下绕开软件。
- 独立直链页改为本机任务表单；预览页的下载/合并动作和 HLS/DASH 解析页的最终下载按钮都提交认证 `createPlan`，解析器原浏览器/在线下载控件隐藏。

## 验收标准

1. 普通 MP4、受 Referer/User-Agent 保护的视频/音频分轨和 AES-128 HLS 均由本机软件完成并通过 ffprobe。
2. bridge 源码不包含 `chrome.downloads`、组件路径回传或旧浏览器路由；普通候选和清单候选都返回 `desktop`。
3. 下载进度、阶段、错误与最终 Eagle 状态写入 SQLite；扩展和桌面窗口读取同一 `plans`。
4. 完整媒体 URL、Cookie、Authorization 和请求头不写数据库或扩展持久存储；同次运行可重试，进程重启后明确要求重建。
5. “仅下载”不进入 Eagle；“下载并导入”只有在下载、合并和校验成功后才创建导入 job。
6. `blob:` 地址明确阻断且不回退浏览器；DRM 继续只识别和阻断。
7. 不移动、删除或修改用户原文件；只处理本程序任务专属临时目录及新生成的最终文件/预览。

## 已完成发行收口

- schema 5 新载荷已构建并覆盖安装；公共健康门返回 `downloadEngine=desktop_ffmpeg`，关键文件哈希一致。
- 桌面“媒体下载 / IDM 导入记录”双标签已实机打开，历史任务在重启与标签切换后保留。
- Chrome popup 的最终视觉截图和真实 Eagle 离线→上线补导入仍是跨任务人工点验，不影响任务 17 的代码与发行门完成状态。
