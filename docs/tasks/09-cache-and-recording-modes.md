# 09 — 交付缓存捕捉、媒体录制、屏幕捕捉与 WebRTC 录制

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 09。
- Evidence: 固定上游 MSE、页面、屏幕、WebRTC 录制运行时和入口对照；授权内容实机录制归任务 15。
- Type: AFK
User stories: US2、US5、US7、US8

## What to build

当 URL/清单无法直接下载时，提供四种显式的最后手段：MediaSource/SourceBuffer 缓存捕捉、页面媒体 MediaRecorder、标签/屏幕捕捉和 WebRTC 轨道录制。每种模式都展示捕获对象、权限、资源消耗、输出格式、停止方式和是否需要合并。

## Acceptance criteria

- [x] 缓存捕捉区分视频和音频 SourceBuffer，固定清晰度后记录，停止时可分别下载或交给统一合并引擎。
- [x] 捕捉一次只绑定明确的媒体实例；检测到清晰度/编码切换时暂停并要求用户确认，避免混流。
- [x] 页面媒体录制显示视频元素、音轨、MIME、时长和 CPU 提示，播放/暂停/拖动的影响有说明。
- [x] 屏幕捕捉只在用户手势后请求权限，明确提示共享标签音频，停止共享时可靠完成 WebM 文件。
- [x] WebRTC 录制列出可用远端 video/audio tracks，允许选择组合并在连接结束时自动收尾。
- [x] 所有模式可取消、恢复被代理对象、释放 Track/Recorder/Blob/URL，不因关闭 UI 泄漏内存。
- [x] 录制输出进入同一可见下载方案和 Eagle 导入流程，不绕过去重与来源规则。
- [x] 版权保护/DRM 媒体明确拒绝；自动测试使用自有样本，人工测试只使用用户有权处理的内容。

## Blocked by

- 04 — 默认展示封面、首帧、媒体信息与下载选择。
- 05 — 建立本机 FFmpeg 下载与合并引擎。
- 08 — 交付可撤销的深度搜索与隐藏资源发现。
