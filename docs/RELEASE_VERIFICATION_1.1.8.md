# 下载中转站 1.1.8 验证报告

验证日期：2026-07-19  
状态：认证读取 POST、完整自动门禁、发行构建、当前电脑覆盖安装和真实持久配对通过；抖音下载内容与所选预览错配，A136 未通过，由 1.1.9 接替。

## 1.1.7 实机失败证据

- 六位码配对 POST 成功，服务端轮换配对码并生成新令牌。
- Chrome 最后一个非空令牌与服务端当前哈希完全匹配，下一条状态把令牌清空。
- 直接请求证明正确 Origin + 正确令牌的 GET 为 200，缺少 Origin 的 GET 为 401。
- 结论：真实失败点是配对后的受认证 GET 请求头兼容，不是配对码、端口、扩展 ID、令牌内容或状态并发覆盖。

## 修复与回归

- 健康、任务列表、任务详情和预览统一使用 `eagleBridgeRead` JSON POST。
- 服务端 POST 路由继续验证扩展 Origin，并从请求体读取随机令牌回退。
- 新回归实现前得到 HTTP 404 与扩展断言失败，实现后通过。
- 全量 unittest 共 90 项通过；扩展 JavaScript 语法、Chrome/Firefox 双清单和认证竞态 Node 回归均包含在门禁内。

## 自动与发行门禁

- 冻结运行时通过：`version=1.1.8`、`extensionProtocol=1`、`databaseSchema=5`、`mediaReady=true`、`downloadEngine=desktop_ffmpeg`，IDM 接收器退出码 0 且生成 1 个任务。
- 隔离安装器的新装、升级、注入失败回滚和卸载全部通过。
- 当前电脑已覆盖安装；在线 `/health` 返回 1.1.8、协议 1、schema 5、`desktop_ffmpeg` 和媒体工具就绪。
- 当前安装的认证 POST `/api/media/health` 返回 200。
- 安装目录 `manifest.json`、`background.js`、`eagle-bridge.js`、`eagle-bridge-ui.js`、`eagle-bridge-auth-logic.js` 与仓库源码 SHA-256 全部一致。

## Chrome 实机闭环

- 重载后顶部保持“已连接”，认证 POST 与任务同步正常。
- 抖音真实任务达到 `imported/100` 且目录存在，但所选卡片为 45:13 视频，最终文件 FFprobe 只有 708.141475 秒且首帧为另一视频。
- 计划数据库中的声明时长为 2713.034 秒，证明扩展在计划创建前把当前播放器视觉身份绑定给了后台预加载 URL。
- 结论：配对/任务状态闭环通过，内容身份闭环失败；1.1.8 不继续推广。

## 发行物

- ZIP：`release/下载中转站-1.1.8-Windows-x64/下载中转站-1.1.8-Windows-x64.zip`
- 大小：93,372,384 字节
- SHA-256：`d0d1ae902a63e1a4155179561a87d2e074586627158f0be3ec16cdf0aac15571`
- PyInstaller：6.21.0
- FFmpeg/ffprobe：8.1.2
