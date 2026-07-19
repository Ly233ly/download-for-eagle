# 10 — 收敛下载路由与保留 IDM 导入兼容

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 10。
- Evidence: 固定 `desktop` 媒体计划、无浏览器/外部目标可见入口、现有 IDM → Eagle 端到端回归。
- Type: AFK
User stories: US6、US7、US8

## What to build

媒体候选的主下载路由固定为本机软件；扩展不再提供 Chrome Downloads、在线 FFmpeg、Aria2、N_m3u8DL-RE、自定义调用、send2local 或 MQTT 的可见下载入口。IDM hook 继续作为软件原有的“外部已下载文件导入 Eagle”入口，与媒体计划下载状态机相互独立。

## Acceptance criteria

- [x] 下载前展示本机处理、输出名、媒体类型、清晰度/音轨、预览和最终是否导入 Eagle。
- [x] 普通直链、受保护直链、分离音视频和 HLS/DASH 都创建 `route=desktop` 计划。
- [x] “仅下载”使用本机软件并以 `completed_local` 结束，不创建 Eagle job。
- [x] 浏览器下载 ID、组件完成/失败回传、外部目标和在线处理动作不进入新 UI 或本机协议。
- [x] Cookie、Authorization 和完整签名 URL 不写入数据库、日志或诊断；软件重启后要求从来源页重建任务。
- [x] 每个任务都有成功、失败、停止、内存内重试和重启后过期测试，且最多创建一个 Eagle 导入任务。

## Blocked by

- 02 — 打通“可见普通媒体 → 下载 → Eagle”首条纵向链路。
- 03 — 完成捕获、过滤、网站规则与会话归组对等。
