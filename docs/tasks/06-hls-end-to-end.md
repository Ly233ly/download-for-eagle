# 06 — 交付 HLS/M3U8 解析、下载、录制、解密与合并

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 06。
- Evidence: 上游 HLS 运行时对照、真实 AES-128 合成样本、Apple 公共 HLS 拉流与 ffprobe 结果。
- Type: AFK
User stories: US1、US2、US4、US7

## What to build

从捕获到 Eagle 完整支持 HLS：解析主/子清单和媒体组，展示清晰度、音轨和字幕，按范围或直播模式下载分片，处理 BYTERANGE、EXT-X-MAP、重试和非 DRM AES-128-CBC，最后通过统一合并引擎生成并导入最终文件。

## Acceptance criteria

- [x] 主清单的分辨率、码率、编码、音频组和字幕组可见且可选择。
- [x] VOD 分片支持并发上限、指数退避、失败重试、Range、EXT-X-MAP、相对 URL 和查询参数继承。
- [x] 用户可按序号或时间选择片段范围，并在下载前看到预计时长和大小。
- [x] 直播清单可持续刷新、停止和恢复，长任务使用流式/组件文件，不无限占用内存。
- [x] AES-128-CBC 的清单 Key、自定义 Hex/Base64/文件 Key 可验证并短时使用；其他加密标记为不支持或 DRM 阻断。
- [x] 支持数据预处理、只要音频、另存为、自动关闭、切片 URL 导出和请求参数/Referer 设置。
- [x] 输出经 FFmpeg/ffprobe 校验后进入现有去重和 Eagle 导入，失败可从已校验分片恢复。
- [x] 自动测试和固定样本覆盖普通 TS、fMP4、BYTERANGE、EXT-X-MAP、AES-128、直播更新及损坏分片。

## Blocked by

- 03 — 完成捕获、过滤、网站规则与会话归组对等。
- 04 — 默认展示封面、首帧、媒体信息与下载选择。
- 05 — 建立本机 FFmpeg 下载与合并引擎。
