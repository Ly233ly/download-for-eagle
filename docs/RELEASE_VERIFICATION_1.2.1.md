# 1.2.1 发行验证

验证日期：2026-07-19  
范围：YouTube MSE 结构化格式目录、通用流身份/探测分片、完整发行与本机更新。

## 根因证据

- 现场页：`https://www.youtube.com/watch?v=pIzs1qe-aBc`。
- 页面正在播放 53:27 视频，但 DOM `video.currentSrc` 为 YouTube 同源 MSE 占位地址，不是 `googlevideo` 媒体直链。
- 普通捕获只形成四条约 7 KB 的音频探测；IDM 同页可展示 1440p、1080p、720p、480p、360p、240p、144p。
- 代码审计确认旧活动扩展只有 Bilibili/Vimeo 结构化适配，没有 YouTube player response 适配。

## 实现证据

- `catch-script/youtube.js` 在主世界读取初始播放器响应并监听 player API，解析带直接 URL 的 `adaptiveFormats`。
- `js/youtube-content.js` 通过随机页面通道把 videoId/itag、标题、缩略图、时长、质量和编码发送给既有后台发现入口。
- 候选身份以 groupKey + streamId 区分，同一路径不同 itag 不折叠。
- 显式 Range 和无身份小媒体探测进入默认隐藏诊断分区。
- 扩展只发现和提交；任务仍由桌面 `desktop_ffmpeg` 下载、合并和校验。

## 自动验证

- 95 项 unittest：通过。
- 所有活动扩展 JavaScript `node --check`：通过。
- `test_youtube.js`、`test_popup_logic.js`、`test_candidate_presentation.js`、`test_auth_race.js`：通过。
- Chrome/Firefox 清单 JSON 与 1.2.1 版本一致：通过。
- 冻结运行时：健康版本 1.2.1、schema 5、扩展协议 1、`desktop_ffmpeg`、FFmpeg/ffprobe、IDM 接收任务唯一入库全部通过。
- 隔离安装器：全新安装、成功更新、故障回滚、卸载、扩展 1.2.1 和配对凭据全部通过。
- 当前电脑覆盖更新：安装器退出码 0；在线健康版本 1.2.1，schema 5，扩展协议 1，`mediaReady=true`，下载引擎 `desktop_ffmpeg`；安装副本包含两个 YouTube 适配文件。

## 发行物

- 目录：`release/下载中转站-1.2.1-Windows-x64/下载中转站-1.2.1`
- ZIP：`release/下载中转站-1.2.1-Windows-x64/下载中转站-1.2.1-Windows-x64.zip`
- 大小：92,277,228 字节
- SHA-256：`c7a41d321c19fbe9a6e98508677f23a11e85f66c129afe9995c757d75776c1aa`
- PyInstaller：6.21.0
- FFmpeg/ffprobe：8.1.2

## Chrome 现场闭环

待用户按 Chrome 安全边界在 `chrome://extensions` 对解压扩展点击一次“重新加载”，再刷新现场 YouTube 页。完成后检查：一个当前视频内容组、多个真实视频/音轨档位、无四条 7 KB 探测；不启动 53 分钟大文件下载，只确认提交前方案仍标记本机下载/合并。
