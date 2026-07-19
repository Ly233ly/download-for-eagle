# 下载中转站 1.1.2 验证报告

日期：2026-07-19  
状态：源码、84 项自动门、冻结构建、覆盖安装、发行哈希和 Behance 播放器实页质量目录均已通过；Chrome 工具栏 popup 同视口视觉截图待人工点验

## 问题与结论

Behance `Song of the Stars - TXT` 的 Vimeo 播放器只对应一个视频，但旧版把自适应播放产生的 21 个 MP4 初始化/媒体分片列进“选择版本”。播放器公开的真实质量目录为 `1080p、720p、540p、360p、240p`，完整 HLS 主清单包含五个对应变体。

1.1.2 从结构化播放器配置提取完整主清单和质量目录；同组清单存在时隐藏普通 MP4/音频分片。popup 分开显示当前播放质量和可下载质量，最高档默认推荐。用户选择的高度随本机计划进入内存，ffprobe 定位相应节目视频与关联音频，FFmpeg streamcopy 输出单一质量。

## 自动证据

- `test_candidate_presentation.js`：Vimeo 配置转完整 HLS 主清单，质量目录降序且绑定视频 ID。
- `test_popup_logic.js`：一个清单替换 21 个 MP4 分片，只显示五个明确质量档位并默认 1080p。
- `test_manifest_quality_selection_uses_the_requested_program`：1080p、720p 与默认最高档分别映射正确节目视频和音频。
- 全部扩展 JavaScript 语法、Chrome/Firefox 清单和版本一致性纳入 84 项 Python 自动测试。

## 发行证据

- 冻结运行时：版本 `1.1.2`、协议 `1`、数据库结构 `5`、下载引擎 `desktop_ffmpeg`、`mediaReady=true`，内置 FFmpeg 与 FFprobe 均存在。
- 隔离安装器：全新安装、覆盖升级废弃脚本清理、失败回滚和卸载恢复全部通过。
- 当前电脑：已覆盖安装到 `%LOCALAPPDATA%\IDM-Eagle自动导入助手`；`/health` 返回 `1.1.2`，安装目录扩展清单为 `1.1.2`，后台与启动器均从该目录运行。
- 旧扩展文件：`background.js`、`js/popup.js`、`js/media-control.js` 均不在安装目录。
- ZIP：`release/下载中转站-1.1.2-Windows-x64/下载中转站-1.1.2-Windows-x64.zip`，`93,322,089` 字节，SHA-256 `9bb8e7662fc3409836e768dff68b05eb78a57fa1bb81aac9623e549a98bb25f4`。
- Chrome 实页：覆盖安装后刷新 Behance，Vimeo 结构化配置仍确认视频 `1143783367`、`1920×1080`、时长 `103` 秒、完整 HLS 主清单以及 `1080p、720p、540p、360p、240p` 五档质量。

## 待人工视觉点验

Chrome 安全边界不允许自动化工具点击或读取工具栏扩展 popup。请在 `chrome://extensions` 对已加载的解压扩展点一次“重新加载”，刷新 Behance 页面并打开 popup；预期只出现一个媒体组，质量选择器只列五个明确档位，`1080p` 标记“推荐”，不再出现 21 个按 KB/MB 命名的 MP4 分片。该点只影响同视口视觉证据，不影响上述代码、下载映射、冻结运行时和覆盖安装结果。
