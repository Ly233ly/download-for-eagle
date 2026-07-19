# 14 — 把扩展、FFmpeg、许可和数据迁移纳入安装更新回滚

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 14。
- Evidence: `packaging/Build-Release.ps1`、`Test-Installer.ps1`、`Test-FrozenRuntime.ps1` 与正式升级前后数据库快照。
- Type: AFK
User stories: US7、US9、US10

## What to build

扩展一键安装器、PyInstaller 载荷和签名更新流程，使其包含新版扩展、多浏览器清单、FFmpeg/ffprobe、第三方许可、schema 5 数据库迁移与 `desktop_ffmpeg` 健康检查。升级失败必须恢复旧程序和原数据，不留下半迁移状态。

## Acceptance criteria

- [x] 安装器复制并校验扩展、FFmpeg/ffprobe、locale、许可和对应源码/源码链接清单。
- [x] FFmpeg 二进制来源、版本、SHA-256、构建配置和许可证可从安装界面或第三方通知查看。
- [x] 0.6.0 → 1.0.0 数据迁移保留任务、规则、配对、指纹、更新设置和 Eagle 项目编号。
- [x] Chrome/Edge/Firefox 的手动加载步骤、配对 Origin 和扩展更新/重载行为分别有说明。
- [x] 新版健康检查覆盖本机 API、数据库版本、`desktop_ffmpeg` 引擎、FFmpeg/ffprobe、扩展协议版本和基本合并自检。
- [x] 任一健康检查失败时恢复旧程序目录和旧数据库可读状态，清理只针对安装器拥有的暂存目录。
- [x] 更新包签名、大小、SHA-256、GitHub 地址和第三方资产哈希任一不符时拒绝安装。
- [x] 卸载保留用户下载、Eagle 内容和可选历史；只删除安装归属与任务归属明确的程序/临时文件。

## Blocked by

- 01 — 锁定 GPL、源码来源与第三方许可门禁。
- 05–13 — 最终运行时资产、schema、权限和健康检查已确定。
