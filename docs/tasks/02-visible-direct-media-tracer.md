# 02 — 打通“可见普通媒体 → 下载 → Eagle”首条纵向链路

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 02。
- Evidence: `chrome-extension/js/eagle-bridge-ui.js`、`js/eagle-bridge.js`、`tests/test_end_to_end.py`、`tests/test_media.py`。
- Type: AFK
User stories: US1、US2、US7

## What to build

以一个普通 MP4/音频资源为 tracer bullet：扩展捕获媒体和页面元数据，创建媒体候选组，在默认界面展示标题、封面/首帧、时长、类型、大小和输出名；用户确认后提交本机软件，完成文件按选择保存在本地或进入现有持久队列并自动导入 Eagle。

该切片同时建立版本化本机 API、数据库迁移、候选/下载方案最小模型、状态反馈和旧来源事件兼容层。

## Acceptance criteria

- [x] 0.6.0 数据库升级后新增候选模型，旧任务、规则、配对和指纹完全保留。
- [x] 当前页普通 MP4/音频在默认界面以内容卡片显示，不以裸 URL 作为主标题。
- [x] 卡片至少展示页面标题、站点、媒体类型、已知大小、最终文件名和封面/回退原因。
- [x] 用户确认前不自动下载；确认页显示下载方式和“完成后导入 Eagle”。
- [x] 本机媒体计划验证完成后最多生成一个最终导入任务；“仅下载”不生成导入任务。
- [x] Eagle 离线、重复内容、取消下载和文件不存在沿用现有可恢复状态。
- [x] 自动测试覆盖 API 认证、schema 迁移、候选创建、下载完成和 Eagle 导入整链路。

## Blocked by

- 01 — 锁定 GPL、源码来源与第三方许可门禁。
