# 下载中转站 1.1.12 验证报告

验证日期：2026-07-19  
状态：固定 Range 分片双层门禁、全量发行门禁和当前电脑覆盖安装通过；等待 Chrome 实机内容闭环。

## 现场问题

- Behance 同一内容的完整 HLS/MKV 任务成功并导入 Eagle。
- 随后两个 `.mp4` 直链任务都在 2% 报 `Error opening input files: Invalid data found when processing input`。
- 数据库证明两条 URL 分别固定了不同字节区间，记录大小精确等于区间长度，不是完整 MP4。

## 修复与回归

- 扩展候选层把 URL 自身固定的字节区间识别为传输分片，而不再只看 `.m4s/.ts` 后缀。
- 同组有 HLS/DASH 时隐藏；只有分片时阻止提交。
- 本机在计划创建和重试执行前复验，以 `fixed_range_fragment` 拒绝，不启动 FFmpeg。
- 修复前 Node 回归的 `segmentOnly` 为 false、Python 回归没有抛错；实现后两者通过。
- 判定要求 URL 明确编码 Range 且区间长度与候选大小一致，不按网站或 `.mp4` 后缀猜测。

## 自动与发行门禁

- [x] 92 项全量 unittest、全部扩展 JavaScript 语法和 Chrome/Firefox 双清单。
- [x] 构建 1.1.12 发行 ZIP。
- [x] 冻结运行时验证协议 1、schema 5、`desktop_ffmpeg`、媒体工具与 IDM 接收器。
- [x] 隔离安装器的新装、升级、注入失败回滚和卸载。
- [x] 当前电脑覆盖安装、在线健康门与关键文件哈希。

当前在线 `/health` 返回 1.1.12、协议 1、schema 5、`desktop_ffmpeg` 且 `mediaReady=true`。安装目录的扩展门禁、Chrome 清单、桌面程序、IDM hook 和后台程序均与发行包 SHA-256 一致。

## Chrome 实机闭环

1. 在 `chrome://extensions` 重载实际加载的 1.1.12 扩展，再完整刷新现场 Behance 页面。
2. 播放视频直至完整 HLS/DASH 被发现，确认固定 Range MP4 不出现在可下载版本中。
3. 若只捕获到分片，下载按钮必须阻断并提示继续播放或查找清单，不能创建本机任务。
4. 选择完整清单执行下载，任务达到正确 100% 终态并可打开目录。
5. 重复打开 popup 和继续播放，不得新增 `desktop_download_failed/2%` 的 MP4 任务。

## 发行物

- ZIP：`release/下载中转站-1.1.12-Windows-x64/下载中转站-1.1.12-Windows-x64.zip`。
- 大小：93,415,850 字节。
- SHA-256：`298e46add8bd8699c4f4302c2f5f23073f0b6a04bf985a362aed0c385e7df5b3`。
- PyInstaller：6.21.0（隔离、固定版本构建环境）。
- FFmpeg/ffprobe：8.1.2。
