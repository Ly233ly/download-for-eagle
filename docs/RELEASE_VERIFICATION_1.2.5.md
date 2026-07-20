# 1.2.5 抖音逐视频标题与候选身份验证报告

验证日期：2026-07-20

## 结论

1.2.5 已实现抖音逐视频内容身份：同一精选页内，每个已加载播放器按自己的明确视频 ID、作者和左下角文案形成独立候选，不再共用浏览器标签页标题。无法精确绑定某个播放器和视频 ID 的底层 blob/MSE 音视频请求只作为隐藏技术分片，不可提交下载。

源码、105 项 Python 回归、5 组 Node 逻辑回归、17 个扩展 JavaScript 文件、Chrome/Firefox 双清单、冻结运行时和隔离安装器均通过。1.2.5 已覆盖安装到当前电脑，在线健康门为 `version=1.2.5`、schema 5、协议 1、`desktop_ffmpeg`、FFmpeg 与 yt-dlp/Deno 均就绪；安装目录四个本次修改的扩展核心文件与源码 SHA-256 一致。

已在当前登录的抖音精选页重载并读取现场 DOM，两个同时存在的播放器仍分别暴露独立视频 ID、文案和时长。Chrome 工具无法直接操控工具栏 popup 完成最终点击下载，因此 A172 的自动验证已完成，最后只保留用户在 popup 中肉眼确认卡片与下载结果一致。

## 根因证据

- 当前项：`7662692425235828009`，作者 `@热话动漫`，文案“这一集的瑞克，终于不像个疯子，像个外公…”，时长 223.234 秒。
- 预加载项：`7653805516250025262`，作者 `@木板解说`，文案“第7集：深度拆解瑞克和莫蒂 S6E4《夜晚家庭》…”，时长 532.922 秒。
- 两项都位于自己的 `data-e2e=feed-item`，各自含 `feed-video-nickname`、`video-desc` 和 `video_<id>`；页面并不缺少逐视频元数据。
- 抖音播放器使用 blob/MSE 时，底层 HTTP 请求不能与 DOM `video.currentSrc` 精确匹配。旧回退会复制 `webInfo.title`，因此多个不同视频被显示成同一个标签页标题。

## 已实现门禁

- 为每个已就绪且能提取明确 ID 的抖音 `feed-item` 建立 `douyin:<videoId>`，不再只处理当前主播放器。
- 标题只由当前项自己的 `feed-video-nickname + video-desc` 组成，并移除界面尾部“展开”；没有正文时使用带 ID 的中性名称，不使用标签页标题。
- 当前播放与页面预加载使用同一内容模型，但标记分别为“当前播放”和“页面已加载”；规范地址统一为 `https://www.douyin.com/video/<id>`。
- 无精确播放器视觉匹配、无结构化 `mediaMeta` 的抖音底层音视频请求标记 `unboundDouyinMedia`，统一进入 `segmentOnly` 技术分区，默认隐藏并阻止提交。
- 测试固定现场两个视频 ID、两组作者/文案，并证明二者保持为两个内容组；即使无身份请求是大型完整 MP4 外观，也不得抢占内容候选。

## 自动与本机验证

- `python -m unittest discover -s tests -q`：105/105 通过。
- `test_auth_race.js`、`test_bilibili.js`、`test_candidate_presentation.js`、`test_popup_logic.js`、`test_youtube.js`：全部通过。
- 全部 17 个扩展 `.js`：`node --check` 通过；两个 manifest JSON 解析通过，版本均为 1.2.5。
- 冻结运行时：健康、schema 5、FFmpeg/ffprobe、yt-dlp/Deno、IDM 接收模式和任务持久化通过；证据为 `.scratch/frozen-runtime-1.2.5-evidence.json`。
- 隔离安装器：全新安装、覆盖更新、强制失败回滚和卸载全部通过；证据为 `.scratch/installer-1.2.5-evidence.json`。
- 当前电脑：在线 `/health` 返回 1.2.5；`eagle-bridge-candidate-logic.js`、`content-script.js`、`background.js`、`eagle-bridge-ui-logic.js` 与源码哈希一致。
- 当前抖音页重载后，现场 DOM 仍有两个独立内容项：223.234 秒的当前项和 532.922 秒的预加载项，ID 与文案没有串联。

## 发行物

- 目录：`release/下载中转站-1.2.5-Windows-x64/下载中转站-1.2.5`
- ZIP：`release/下载中转站-1.2.5-Windows-x64/下载中转站-1.2.5-Windows-x64.zip`
- 大小：164,388,754 字节
- SHA-256：`8eba9f8ad0c080a76077c2909213210a31c256035c63a96b52140692a5ecc984`

## 最后人工闭环

1. 在 `chrome://extensions` 对实际加载的“下载中转站”点击一次“重新加载”，再刷新抖音来源页；这一步会清除旧会话中已经写入的错误标题。
2. 打开 popup，确认当前 3:43 视频显示 `@热话动漫 · 这一集的瑞克…`，下一条 8:53 预加载视频显示 `@木板解说 · 第7集：深度拆解…`，而不是相同标签页标题。
3. 分别下载两个候选，确认任务标题、预览、时长和最终文件属于同一视频。
