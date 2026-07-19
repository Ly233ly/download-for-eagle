# 方案 2 弹窗设计 QA

- source visual truth path: `docs/evidence/ui-redesign/02-selected-direction.png`
- implementation screenshot path: unavailable
- viewport: 660×574 CSS px（目标）；实际 Chrome popup 截图尚未取得
- state: 当前页面已捕获一个包含多路视频与音频的非 DRM 内容组
- full-view comparison evidence: blocked；选定稿已打开并保存，但 Chrome 实际工具栏 popup 尚未由用户截图，不能用代码或替代页面冒充实现证据
- focused region comparison evidence: blocked；缺少同状态实现截图，无法可靠检查轨道选择、主动作、任务标签和滚动区域

**Findings**

- [P1] 缺少 Chrome 实际弹窗视觉证据
  Location: Chrome 工具栏中的下载中转站 popup。
  Evidence: 选定方案 2 有 1346×1169 原始设计图；覆盖安装后的实现文件和健康门已验证，但浏览器内部扩展弹窗无法由当前控制接口捕获。
  Impact: 无法确认字体、裁切、间距、图标、滚动与真实动态数据在 660×574 视口中的最终表现。
  Fix: 在 Chrome 重新加载已解压扩展，打开一个已捕获分轨媒体的 popup，截取完整弹窗并保存为 `docs/evidence/ui-redesign/03-implemented-popup.png`；与选定稿放进同一比较输入后修正所有 P0/P1/P2。

**Open Questions**

- 真实页面捕获数据的标题长度、封面比例和音轨数量是否会触发滚动或截断，需要实现截图确认。

**Implementation Checklist**

- [x] 方案 2 代码实现与 1.1.0 覆盖安装；1.1.1 单运行时与真实帧补丁已实现。
- [x] schema 5 源码 81 项测试、脚本语法和双清单验证。
- [x] schema 5 冻结运行时、安装回滚、覆盖安装、健康门和桌面双标签 UI 验证。
- [ ] 获取 Chrome 实际 popup 的 660×574 完整截图。
- [ ] 将参考图与实现截图放入同一比较输入，检查五个必查表面：字体、间距、颜色、图片质量、文案。
- [ ] 检查媒体/任务/工具、设置、筛选、空、离线、DRM 和进行中状态；修复所有 P0/P1/P2 后重新截图比较。

**Follow-up Polish**

- 只有实际比较通过后再记录 P3 微调；当前不从代码推测视觉结论。

## Comparison History

- 2026-07-18 pass 0: 源视觉可用，实现已安装；因缺少 Chrome 实际 popup 截图而阻断，未进行虚假的分离视图比较。
- 2026-07-18 pass 1: 用户提供抖音和 Behance 实机截图，确认候选错误复用 favicon、首次快照与计数不同步；已修复并加入 A104–A105，schema 5 已覆盖安装，待用同两类页面重拍最终 popup 证据。

final result: blocked
