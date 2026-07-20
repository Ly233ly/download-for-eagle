# 1.2.9 结构化视频页面发现验证报告

日期：2026-07-20

## 结论

1.2.9 已修复“网页视频正常播放、扩展捕获到多条播放器请求，但默认媒体仍为 0”的通用发现缺口。网页明确公开视频类型或 Player 卡片，并给出同源、非首页的规范作品地址时，扩展会建立一个 `resolver=page` 内容候选；底层未关联 HLS、DASH 和分片仍留在技术区，不会冒充完整视频。

实现按页面元数据能力判断，不包含 Vimeo 或其他站点域名分支。普通网页、首页、跨源规范地址以及没有明确视频声明的页面不会生成页面视频候选。

## 现场根因与解析能力

- 现场作品：`https://vimeo.com/746646949?fl=pl&fe=vl`。
- 修复前：视频正常播放，扩展显示 0 个默认媒体，并隐藏 11 个未关联播放器资源。
- 页面公开 `og:type=video.other`、`twitter:card=player`、`og:url=https://vimeo.com/746646949` 及带作品 ID 的 Player 地址。
- 本机安装版 yt-dlp 2026.06.09 已对同一地址实测成功，列出 240p、360p、540p、720p、1080p、1440p 和 2160p/4K 格式，证明桌面下载解析链路可用。

## 自动与发行验证

- Python：105 项全部通过，包含结构化页面候选、通用页面解析、下载、合并、验证和敏感上下文边界。
- Node：候选展示与启动快照等逻辑回归通过，Vimeo 数字作品页会规范化为 `https://vimeo.com/746646949`；普通首页和无视频声明页面保持空结果。
- 扩展：全部 JavaScript 文件通过语法检查；Chrome/Firefox 双清单均为 1.2.9。
- 冻结运行时：健康版本 1.2.9、schema 5、扩展协议 1、`desktop_ffmpeg`、FFmpeg/ffprobe、yt-dlp/Deno 和 IDM 接收模式全部通过；证据为 `.scratch/frozen-runtime-1.2.9-evidence.json`。
- 隔离安装器：全新安装、覆盖更新、强制失败回滚和卸载恢复全部通过；证据为 `.scratch/installer-1.2.9-evidence.json`。
- 当前电脑：覆盖更新成功；在线健康返回 1.2.9、`mediaReady=true`、`youtubeResolverReady=true`，安装目录扩展清单为 1.2.9，已安装候选逻辑包含结构化视频修复。
- 分享 ZIP：共 1,477 个条目，已核对一键安装器、浏览器插件、完整源码和结构化视频修复均在包内。

## 发行物

- 目录：`release/下载中转站-1.2.9-Windows-x64/下载中转站-1.2.9`
- ZIP：`release/下载中转站-1.2.9-Windows-x64/下载中转站-1.2.9-Windows-x64.zip`
- 大小：165,422,592 字节
- SHA-256：`4d924791c23dc34683ff8317fcd53553c625b79d3c90ce0c6cd92d29dccbc671`
- 固定工具：PyInstaller 6.21.0、FFmpeg 8.1.2、yt-dlp 2026.06.09、Deno 2.8.1

## 用户复验

安装文件已经更新，但 Chrome 已加载的旧脚本必须重载一次：打开 `chrome://extensions`，在“下载中转站”卡片点击“重新加载”，回到 Vimeo 作品页刷新并播放数秒，再打开扩展。默认列表应出现一个标题为 “Bang & Olufsen - Beosound Theatre” 的页面视频卡片；11 个底层技术资源可以继续隐藏，这是正常行为。Chrome 现场卡片与实际创建任务是 A187 剩余的人工点验。
