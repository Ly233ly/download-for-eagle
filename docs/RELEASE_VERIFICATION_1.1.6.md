# 下载中转站 1.1.6 验证报告

验证日期：2026-07-19  
状态：自动门禁、构建、安装与扩展重载通过；真实配对仍失败，A132 未通过，已由 1.1.7 接替。

## 故障复现与根因

- 用户完成六位码配对后，toast 显示成功，但同一视图仍提示“请先连接本机软件”，重开设置又回到配对输入。
- Chrome `Default` 配置加载仓库开发副本，扩展 ID `phochakdmmmehfamipieafeiigencilf`；服务端保存的 Origin 完全一致。
- 扩展 LevelDB 中 `downloadTransferStation.token` 最近记录反复为长度 43 与 0；最后一个非空令牌摘要与服务端当前摘要相同。
- 根因是配对前的旧请求在新令牌持久化后返回 401，旧代码无条件清空当前令牌。令牌本身、服务端摘要、Origin 和手动配对响应均不是故障点。

## 修复与回归

- 先加入失败测试 `tests/js/test_auth_race.js`；缺少竞态决策模块时按预期失败。
- `unauthorizedAction(requestToken, latestToken)` 规定：发现更新令牌就重试；只有被拒绝令牌仍为当前值时才清除；无可用令牌进入恢复。
- 配对 UI 必须在受认证 `/api/media/health` 和 `authState.paired` 都成功后才显示“配对完成”。
- 定向 Node 与 Python 扩展回归通过。

## 自动与发行门禁

- `python -m unittest discover -s tests -p "test_*.py" -v`：89/89 通过；全部扩展 JavaScript 语法和 Chrome/Firefox 清单通过。
- 冻结运行时通过：`version=1.1.6`、协议 1、schema 5、`desktop_ffmpeg`、媒体工具就绪和 IDM 接收任务。
- 隔离安装器通过全新安装、升级、bootstrap 轮换、故障回滚和卸载。
- 当前电脑覆盖安装后 `/health=1.1.6`；安装目录的清单、后台、bridge、UI 和认证模块与源码 SHA-256 一致。

## Chrome 实机结果

Chrome 重载 1.1.6 后输入六位码，toast 直接显示“尚未配对或配对已失效”，设置仍为需要配对。新取证确认服务端当前令牌与最后非空浏览器令牌一致，但随后另一个共享状态写入把 token 覆盖为空。1.1.6 只修复了 401 分支，没有串行化整个状态对象，因此不满足 A132，不作为最终修复发布。

## 发行物

- ZIP：`release/下载中转站-1.1.6-Windows-x64/下载中转站-1.1.6-Windows-x64.zip`
- 大小：93,363,927 字节
- SHA-256：`3632d6f58a3a74bd08aae7f97e54214c3d484e5a7361a524a1fc2482fb813a3c`
- PyInstaller：6.21.0
- FFmpeg/ffprobe：8.1.2
