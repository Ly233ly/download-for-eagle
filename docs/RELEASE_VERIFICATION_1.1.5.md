# 下载中转站 1.1.5 验证报告

验证日期：2026-07-19  
状态：自动门禁与当前电脑安装通过；Chrome popup 最后一项真实任务闭环待用户完成配对后复验。

## 故障复现与根因

- Chrome `Default` 配置实际加载 `<仓库>\chrome-extension`，扩展 ID 为 `phochakdmmmehfamipieafeiigencilf`，版本最初为 1.1.4。
- 仓库开发副本的 `bootstrap.js` 为空；正式安装副本包含 64 字符单机凭据，且其 SHA-256 与未过期的本机恢复文件匹配。开发副本不携带本机密钥属于安全设计，不得把正式凭据复制回源码。
- 截图中的顶部状态为“需要配对”。旧 UI 只禁用“下载并导入 Eagle”，仍允许点击“仅下载”。`downloadOnlyForGroup` 校验失败后返回，外层却无条件显示“下载已开始”。
- 故障点击后 SQLite `download_plans` 仍为 8 条，最新记录仍是此前 Tmall 的 `completed_local/100`，证明没有创建新计划；任务消失不是桌面筛选问题，而是请求从未到达服务端。

## 修复与回归

- 先加入失败测试：调用不存在的 `startValidatedTask` 时 Node 明确失败。实现后，未配对校验不会调用计划创建器；有效校验只调用一次并返回真实计划。
- 单项和批量“仅下载”使用与主按钮相同的校验结果决定是否禁用。
- 成功提示只在 `downloadOnlyForGroup` 返回真实计划对象后出现；校验早退返回 `null`，不会切换任务页或显示假成功。
- service worker 增加 `autoPair` 消息；popup 每次连接检查在显示“需要配对”前主动重试一次安装器 bootstrap。

## 自动与发行门禁

- `python -m unittest discover -s tests -p "test_*.py" -v`：88/88 通过。
- 扩展全部 JavaScript 通过 `node --check`；Chrome/Firefox 清单均可解析且版本为 1.1.5。
- 冻结运行时通过：`version=1.1.5`、`extensionProtocol=1`、`databaseSchema=5`、`downloadEngine=desktop_ffmpeg`、`mediaReady=true`；IDM 接收模式产生 1 条测试任务。
- 隔离安装器通过全新安装、成功升级、bootstrap 轮换、故障注入回滚和卸载；旧程序恢复、测试 IDM 设置恢复及备份清理均通过。
- 当前电脑已静默覆盖安装 1.1.5；`/health`、安装目录清单和四个关键扩展文件哈希与源码一致。
- Chrome 扩展管理页已执行“重新加载”，卡片版本从 1.1.4 更新为 1.1.5。

## 待完成的 Chrome 闭环

Chrome 控制接口的安全策略拒绝直接访问 `chrome-extension://.../popup.html`，并禁止改用其他自动化表面绕过；因此没有伪造 popup 实测证据。桌面“复制配对码”已执行，配对码保留在剪贴板。用户需要打开工具栏扩展，在设置中粘贴六位码完成配对，然后点击当前媒体的“仅下载”。验收需同时确认：

1. 顶部显示“已连接”，任务徽标不再固定为 0。
2. 点击后 popup 与桌面同时出现一个新计划，不再仅显示 toast。
3. 任务进度来自桌面，完成为 `completed_local/100`。
4. 完成卡显示最终路径，“打开所在文件夹”打开程序拥有的 `下载中转站/已完成`。

完成上述四项后，把 TASKS 任务 34 与 A130 改为通过，并补记真实 `planId`、最终文件和任务计数。

## 发行物

- ZIP：`release/下载中转站-1.1.5-Windows-x64/下载中转站-1.1.5-Windows-x64.zip`
- 大小：93,355,002 字节
- SHA-256：`a4f8348cb467440e10fa1b28ca07c97f3c34b3d818eef59950508f6aa699b31a`
- PyInstaller：6.21.0
- FFmpeg/ffprobe：8.1.2
