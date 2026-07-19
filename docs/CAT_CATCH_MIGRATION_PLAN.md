# `cat-catch` 全量集成计划

> 历史文档：这是 1.0.0 的迁移计划，不再定义 1.2.0 活动运行时。1.2.0 由决策 65–69 与 A145–A151 取代“完整上游工具箱”目标；固定源码仍因 GPL 对应源码义务保留。

- 状态：任务 01–14 已形成 1.0.0 集成基线；任务 16–17 已完成方案 2 与本机统一下载，待新载荷视觉/发行复验和维护者签字
- 目标版本：`1.0.0`
- 交付方式：一次性正式发布；内部任务可独立开发和验证，但不发布缺功能的中间正式版。

## 目标

1. 将 `cat-catch` 2.7.1 的资源嗅探、深度搜索、预览、HLS、DASH、下载、录制、调用外部工具和媒体控制能力完整纳入下载中转站。
2. 保留下载中转站现有的 IDM 完成事件、SQLite 持久任务、来源匹配、内容去重、Eagle 导入、签名更新和故障回滚。
3. 默认让用户看见要下载的内容，而不是只看到文件后缀或原始 URL。
4. 对 B 站等音视频分离场景提供视频档位、音轨和最终输出的统一选择，并自动无损合并。
5. 所有功能在 `1.0.0` 发布门一次性验收，不把半成品作为正式升级推送给现有用户。

## 已核实的上游行为

- 上游以 Manifest V3 `webRequest` 捕获 URL、MIME、大小和请求头，并用 MAIN world 脚本补充 XHR、Fetch、Worker、MediaSource 和 WebRTC 等隐藏资源。
- 预览页面支持筛选、排序、预览以及选中一条视频和一条音频进行在线合并，但需要用户额外打开筛选页面；本项目把可见预览改为默认入口。
- HLS 解析器包含清单解析、变体/音轨、切片范围、并发重试、BYTERANGE、初始化段、AES-128-CBC、自定义 Key、直播录制、边下边存和 MP4 转封装。
- DASH 解析器能列出视频和音频 Representation 并转换为可下载清单；上游仍把 DASH 加密和直播标为不支持。
- 上游“在线 FFmpeg”通过外部网页加载约 30MB 的 FFmpeg/WASM，在浏览器中处理文件；受 WebAssembly/Chromium 内存约束，最大约 2GB。
- FFmpeg 官方文档支持用显式 `-map` 和 `-c copy` 把独立视频、音频流无损封装进同一容器；不兼容时才允许转码。

研究基线：

- `cat-catch`：<https://github.com/xifangczy/cat-catch/tree/7a77612b3e2a01cedacae6e43eb88a89eee3034f>
- 上游预览：<https://cat-catch.94cat.com/docs/preview>
- 上游 HLS：<https://cat-catch.94cat.com/docs/m3u8parse>
- 上游 DASH：<https://cat-catch.94cat.com/docs/mpdparse>
- 上游在线 FFmpeg：<https://cat-catch.94cat.com/docs/online-ffmpeg>
- FFmpeg streamcopy 与 stream mapping：<https://ffmpeg.org/ffmpeg.html#Streamcopy>
- Chrome Downloads API：<https://developer.chrome.com/docs/extensions/reference/api/downloads>
- IDM 命令行：<https://www.internetdownloadmanager.com/support/command_line.html>

## 一次性交付范围

“一次性”是一个发行门，不是把所有代码塞进单个任务。十五个任务必须全部达到验收条件后才允许生成 `1.0.0` 正式更新；实现过程中允许使用开发构建和隔离测试包，但不得标记为稳定版或推送自动更新。

完整功能映射见 [FEATURE_PARITY_MATRIX.md](FEATURE_PARITY_MATRIX.md)，详细任务与逐项验收见 [`docs/tasks/`](tasks/)。

## 目标体验

### 默认可见资源库

点击扩展后直接打开当前页面的媒体候选组，而不是原始请求列表。每组默认展示：

- 页面标题、站点、封面或可生成的首帧；
- 资源类型（直链、HLS、DASH、缓存、录制）；
- 时长、分辨率、帧率、编码、码率、预计大小；
- 可用视频档位、音轨、字幕和容器；
- 最终文件名、下载方式、合并方式和是否会自动导入 Eagle；
- 内嵌视频/音频预览；无法预览时显示具体原因，不使用空白占位。

原始 URL、请求头摘要、requestId 和调试字段放在折叠的“技术信息”中。

### B 站/DASH 示例

1. 扩展在同一捕获会话中识别页面标题、封面和独立视频/音频流。
2. 候选归组器按标签页、主文档导航周期、清单/播放器上下文、时间窗口和媒体元数据创建一个媒体候选组。
3. 用户选择一个视频档位和一个音轨；界面显示最终容器、预计大小和输出名。
4. 扩展经认证回环 API 提交每路完整 URL 与白名单请求上下文；普通直链和受保护分轨都由本机 `desktop` 任务下载，请求头只在任务内存中存在。
5. 本机 FFmpeg 使用显式流映射和 `-c copy` 合并；若容器不兼容，界面解释后才允许受控转码或改用 MKV。
6. 下载/合并成功后只清理任务专属临时目录中的中间输出；最终文件按选择进入 JobProcessor/Eagle 或以“仅下载”交付。
7. 任一媒体流失败、取消或校验不通过时不产生伪成功文件；同次运行可重试，软件重启后要求回来源页重建。

## 目标架构

```text
页面与网络请求
  ├─ webRequest / 页面媒体元数据
  ├─ content script 元数据
  └─ 可选 MAIN world 深度搜索、缓存与录制
                  │
                  v
      捕获会话 → 媒体候选组 → 可见预览与选择
                  │
                  v
          认证本机下载方案（desktop）
                        │
                        v
       本机 FFmpeg 下载/streamcopy + ffprobe
                        │
              ┌─────────┴─────────┐
              v                   v
     completed_local      持久队列与 JobProcessor
                                  │
                                  v
                             Eagle 官方 API
```

### 浏览器扩展

- 使用清晰模块边界替代单个超大 background/popup 文件：捕获、归组、预览、下载、解析、录制、集成和设置分别维护。
- service worker 只保存可恢复的轻量状态；大量媒体数据不得依赖 service worker 内存。
- 候选列表保存在扩展会话存储并按需同步到本机数据库；敏感请求信息默认不持久化。
- Chrome/Edge Windows 是完整验收基线；Firefox 对浏览器 API 允许的功能达到同等行为，并明确记录无法实现的 API 差异。

### 本机 API 与数据库

新增版本化 API 和数据模型：

- `capture_sessions`：标签页和主文档导航周期。
- `media_groups`：用户看到的内容级候选。
- `media_streams`：视频、音频、字幕、清单和普通资源。
- `download_plans`：用户确认的下载/合并输出。
- `download_plans` 直接记录本机阶段、处理字节、预计总量、预览、最终文件、是否导入 Eagle 和关联 job；schema 5 不再使用 `component_files` 浏览器交接表。

所有迁移使用 `PRAGMA user_version`。旧任务、网站规则、配对、指纹和 Eagle 项目编号原样保留。最终媒体文件仍进入现有 `jobs`/`JobProcessor`，避免建立第二套导入逻辑。

### 下载路由

- **统一本机路线**：所有可见主下载动作固定 `route=desktop`。扩展只提交计划，本机 FFmpeg 负责普通直链、受保护分轨和 HLS/DASH；签名查询和请求头不写数据库。
- **仅下载**：与导入任务使用同一下载和验证路径，但 `import_to_eagle=0`，完成后不创建 job。
- **IDM 原流程**：IDM 已完成文件的自动导入仍独立保留，不作为扩展媒体任务的下载分流。
- **不再可见的替代路线**：Chrome 组件下载、浏览器 FFmpeg、自动下载、完整浏览器下载器、Aria2、N_m3u8DL-RE、send2local、MQTT 和自定义调用不进入新版可见界面。

### 合并引擎

- 默认捆绑经过许可审计的 `ffmpeg.exe` 和 `ffprobe.exe`，只从固定安装目录执行，命令参数使用数组构造，不经 shell 拼接。
- 第一选择为 `-map 0:v:0 -map 1:a:0 -c copy` 一类 streamcopy；兼容失败时优先更换容器，再由用户选择是否转码。
- 新版可见下载流程不加载浏览器 FFmpeg/WASM 或第三方处理页面；本机路线不设 2GB 产品上限。

## 许可方案

`cat-catch` 2.x 声明为 GPL-3.0，本仓库当前为 MIT。直接复制或修改上游代码形成组合发行时，不能继续把整个发行描述为“仅 MIT”。

实际采用的方案是：

1. 在任何源码迁移前生成来源清单和文件级版权记录。
2. 由项目所有者确认 `1.0.0` 组合发行采用 GPL-3.0 合规方式；原有 MIT 代码保留其原版权和 MIT 许可通知。
3. 发布包提供 GPL 文本、第三方通知、对应源码、构建脚本和可复现版本信息。
4. 1.0.0 已选择 GPL-3.0 组合发行，没有使用 clean-room 分支；完整上游固定源码快照随对应源码提供。

该门禁是法律与发行条件，不是可在末尾补做的文档任务。

## 安全与隐私

- 默认不持久化 Cookie、Authorization、完整请求头、媒体字节或网页正文。
- 需要登录态时由扩展把字段白名单化的最小请求上下文经配对认证传给本机任务内存；不写 SQLite、扩展 storage 或日志，并在终态擦除。
- 封面只保存 URL 或用户确认的本地副本；诊断导出只保留站点和脱敏字段。
- 在线服务、Aria2、MQTT、send2local、自定义调用和浏览器下载器不进入新版可见下载流程。
- 检测 Widevine、PlayReady、FairPlay、SAMPLE-AES 或等效 DRM 时标记 `blocked_drm`，不下载密钥、不调用解密、不提供绕过教程。
- 深度搜索、MediaSource 代理和 WebRTC 录制按标签页显式启用；脚本关闭或页面离开时恢复被代理对象。

## 失败与恢复

- 下载方案状态：`queued`、`downloading`、`validating`、`ready_to_import`、`imported`、`completed_local`、`retry`、`canceled`、`blocked_drm`。
- 下载、解析、合并、校验和导入分别记录错误分类；同次软件运行保留内存上下文以重试。
- 软件中断后保留任务记录，但完整媒体 URL 不落盘，因此活动任务标记 `download_context_expired` 并要求回来源页重建，不把半成品或脱敏 URL 当作可恢复输入。
- 更新和卸载只清理带安装归属或任务归属的目录；用户原文件和 Eagle 内容永不删除。

## 正式发布门

> 2026-07-18 补充：1.0.0 功能集成后的 popup 暴露出双 UI、候选未归组和全局单任务；随后 Chrome 下载普通组件又造成路由、进度和请求上下文不一致。任务 16–17 与 A96–A112 以单 UI 和统一 `desktop` 状态机取代这些路线。旧 1.1.0 schema 4 包不能作为 schema 5 的最终发行证据。

1.0.0 保留为全功能集成基线；包含方案 2 UI 重构的正式交付版本为 `1.1.0`。只有同时满足以下条件才允许把 1.1.0 标记为最终通过：

- [x] `FEATURE_PARITY_MATRIX.md` 没有未解释的功能缺失，上游 96 个运行时文件全部在包内。
- [x] GPL-3.0 许可门禁、固定来源、对应源码、构建材料和第三方通知齐全。
- [x] 83 项回归/新增测试、Eagle 4 健康接口兼容、扩展连接健康端点、真实帧、稳定播放器归组、传输分片折叠、补丁升级自重载、首次缓存快照、统一归组计数、所有媒体 `desktop` 路由、普通直链/仅下载/受保护分轨/AES-128 HLS、schema 5 迁移、Chrome/Firefox 清单和所有 JavaScript 语法通过。
- [-] B 站公共 DASH 已完成真实分轨拉流、本机合并和 ffprobe；扩展工具栏中的可见选择与 Eagle 实机点击待用户复验。
- [-] 直链、HLS、AES-128、DASH 有自动或公开站点证据；直播停止有本机状态机测试；缓存与录制的真实授权内容证据待用户复验。
- [x] DRM 阻断、敏感字段内存化/脱敏、重启后拒绝猜测 URL、任务临时根和外部路线退出可见界面通过自动检查。
- [x] 0.6.0 数据、配对、网站规则和 IDM 设置升级/故障回滚无损。
- [x] README、开发、验收、安全、安装、状态、架构、决策、许可和任务文档已按 schema 5 行为更新。
- [-] A96–A100、A102–A112 已由实现和自动检查通过；A101 与新载荷覆盖安装、桌面窗口截图、最终重建与哈希收口待完成。
