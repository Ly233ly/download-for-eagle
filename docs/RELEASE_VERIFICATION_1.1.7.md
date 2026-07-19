# 下载中转站 1.1.7 验证报告

验证日期：2026-07-19  
状态：共享状态串行化、完整自动门禁、发行构建与当前电脑覆盖安装通过；真实 Chrome 配对仍因认证 GET 401 失败，A134 未通过，由 1.1.8 接替。

## 1.1.6 实机失败证据

- Chrome 已重载 1.1.6，手动配对后直接提示“尚未配对或配对已失效”。
- 最新非空令牌 T8 的 SHA-256 与服务端当前 `extension_token_hash` 相同，Origin 为同一扩展 ID。
- LevelDB 下一条状态记录把令牌改为空，而最近任务 ID 长度和 `queued` 状态保持不变。
- 结论：服务端配对成功；共享状态的另一个旧快照写回覆盖了新令牌。

## 修复与回归

- `tests/js/test_auth_race.js` 扩展为真实并发状态更新和原子条件清除；新增 API 前按预期失败。
- `createStateUpdateQueue` 串行化所有共享状态读改写。
- 来源队列追加/消费和 401 compare-and-clear 使用函数式补丁，在最新状态上计算。
- 定向 Node 与 Python 扩展回归已通过。

## 自动与发行门禁

- 全量 unittest 共 89 项通过；扩展 JavaScript 语法、Chrome/Firefox 双清单解析和认证竞态 Node 回归均包含在门禁内。
- 冻结运行时通过：`version=1.1.7`、`extensionProtocol=1`、`databaseSchema=5`、`mediaReady=true`、`downloadEngine=desktop_ffmpeg`，IDM 接收器退出码为 0 且生成 1 个任务。
- 隔离安装器的新装、升级、注入失败回滚和卸载全部通过；FFmpeg/ffprobe、自动配对引导和 IDM 归属保护均通过。
- 当前电脑已覆盖安装；在线 `/health` 返回 1.1.7、协议 1、schema 5、`desktop_ffmpeg` 和媒体工具就绪。
- 安装目录扩展清单为 1.1.7；`manifest.json`、`background.js`、`eagle-bridge.js`、`eagle-bridge-ui.js`、`eagle-bridge-auth-logic.js` 与仓库源码 SHA-256 全部一致。

## Chrome 实机闭环

实际结果：步骤 2 失败。服务端接受配对 POST、轮换六位码并保存新令牌哈希；Chrome 存储的倒数第二条令牌与服务端哈希完全匹配，下一条却为空。直接探针证明带正确 Origin 与令牌的 GET 为 200，缺少 Origin 的 GET 为 401；当前 popup 的受认证健康检查使用 GET，因此触发条件清除。以下原计划不再在 1.1.7 继续执行：

1. 重载实际加载的 1.1.7 解压扩展。
2. 输入桌面当前六位码；受认证健康检查通过后才显示“配对完成”。
3. 关闭并重新打开设置，顶部仍显示“已连接”。
4. 点击“仅下载”，popup 与桌面出现同一个新任务。
5. 最终为 `completed_local/100`，显示保存路径且可打开文件夹。

## 发行物

- ZIP：`release/下载中转站-1.1.7-Windows-x64/下载中转站-1.1.7-Windows-x64.zip`
- 大小：93,369,775 字节
- SHA-256：`b4c8bbbca54e192889f7e95a014915abf70e5a0c096ef7d036de1845d35a1bbd`
- PyInstaller：6.21.0
- FFmpeg/ffprobe：8.1.2
