# 下载中转站 1.0.0 验证报告

验证日期：2026-07-18

## 结论

1.0.0 的代码、扩展载荷、FFmpeg、数据库迁移、安装器、对应源码和许可材料已组成一次性交付候选。任务 01–14 完成；任务 15 仍保留两项必须由人完成的发布门：Chrome 工具栏实际视觉/录制点验，以及项目所有者对 GitHub Release 的最终签字。未把这两项伪报为自动通过。

## 自动与公开媒体证据

- Python 全量回归：68/68 通过，包含原 IDM/Eagle 流程、schema 4、候选计划、DRM、敏感上下文、组件归属、停止、AES-128 HLS、真实 FFmpeg 分轨合并和扩展协议健康门。
- 浏览器载荷：全部 JavaScript 通过 `node --check`；Chrome 与 Firefox manifest 通过 JSON 解析；B 站页面 playinfo 转换为一个视频+音频候选组的 Node 测试通过。
- 上游对照：cat-catch 2.7.1 固定提交的 96 个运行时文件全部存在；88 个保持一致，8 个登记入口文件为下载中转站集成修改。
- Apple 公共 HLS：下载 5 秒样本，1,360,101 字节，ffprobe 确认 `h264` 视频和 `aac` 音频。
- B 站公共非 DRM DASH：页面提供 4 个视频和 3 个音频表示；选择 480×852 视频与音频实际拉流并 streamcopy，输出 559,094 字节，ffprobe 确认 `h264` + `aac`。
- 可重跑命令：`python packaging/Verify-PublicMedia.py --ffmpeg media-tools/ffmpeg.exe --ffprobe media-tools/ffprobe.exe --output <临时目录> --evidence <证据文件>`；脱敏结果保存在 [`public-media-1.0.0.json`](evidence/public-media-1.0.0.json)。

## 安装、升级与回滚证据

- `packaging/Test-Installer.ps1` 覆盖全新安装、0.6.0 状态升级、注入失败回滚和卸载；检查旧标记/程序恢复、配对 bootstrap 保留、IDM 原设置恢复及暂存备份清理。
- `packaging/Test-FrozenRuntime.ps1` 覆盖冻结后台进程、`/health` 的版本 1.0.0、schema 4、扩展协议 1、FFmpeg 就绪，以及冻结版 `--receive` 只创建一个任务。
- 脱敏结果分别保存在 [`installer-1.0.0.json`](evidence/installer-1.0.0.json) 和 [`frozen-runtime-1.0.0.json`](evidence/frozen-runtime-1.0.0.json)。
- 正式升级前使用 SQLite 在线备份；升级后执行 `PRAGMA integrity_check`、旧表计数、配对状态、schema 和健康检查，不把数据目录当作程序载荷替换。
- 健康门同时要求 `version=1.0.0`、`databaseSchema=4`、`extensionProtocol=1`、`mediaReady=true`；任一失败即由安装器恢复旧程序目录。
- 最终 ZIP 的字节数与 SHA-256 写在发行目录同名 `.sha256.txt`，二进制逐文件哈希写在包内 `BINARY-INVENTORY.json`。

## 安全与许可证据

- 本机 API 仅监听 loopback，并校验 Chrome/Edge/Firefox 扩展 Origin 与配对令牌。
- 签名 URL 查询参数不入长期表；Cookie、Authorization、Referer、Origin 和 User-Agent 仅在当前受认证清单任务内存中使用；CR/LF 注入被拒绝。
- DRM 计划在创建组件前进入阻断；路径越出任务专属临时目录时拒绝接收或清理；停止计划不会生成可导入伪成品。
- 外部 Aria2、MQTT、send2local、m3u8dl、自定义调用和第三方在线目标默认关闭。
- 组合发行采用 GPL-3.0；固定 cat-catch 上游快照、原许可证、修改说明、项目 MIT 保留通知、FFmpeg 来源/哈希/许可、Python/PyInstaller/Tcl/Tk 通知和完整构建脚本均随包提供。

## 保留的人工发布门

- Chrome 自动控制明确禁止接管 `chrome://extensions` 和扩展工具栏内部页面，也禁止用替代浏览器表面绕过。用户需要亲自在工具栏确认顶部候选卡片显示标题/封面/清晰度/音轨/方案，并用有权处理的内容点验缓存捕获或一种录制模式。
- 安装器仍只能打开扩展管理页和扩展目录；“加载已解压”或重载必须由用户确认，这是 Chrome 安全模型，不是安装器故障。
- 项目所有者完成上述点验后，才把任务 15、A93 和 A95 标为完成并上传 GitHub Release。
