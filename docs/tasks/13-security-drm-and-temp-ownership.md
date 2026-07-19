# 13 — 完成隐私、DRM、消息边界和临时文件归属硬化

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 13。
- Evidence: DRM 前置阻断、内存请求头、CRLF 注入拒绝、签名 URL 脱敏、重启上下文失效、owned-temp 与 loopback/Origin 测试。
- Type: AFK
User stories: US8、US9

## What to build

对完整媒体捕获/下载链做威胁建模和安全硬化：浏览器页面与扩展消息、本机 API、敏感请求信息、本机 FFmpeg 参数、DRM 检测和临时中间文件清理。媒体下载不再分流到浏览器或第三方处理服务。

## Acceptance criteria

- [x] 本机 API 只监听 loopback，验证 token、Origin、方法、Content-Type、body 大小和 schema，并限制请求频率。
- [x] 页面—content script—service worker 消息校验 origin、nonce、tab/frame 和动作白名单，页面不能伪造下载或本机命令。
- [x] Cookie、Authorization、完整请求头、媒体字节和网页正文默认不入库、不入日志、不进诊断；例外有字段白名单、TTL 和擦除测试。
- [x] 第三方在线服务、Aria2、MQTT、send2local、自定义调用和浏览器下载不进入新版可见下载流程。
- [x] URL、文件名、组件路径、协议模板和 FFmpeg 参数经过注入、路径穿越、SSRF 和 shell 元字符测试。
- [x] Widevine、PlayReady、FairPlay、SAMPLE-AES 等进入 `blocked_drm`，不捕获许可证、不导出 PSSH 作为解密功能、不提供绕过。
- [x] 只有程序专用临时根内、带任务归属的中间文件可以自动删除；最终下载文件与用户文件永不自动删除，路径越界时拒绝清理。
- [x] 隐身窗口、多个浏览器配置和多扩展 ID 的数据隔离经过测试。
- [x] 安全审查结果同步 SECURITY、PRD、验收、安装说明和第三方通知。

## Blocked by

- 02–12 — 全部数据流和功能入口可供审查。
