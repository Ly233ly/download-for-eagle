# 07 — 交付 DASH/MPD 与 B 站分轨自动归组、预览和合并

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 07。
- Evidence: B 站内联 playinfo 归组、无 `__INITIAL_STATE__` 时 OG 封面回退 Node 测试，公共 B 站 DASH 分轨拉流/合并/ffprobe；工具栏视觉复验归任务 16。
- Type: AFK
User stories: US1、US2、US3、US7

## What to build

解析 DASH/MPD 和页面播放器暴露的非 DRM DASH 描述，把同一内容的视频档位、音频轨、字幕、封面和页面来源归入一个媒体候选组。针对 B 站等分轨网站，用户选择后由本机软件下载两轨、无损合并，并按选择导入 Eagle 或只保存在本地。

## Acceptance criteria

- [x] MPD 的 Period、AdaptationSet、Representation、BaseURL、SegmentTemplate/Timeline/List、初始化段和 Range 正确解析。
- [x] 视频档位展示分辨率、帧率、编码、码率和预计大小；音轨展示语言、编码、声道和码率。
- [x] 同一标签页中的 B 站视频/音频不会以两条无关联 URL 呈现，界面默认生成一个可选择的媒体候选组。
- [x] 页面标题、封面、BV/分 P 等可公开元数据用于识别内容，但 Eagle 来源仍写页面 URL。
- [x] 勾选的字幕进入下载方案，不参与音视频 mux，并以同名 sidecar 文件保存在最终目录。
- [x] 用户可预览或至少验证所选视频画面和音轨，确认页展示最终文件名、容器和组合明细。
- [x] 需要登录态的输入由扩展把白名单请求上下文提交到本机任务内存；Cookie、完整请求头和签名 URL 不持久化到数据库或日志。
- [x] 本机 FFmpeg 默认 streamcopy；输出包含恰好所选视频和音频，音画时长差异在阈值内。
- [x] MPD 或页面数据包含 Widevine/PlayReady/FairPlay 等保护信息时进入 `blocked_drm`，不尝试获取或使用解密材料。
- [x] 真实 B 站普通公开视频完成“发现—可见—选择—下载—合并—Eagle 导入”人工验收并保留证据。

## Blocked by

- 03 — 完成捕获、过滤、网站规则与会话归组对等。
- 04 — 默认展示封面、首帧、媒体信息与下载选择。
- 05 — 建立本机 FFmpeg 下载与合并引擎。
