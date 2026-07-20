# 1.2.6 通用信息流内容绑定验证报告

验证日期：2026-07-20

## 结论

1.2.6 已把主页、推荐流和瀑布流中的候选爆炸作为通用内容绑定问题修复，不包含 X 或其他示例站点的域名白名单。每个能证明内容永久链接的播放器按自己的内容容器形成一张候选卡片；无法证明属于哪张内容卡片的 HLS、DASH、视频和音频请求默认进入不可提交的技术区。

源码、105 项 Python 回归、5 组 Node 逻辑回归、17 个扩展 JavaScript 文件、Chrome/Firefox 双清单、冻结运行时和隔离安装器均通过。1.2.6 已覆盖安装到当前电脑，在线健康门为 `version=1.2.6`、schema 5、协议 1、`desktop_ffmpeg`，媒体工具与 YouTube 解析器均就绪；安装目录五个本次修改的扩展核心文件与源码 SHA-256 一致。

Chrome 安全边界禁止自动操作 `chrome://extensions`，所以自动与安装验证已完成，A176 最后只保留用户手动重载扩展后的 popup 点验。

## 根因证据

- 现场信息流 DOM 只有 4 个 `<video>`，其中 2 个位于当前可视区域；旧 popup 却显示 18 个默认媒体组并另藏 42 个播放分片。
- 每个真实播放器附近都能读取自己的内容容器、稳定状态永久链接、正文、poster 和时长，页面并不缺少区分内容所需的信息。
- blob/MSE 的 `video.currentSrc` 无法与网络层 HLS/DASH 地址直接相等；未被 DOM 内容候选认领的清单因此各自成组。
- 旧标题回退使用浏览器标签页标题，进一步把不同请求显示成同名内容，用户无法判断下载对象。

## 通用实现门禁

- `selectContentTitle` 从最近内容容器的语义说明、标题、可读正文和图片说明中选择最有信息量的标题，并过滤纯计数、时间轴、相对时间、账号名和控件文案；标签页标题只作最后兜底。
- 能从同源稳定永久链接证明身份的 blob/MSE 播放器形成 `resolver=page` 内容候选，标题、封面、时长和链接均来自同一个内容容器。
- 同一标签页和来源域已有内容绑定候选时，无内容身份的孤立播放请求标记为 `technicalOnly`，默认隐藏；诊断开关可查看紧凑技术行，但单项和批量提交都会阻断。
- 没有内容绑定候选的网站不套用上述降级，唯一完整 HLS/DASH 清单继续可见、可下载，避免用信息流规则破坏普通播放器。
- 工具栏角标与 popup 共同调用 `groupCandidates → partitionGroups`，不会再出现小图标数量和打开后数量口径不同。

## 自动与本机验证

- `python -m unittest discover -s tests -q`：105/105 通过。
- `test_auth_race.js`、`test_bilibili.js`、`test_candidate_presentation.js`、`test_popup_logic.js`、`test_youtube.js`：全部通过。
- 全部 17 个扩展 `.js`：`node --check` 通过；两个 manifest JSON 解析通过，版本均为 1.2.6。
- 回归固定 3 个内容绑定候选和 12 个未关联 HLS：默认仅显示 3 个，诊断区保留 12 个技术项且下载校验返回 `unbound_playback`；没有页面替代项的单个完整清单继续可用。
- 冻结运行时：健康、schema 5、FFmpeg/ffprobe、yt-dlp/Deno、IDM 接收模式和任务持久化通过；证据为 `.scratch/frozen-runtime-1.2.6-evidence.json`。
- 隔离安装器：全新安装、覆盖更新、强制失败回滚和卸载全部通过；证据为 `.scratch/installer-1.2.6-evidence.json`。
- 当前电脑：在线 `/health` 返回 1.2.6；`eagle-bridge-candidate-logic.js`、`content-script.js`、`background.js`、`eagle-bridge-ui-logic.js`、`eagle-bridge-ui.js` 与源码哈希一致。

## 发行物

- 目录：`release/下载中转站-1.2.6-Windows-x64/下载中转站-1.2.6`
- ZIP：`release/下载中转站-1.2.6-Windows-x64/下载中转站-1.2.6-Windows-x64.zip`
- 大小：164,401,138 字节
- SHA-256：`2e2672e9da3b217985c2259622be50c0587f86bed1d5fc6efb7a61d6114d0ccd`

## 最后人工闭环

1. 在 `chrome://extensions` 对实际加载的“下载中转站”点击一次“重新加载”，再刷新来源信息流页面；旧 service worker 和旧会话候选不会自动替换。
2. 打开 popup，默认列表应接近页面真实视频卡片数；每张卡片应显示自己的正文标题、预览和时长，不再堆叠同名“主页 / X”或其他标签页标题。
3. 打开筛选中的“显示未关联资源与播放分片”，可审计被隐藏的网络请求；它们只以紧凑技术行显示，不能单项或批量下载。
