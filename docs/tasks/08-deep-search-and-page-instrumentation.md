# 08 — 交付可撤销的深度搜索与隐藏资源发现

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 08。
- Evidence: 固定上游深搜/MAIN-world 运行时、命令路由和 96 文件对照测试。
- Type: AFK
User stories: US1、US5、US8

## What to build

在默认 webRequest 无法发现资源时，按标签页显式启用 MAIN world 深度搜索，观察 XHR、Fetch、Worker、WebSocket/消息、Blob、Performance 和媒体清单数据，发现隐藏的 HLS、DASH、普通媒体和疑似非 DRM Key。注入必须可撤销、可诊断并有资源上限。

## Acceptance criteria

- [x] 深度搜索默认关闭，可对当前标签临时开启或由明确规则启用，状态在 UI 中持续可见。
- [x] 能发现 XHR/Fetch 响应、Worker 消息、Blob/data URL 和内嵌 JSON/字符串中的 HLS/DASH/媒体地址。
- [x] 一次性清单内容可缓存为候选，但缓存有大小、数量和生命周期上限。
- [x] 代理函数保留原始 `this`、参数、返回值、异常和可观察的 `toString` 行为，关闭后恢复原对象。
- [x] 消息桥验证 origin、消息 schema、tab/frame 和随机 nonce，拒绝页面伪造控制消息。
- [x] 疑似 Key 只在非 DRM HLS 流程中短时展示和验证，不进入日志或诊断导出。
- [x] 性能测试记录开启/关闭时页面加载、CPU 和内存差异，超过阈值时自动停用并说明原因。
- [x] 回归测试包含 SPA 导航、跨域 iframe、多个 worker、页面覆盖 postMessage 和脚本重复注入。

## Blocked by

- 03 — 完成捕获、过滤、网站规则与会话归组对等。
- 04 — 默认展示封面、首帧、媒体信息与下载选择。
