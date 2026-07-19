# 05 — 建立本机 FFmpeg 下载与合并引擎

- Status: completed
- Tracking: 下载中转站 1.0.0 一次性交付任务 05。
- Evidence: 固定 FFmpeg 8.1.2 哈希、真实直链/受保护分轨/AES-128 HLS、streamcopy、ffprobe 和取消测试。
- Type: AFK
User stories: US3、US4、US7、US8

## What to build

提供统一本机任务：安装包内固定版本 FFmpeg/ffprobe 直接拉取普通直链、分离音视频和 HLS/DASH，优先 streamcopy。任务进入同一下载方案、字节/阶段进度、取消、输出校验、预览和可选 Eagle 队列；浏览器/WASM 和第三方在线合并路线已由任务 17 取代并退出可见流程。

## Acceptance criteria

- [x] 本机 FFmpeg/ffprobe 版本、哈希、许可证和执行路径固定且可验证，命令参数不经过 shell 拼接。
- [x] 两个独立音视频文件可用显式 stream mapping 和 `-c copy` 合并，画质/音质不重编码。
- [x] 容器不兼容时先建议 MKV/其他兼容容器，只有用户确认才转码。
- [x] 合并展示阶段、速度、已处理时长、取消和可理解错误；取消后不产生可导入伪成品。
- [x] 大文件、私密内容、普通直链、分轨和清单全部使用本机 FFmpeg，不向第三方处理页上传媒体。
- [x] “仅下载”和“下载并导入 Eagle”使用相同引擎；区别只在输出完成后是否建立 Eagle job。
- [x] 运行时 Referer/Origin/User-Agent/Authorization/Cookie 只按白名单保存在任务内存，终态或重启后失效。
- [x] 输出通过 ffprobe 流数量、时长和容器检查后才进入 Eagle 导入队列。

## Blocked by

- 01 — 锁定 GPL、源码来源与第三方许可门禁。
- 02 — 打通“可见普通媒体 → 下载 → Eagle”首条纵向链路。
