# 03 — 完成捕获、过滤、网站规则与会话归组对等

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 03。
- Evidence: `tests/test_upstream_parity.py`、`tests/test_extension.py` 与 schema 5 媒体模型测试。
- Type: AFK
User stories: US1、US2、US8

## What to build

把 URL 后缀、MIME、大小表达式、正则、请求/响应阶段、黑白名单和强制屏蔽统一到捕获会话与媒体候选组。扩展必须解释每条候选为何被捕获或过滤，并与现有网站启停/子域名规则形成单一优先级体系。

## Acceptance criteria

- [x] 支持后缀和 MIME 通配匹配，并支持 `> >= < <= = !=`、范围及 B/KB/MB/GB。
- [x] 正则规则保存前编译验证，运行时有耗时/数量保护，错误规则不能拖垮页面。
- [x] URL 黑名单、白名单、强制屏蔽、网站规则和单次忽略有唯一且文档化的优先级。
- [x] 主文档导航创建新的捕获会话；同页重复请求去重但不丢失不同清晰度或音轨。
- [x] 候选记录捕获原因、tab/frame、导航周期、类型和最小必要元数据。
- [x] 关闭网站时不运行深度脚本、不持久化候选，并保持现有明确跳过行为。
- [x] 自动测试覆盖重定向、iframe、同 URL 不同 Range、重复请求和规则冲突。

## Blocked by

- 02 — 打通“可见普通媒体 → 下载 → Eagle”首条纵向链路。
