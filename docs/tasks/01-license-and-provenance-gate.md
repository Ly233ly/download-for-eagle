# 01 — 锁定 GPL、源码来源与第三方许可门禁

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 01。
- Evidence: `LICENSE`、`COPYING.md`、`docs/UPSTREAM_PROVENANCE.md`、`third_party/cat-catch/source/` 与发行包对应源码。
- Type: HITL
User stories: US8、US10

## What to build

在迁移任何上游表达性源码或资产前，建立可审计的来源清单和发行许可决定。默认路线是让 1.0.0 组合发行满足 GPL-3.0，并保留原 MIT 代码通知；如果项目所有者拒绝该路线，则切换为 clean-room 行为重实现，禁止复制上游代码、样式、图片和翻译。

同时盘点 FFmpeg、FFmpeg/WASM、hls.js、mux.js、mpd-parser、StreamSaver、MQTT 等第三方组件的版本、许可证、源码获取方式和构建义务。

## Acceptance criteria

- [x] 记录 `cat-catch` 基线提交、文件来源、版权头、修改说明和未复用文件。
- [x] 项目所有者书面确认“GPL-3.0 组合发行”或“clean-room MIT”路线，决定写入 ADR。
- [x] 在许可决定完成前，代码审查能阻止上游源码或资产进入产品目录。
- [x] 第三方清单包含版本、哈希、许可证、主页、源码地址、构建/安装信息和发布包位置。
- [x] 发行策略说明如何同时保留原 MIT 通知和满足 GPL 对应源码要求。
- [x] 文档明确这不是法律意见，并记录需要人工复核的风险点。

## Blocked by

None - can start immediately.

## Comments

用户要求一次性全量迁移；许可门禁决定实现方式，但不缩减功能范围。
