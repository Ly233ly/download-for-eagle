# 1.2.3 通用内容页解析与字节分片重建验证报告

验证日期：2026-07-19

## 结论

源码、102 项 Python 回归、4 组 Node 逻辑回归、全部扩展 JavaScript 语法、Chrome/Firefox 双清单、冻结运行时和隔离安装器均通过。1.2.3 已覆盖安装到当前电脑，安装目录六个关键扩展文件与源码 SHA-256 一致；在线健康为 `version=1.2.3`、schema 5、协议 1、`desktop_ffmpeg`、FFmpeg 与 yt-dlp/Deno 均就绪。

Windows Computer Use 在准备读取 Chrome 扩展管理页时因无法高置信确认当前浏览器 URL而按安全策略停止，因此没有自动点击受保护的扩展“重新加载”按钮，也没有代替用户点击 Instagram 的最终下载按钮。A163 的最后一项仍是 Chrome 手动重载后的现场内容/下载一致性确认；这不会改变自动门禁已完成的结论。

## 根因证据

- 当前 Instagram 页面观测到 121 个视频请求，地址以 `bytestart/byteend` 表示固定字节区间。
- 失败任务保存 172,979 字节；现场请求 `886–173864` 的区间长度也是 172,979，证明任务输入只是播放分片。
- 同一签名地址只删除 `bytestart/byteend`、保留 `efg` 和签名参数后，服务器可按标准 HTTP Range 返回媒体字节；原分片地址仅返回声明区间。
- 页面 DOM 的视频为 `blob:`，但最近 `article` 提供稳定 `/p/<id>` 或 `/reels/<id>` 永久链接。因此网络分片不应冒充完整视频，稳定内容页应成为用户可见候选。

## 已实现门禁

- 扩展和桌面双层识别 `bytestart/byteend`、`range/bytes/start/end` 及路径区间，原始分片不能进入 FFmpeg。
- Instagram `efg` 元数据按精确字符串资产 ID 归组，避免大整数精度丢失；分轨角色、时长、码率和完整大小估算进入候选模型。
- blob 视频从最近内容容器选择同源稳定永久链接，生成带当前帧、标题、时长和尺寸的 `resolver=page` 候选。
- 永久链接矩阵覆盖 Instagram 帖子/Reels/Story、TikTok、抖音 `modal_id`、X status、Reddit comments、Facebook Watch 和 Pinterest pin；无稳定身份的主页不猜测。
- 桌面固定 yt-dlp 2026.06.09 + Deno 2.8.1 解析最佳 MP4/M4A，再进入统一 FFmpeg 8.1.2/FFprobe 状态机。
- 解析上下文只在内存；Cookie 上限 16 KiB，写入任务临时 Netscape 文件并在 `finally` 删除，不进入数据库、命令行、错误或诊断。页面解析拒绝 localhost 和字面非公网 IP。
- 同页已有稳定页面解析候选时，重建地址退入技术分片分区，默认列表不再堆叠小文件假视频。

## 自动验证

- `python -m unittest discover -s tests -p "test_*.py" -v`：102/102 通过。
- `test_youtube.js`、`test_popup_logic.js`、`test_candidate_presentation.js`、`test_auth_race.js`：全部通过。
- 全部扩展 `.js`：`node --check` 通过；两个 manifest JSON 解析通过，版本均为 1.2.3。
- 冻结运行时：健康、schema 5、FFmpeg/ffprobe、yt-dlp/Deno、IDM `--receive` 和唯一任务持久化通过；证据为 `.scratch/frozen-runtime-1.2.3-evidence.json`。
- 隔离安装器：全新安装、覆盖更新、强制失败回滚和卸载全部通过；证据为 `.scratch/installer-1.2.3-evidence.json`。
- 当前电脑：安装清单及候选/分组/background/content/bridge 六个文件与源码哈希一致；在线 `/health` 全部门禁通过。

## 发行物

- 目录：`release/下载中转站-1.2.3-Windows-x64/下载中转站-1.2.3`
- ZIP：`release/下载中转站-1.2.3-Windows-x64/下载中转站-1.2.3-Windows-x64.zip`
- 大小：164,398,184 字节
- SHA-256：`a0b038d7763fe087e59e908845182cb59fe39b5453fa0d8692f8a6c6ec0e8d9d`

## 最后人工闭环

1. 在 `chrome://extensions` 对实际加载的“下载中转站”点击一次“重新加载”，确认路径为安装目录或当前仓库预期副本。
2. 刷新 Instagram 来源页并播放目标视频；默认媒体列表应显示内容级标题、当前帧和时长，不显示 169 KB/288 KB 分片。
3. 点击“仅下载”，确认任务进入页面解析/下载而不是在 2% 报 `Invalid data`；完成后打开目录，用任务预览和最终视频核对所选内容一致。
