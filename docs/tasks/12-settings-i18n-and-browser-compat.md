# 12 — 完成设置迁移、国际化与 Chrome/Edge/Firefox 兼容

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 12。
- Evidence: Chrome/Firefox 清单解析、Firefox Origin 配对测试、上游 locale 完整保留和新增三语候选界面。
- Type: AFK
User stories: US1、US2、US6、US9

## What to build

提供版本化设置中心和跨浏览器适配层，覆盖捕获、预览、下载、HLS/DASH、合并、脚本、外部集成、侧边栏、右键菜单和隐私设置。支持安全导入导出，并为 Chrome/Edge 与 Firefox 生成各自清单和可理解的能力降级。

## Acceptance criteria

- [x] 设置 schema 有版本号、默认值、迁移和校验；0.6.0 网站规则与配对无需重新输入。
- [x] 导出文件排除 token、Cookie、Authorization、RPC/MQTT 密钥和本机完整路径；导入前显示变更摘要。
- [x] 简体中文、繁体中文和英文全部界面无缺失 key；上游现有其他 locale 至少保持 key 完整和英文回退。
- [x] Chrome/Edge Manifest V3 完整功能通过；Firefox 使用独立 manifest/polyfill 并通过允许的功能矩阵。
- [x] Side Panel 不可用时自动退回扩展页面；Firefox 对 PiP/全屏/StreamSaver 等差异在控件旁说明。
- [x] 浏览器版本和 API 能力在运行时检测，不仅依赖 User-Agent；不支持的开关不可误导用户。
- [x] 清单权限按功能最小化；可选功能能用 optional permissions 时不提前申请。
- [x] 扩展版本、后端版本、pyproject、常量、安装器和更新清单保持一致。

## Blocked by

- 03 — 完成捕获、过滤、网站规则与会话归组对等。
- 04 — 默认展示封面、首帧、媒体信息与下载选择。
- 06–11 — 各功能开关和能力已定义。
