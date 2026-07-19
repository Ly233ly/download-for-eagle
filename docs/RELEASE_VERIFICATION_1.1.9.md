# 下载中转站 1.1.9 验证报告

验证日期：2026-07-19  
状态：媒体身份修复、91 项全量回归、发行构建、当前电脑覆盖安装和自动门禁通过；Chrome 实机证明错配防线生效，但同页多数未匹配候选只显示占位，A138 未完整关闭，由 1.1.10 接替。

## 1.1.8 实机失败证据

- 用户选择的卡片为当前 45:13 抖音视频，画面和右侧预览一致。
- 计划数据库记录 `duration=2713.034`，最终文件 FFprobe 为 `708.141475`。
- 最终文件首帧与所选画面不同，证明任务虽为 `imported/100`，内容身份仍错误。

## 修复与回归

- 请求 URL 与播放器来源按同主机、同路径匹配；只忽略签名查询参数。
- 未匹配预加载请求不再继承当前播放器的帧、时长、尺寸和组键。
- 本机对非清单直链增加输出时长一致性门禁，明显错配返回 `output_duration_mismatch` 并阻止交付。
- 修复前 JS 身份测试和 Python 错配交付测试失败；实现后通过。
- 全量 unittest 共 91 项通过，包含全部扩展 JavaScript 语法与 Chrome/Firefox 双清单解析。

## 自动与发行门禁

- 冻结运行时通过：`version=1.1.9`、`extensionProtocol=1`、`databaseSchema=5`、`mediaReady=true`、`downloadEngine=desktop_ffmpeg`，IDM 接收器退出码 0 且生成 1 个任务。
- 隔离安装器的新装、升级、注入失败回滚和卸载全部通过。
- 当前电脑已覆盖安装；在线 `/health` 返回 1.1.9、协议 1、schema 5、`desktop_ffmpeg` 和媒体工具就绪。
- 安装目录 `eagle-bridge-candidate-logic.js`、`content-script.js`、`background.js` 与仓库源码 SHA-256 一致；三个主可执行文件与发行包一致。

## Chrome 实机闭环

1. 重载实际加载的 1.1.9 解压扩展并刷新抖音来源页，清除 1.1.8 的旧候选会话。
2. 选择有真实当前帧和时长的内容卡；未匹配预加载请求不得显示成该内容的版本。
3. 点击“仅下载”或“下载并导入 Eagle”，记录同一任务 ID。
4. 用 FFprobe 和本机预览确认最终文件时长/画面与所选卡片相同。
5. 任务达到 `completed_local/100` 或 `imported/100`，保存路径存在且可打开。

## 发行物

- ZIP：`release/下载中转站-1.1.9-Windows-x64/下载中转站-1.1.9-Windows-x64.zip`
- 大小：93,384,445 字节
- SHA-256：`609e2dd3673f8a454d3106ac597368825145f8a36f7d982471c1809cce0fe969`
- PyInstaller：6.21.0
- FFmpeg/ffprobe：8.1.2
