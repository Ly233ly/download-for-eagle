# 1.2.2 发行验证

日期：2026-07-19  
范围：YouTube SABR 全画质目录、桌面准确画质解析、安全上下文、发行与现场下载。

## 根因证据

- 现场页：`https://www.youtube.com/watch?v=pIzs1qe-aBc`。
- `ytInitialPlayerResponse.streamingData` 包含 56 条 `adaptiveFormats` 和 1 条 progressive `formats`。
- 自适应条目覆盖 1440p、1080p、720p、480p、360p、240p、144p，但全部没有 `url`、`signatureCipher`；只有 itag 18 的 360p progressive 格式有直接 URL，同时响应提供 `serverAbrStreamingUrl`。因此 1.2.1 安全回退为单一 360p，UI 筛选和去重不是根因。

## 实现证据

- `catch-script/youtube.js` 把 SABR 元数据去重为一个 `resolver=youtube` 候选和完整高度目录；传统直接自适应 URL 路径保持兼容。
- popup 新增 resolver 选择模式，默认最高高度；提交字段为页面 URL、`preferredQuality` 与最小请求上下文，不提交虚假的媒体 URL 列表。
- `MediaCoordinator` 使用固定 yt-dlp 2026.06.09 与 Deno 2.8.1 解析所选准确高度和最佳音轨，再由既有 FFmpeg/FFprobe 状态机下载、合并、校验和交付。
- Cookie 不入数据库、命令行、错误或诊断；任务专用 Netscape 文件在解析进程 `finally` 中删除。自动回归验证文件路径仍在命令参数中，但 Cookie 内容不在参数中且方法返回前文件已不存在。

## 自动门禁

- Python/JavaScript/双清单回归：97 项通过（发行前完整重跑）。
- yt-dlp 2026.06.09 Windows x64 SHA-256：`3a48cb955d55c8821b60ccbdbbc6f61bc958f2f3d3b7ad5eaf3d83a543293a27`。
- Deno 2.8.1 Windows x64 ZIP SHA-256：`5fb5bac71f609fb91ec8960fb290885aadc27eeb22f07a8eca0c3db6be38b11a`。
- 冻结运行时通过：`version=1.2.2`、schema 5、协议 1、`mediaReady=true`、`youtubeResolverReady=true`、`desktop_ffmpeg`，yt-dlp 与 Deno 均为发行包内固定版本。
- 隔离安装器通过全新安装、更新、注入失败回滚与卸载四条路径；当前电脑覆盖安装完成，在线 `/health` 返回 1.2.2 且 YouTube resolver 就绪。
- 用发行包解析同一公开视频时，未携带浏览器会话的独立命令被 YouTube 反机器人门禁拒绝；这条结果不算下载通过，也验证了扩展必须把当前标签页的最小 Cookie/UA/Referer 上下文临时交给桌面解析器。直接读取正在运行的 Chrome Cookie 数据库同样因文件锁失败，程序不会绕过浏览器去抓取该数据库。
- Chrome 受保护的扩展管理页不能由自动化可靠操作；现场画质目录和真实 1440p 下载保留为用户手动重载扩展后的唯一人工闭环，不以未执行的长视频下载冒充通过。

## 发行物

- 目录：`release/下载中转站-1.2.2-Windows-x64/下载中转站-1.2.2`。
- ZIP：`release/下载中转站-1.2.2-Windows-x64/下载中转站-1.2.2-Windows-x64.zip`。
- ZIP 字节数：`164,373,275`。
- ZIP SHA-256：`7be6eed0ace15cced6d05b28ddf75cfe189a7d9ad3e9e6e73d56dc98c2a81864`。
