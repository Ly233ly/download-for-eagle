# 下载中转站 1.1.4 验证报告

验证时间：2026-07-19（Asia/Shanghai）

## 修复范围

- popup 不再把方案创建时的 `queued/0` 当作永久状态；`completed_local` 和 `imported` 强制显示 100%。轮询失败会显示同步中断并自动重连。
- 扩展令牌收到 401 后清除失效值并尝试安装器 bootstrap 自动配对；成功升级在所有健康门完成后轮换一份新的单次凭据，失败则进入明确配对态。
- “仅下载”任务显示最终完整路径，并可通过任务 ID 打开经服务端归属校验的 `下载中转站/已完成` 目录。
- 任务创建时绑定通用当前视频帧；popup 重开后从认证接口读取本机 FFmpeg 生成的 PNG。实现不包含 Behance、Tmall、Douyin 等域名判断。

## 现场诊断证据

- Tmall 示例页在 Chrome 中存在标准可见 `<video>`，可见矩形为 820×615；因此缺图不是网站白名单或页面无视频。
- 同一真实任务在桌面 SQLite 中为 `completed_local/100`，包含存在的 `final_path` 与 `preview_path`；旧 popup 同时显示“助手离线/等待本机下载/0%”，证明断点位于扩展同步与预览交接。
- 下载前的瞬时帧仍不写 SQLite；下载后的 PNG 只允许从程序 `预览` 根读取，限制为 PNG 且不超过 2 MB。

## 自动验证

- 88 项 Python unittest 全部通过；其中新增完成态钳制、预览路径归属、输出路径归属、认证预览/打开目录接口和站点无关性覆盖。
- 全部扩展 JavaScript 通过 `node --check`；Chrome/Firefox 清单可解析且版本均为 1.1.4。
- 冻结运行时通过：`version=1.1.4`、`extensionProtocol=1`、`databaseSchema=5`、`downloadEngine=desktop_ffmpeg`、`mediaReady=true`，FFmpeg/ffprobe 均随包提供，IDM 接收模式持久化一条任务。
- 隔离安装器通过全新安装、成功升级、故障注入回滚和卸载；成功升级轮换 bootstrap，故障回滚发生在轮换前，旧文件删除、备份清理和 IDM 配置恢复均通过。

## 当前电脑覆盖安装

- 已原子覆盖安装到 `%LOCALAPPDATA%\IDM-Eagle自动导入助手`；后台 `/health` 为 1.1.4、媒体工具就绪，安装目录扩展清单为 1.1.4。最终安装器实测 `BootstrapRotated=true` 且恢复凭据文件已准备。
- `eagle-bridge.js`、`eagle-bridge-ui.js`、`eagle-bridge-ui-logic.js`、`eagle-bridge.css` 的安装目录 SHA-256 与源码逐一相同。
- 覆盖后旧 Tmall 任务仍为 `completed_local/100`，最终文件路径和本机预览路径均保留。

Chrome 已加载的解压扩展需要在 `chrome://extensions` 点一次“重新加载”，或等待扩展的补丁升级自重载，才能让当前 service worker 和 popup 同时切换到 1.1.4。A101 的同视口最终视觉截图仍属于人工视觉验收，不用静态页面代替。

本验证报告本身不复制进同版本对应源码包，避免报告中的 ZIP 哈希反过来改变该 ZIP；仓库和 GitHub Release 保留本报告，发行包仍包含全部构建所需源码、历史验证材料和构建脚本。

## 发行物

- ZIP：`release/下载中转站-1.1.4-Windows-x64/下载中转站-1.1.4-Windows-x64.zip`
- 大小：93,347,834 字节
- SHA-256：`38c3a0e737094387f715d111520324f29348eaaa4d2e8501b303521366338d27`
- 构建工具：PyInstaller 6.21.0、FFmpeg 8.1.2
