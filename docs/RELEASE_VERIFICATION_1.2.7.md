# 1.2.7 通用信息流发现生命周期验证报告

验证日期：2026-07-20

## 结论

1.2.7 已修复信息流页面“网页中正在播放的视频存在，但 popup 没有内容卡片”的通用生命周期问题。实现不包含 X 或其他示例站点分支：持续 DOM 变化不能再无限推迟扫描；打开或刷新 popup 会主动恢复扩展重载后保持打开网页的发现脚本，并立即扫描当前播放器。

源码、105 项 Python 回归、5 组 Node 逻辑回归、17 个扩展 JavaScript 文件、Chrome/Firefox 双清单、冻结运行时和隔离安装器全部通过。1.2.7 已覆盖安装到当前电脑，在线健康门为 `version=1.2.7`、schema 5、协议 1、`desktop_ffmpeg`，媒体工具与 YouTube 解析器均就绪；安装目录六个相关扩展文件与源码 SHA-256 一致。

Chrome 保护页不允许自动化接口代点扩展重载，因此 A180 最后保留用户点击一次“重新加载”后，由已连接的当前 X 页面完成不刷新页面的 popup 恢复点验。

## 现场根因证据

- 当前页面 DOM 只有两个 `<video>`；目标播放器处于可视区域并正在播放，时长 21.632 秒。
- 目标内容容器提供稳定永久链接 `https://x.com/xilo2991/status/2078995639690723495`、poster 和两行独立正文。
- `chooseContentPageUrl` 对现场链接输出该永久链接；`selectContentTitle` 输出“我的动画科普Skill快完成了haha”。因此链接和标题算法并未漏掉该视频。
- popup 同时显示多条网络清单却没有该内容卡，说明新 service worker 可以捕获请求，但页面内容候选扫描没有执行。
- 原扫描使用尾随防抖：每次 DOM 变化先清除 250 ms 定时器。高频信息流更新会长期推迟扫描；扩展重载时保持打开的网页也不会自动注入新内容脚本。这两个条件均为通用浏览器生命周期问题。

## 已实现门禁

- `createBoundedScheduler` 在已有待执行扫描时只合并信号，不重置期限；100 次连续变化仍只建立一个必定执行的回调，回调完成后可安排下一轮。
- `content-script.js` 启动时立即执行 `discoverPageResolvers`，并响应同名主动探测消息。
- popup 在读取候选快照前调用 `ensureDiscovery`；后台先向指定标签发消息，已响应时只扫描、不重复注入。
- 接收端不存在时，`chrome.scripting` 只向当前顶层 HTTP(S) 标签注入 `eagle-bridge-candidate-logic.js` 与 `content-script.js`，然后再次触发扫描。
- `chrome://` 等受限协议、无效标签和其他标签禁止注入。恢复路径不包含下载器、站点适配或远程代码。
- 恢复出的页面候选继续进入 1.2.6 的通用内容绑定；未关联网络请求仍只作不可提交技术资源。

## 自动与本机验证

- `python -m unittest discover -s tests -q`：105/105 通过。
- `test_auth_race.js`、`test_bilibili.js`、`test_candidate_presentation.js`、`test_popup_logic.js`、`test_youtube.js`：全部通过。
- 全部 17 个扩展 `.js`：`node --check` 通过；两个 manifest JSON 解析通过，版本均为 1.2.7。
- 冻结运行时：健康、schema 5、FFmpeg/ffprobe、yt-dlp/Deno、IDM 接收模式和任务持久化通过；证据为 `.scratch/frozen-runtime-1.2.7-evidence.json`。
- 隔离安装器：全新安装、覆盖更新、强制失败回滚和卸载全部通过；证据为 `.scratch/installer-1.2.7-evidence.json`。
- 当前电脑：在线 `/health` 返回 1.2.7；候选逻辑、内容脚本、桥接后台、UI、UI 归组逻辑和网络后台六个文件与源码哈希一致。

## 发行物

- 目录：`release/下载中转站-1.2.7-Windows-x64/下载中转站-1.2.7`
- ZIP：`release/下载中转站-1.2.7-Windows-x64/下载中转站-1.2.7-Windows-x64.zip`
- 大小：164,410,836 字节
- SHA-256：`7fe6aebce831a3f074f55f68004803d2806edb43b2f8c22f91d4128ab489affe`

## 最后人工闭环

1. 保持当前信息流页面不刷新，在 `chrome://extensions` 对“下载中转站”点击一次“重新加载”。
2. 直接打开 popup；它应自动恢复当前网页发现脚本并出现目标视频自己的标题、poster/帧和约 22 秒时长。
3. 默认列表不再把未关联清单冒充内容；诊断开关仍可查看这些技术资源，但不能下载。
