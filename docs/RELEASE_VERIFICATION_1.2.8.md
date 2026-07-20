# 1.2.8 通用页面分轨格式兼容验证报告

日期：2026-07-20

## 结论

1.2.8 已修复通用页面解析把独立音轨固定限制为 M4A 的问题。格式选择继续优先 MP4 视频+M4A 音频，同时接受 MP4 视频+MP4 音频，并按合并 MP4、MP4 视频+任意音频和通用最佳格式逐级回退。实现不包含 Pinterest 或其他站点域名分支。

现场 Pinterest Pin `72690981480504869` 在 yt-dlp 2026.06.09 中公开五档 H.264 HLS 视频轨和一条扩展名为 MP4 的独立音频轨，没有合并格式。1.2.7 因选择器只接受 `bestaudio[ext=m4a]` 而在零下载字节时报 `Requested format is not available`。

## 现场媒体闭环

- 新选择器命中 `V_HLSV3_MOBILE-1633+V_HLSV3_MOBILE-audio1-1`。
- FFmpeg 8.1.2 使用两个解析地址执行 streamcopy 成功。
- FFprobe 确认输出包含 720×900 H.264 视频流和 AAC 音频流。
- 输出时长 12.194467 秒，文件大小 2,464,356 字节。
- 现场临时输出只用于验证，验证后从项目缓存清理；不导入 Eagle，不保留签名媒体地址。

## 自动与发行验证

- Python：105 项全部通过，包含页面解析格式优先级、MP4 音轨兼容、临时 Cookie 清理和敏感上下文不落盘。
- Node：5 组候选、内容展示、认证和 B 站/YouTube 逻辑回归通过。
- 扩展：17 个 JavaScript 文件通过语法检查；Chrome/Firefox 双清单均为 1.2.8。
- 冻结运行时：健康版本 1.2.8、schema 5、扩展协议 1、`desktop_ffmpeg`、FFmpeg/ffprobe、yt-dlp/Deno 和 IDM 接收模式全部通过；证据为 `.scratch/frozen-runtime-1.2.8-evidence.json`。
- 隔离安装器：全新安装、覆盖更新、强制失败回滚和卸载恢复全部通过；证据为 `.scratch/installer-1.2.8-evidence.json`。
- 当前电脑：覆盖更新成功；在线健康返回 1.2.8、schema 5、协议 1、`mediaReady=true`、`youtubeResolverReady=true`，安装目录扩展清单为 1.2.8。

## 发行物

- 目录：`release/下载中转站-1.2.8-Windows-x64/下载中转站-1.2.8`
- ZIP：`release/下载中转站-1.2.8-Windows-x64/下载中转站-1.2.8-Windows-x64.zip`
- 大小：165,416,683 字节
- SHA-256：`2447b5c60216099954d2c2cda9fe7de81f3f4e5418d0d6d9fc55f86b3ef730d5`
- 固定工具：PyInstaller 6.21.0、FFmpeg 8.1.2、yt-dlp 2026.06.09、Deno 2.8.1

## 用户复验

旧失败任务的完整解析上下文不会跨软件重启保存。回到原 Pinterest 页面刷新并重新创建任务即可使用 1.2.8 选择器；不应继续重试 1.2.7 创建的旧任务。
