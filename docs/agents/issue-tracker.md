# Issue tracker：本地 Markdown

本仓库不自动向 GitHub Issues 发布任务。`TASKS.md` 是面向维护者的任务总览，完整 PRD 和可独立领取的实现任务保存在 `.scratch/`。

## 约定

- 一个功能一个目录：`.scratch/<feature-slug>/`。
- 功能需求文档：`.scratch/<feature-slug>/PRD.md`。
- 实现任务：`.scratch/<feature-slug>/issues/<NN>-<slug>.md`，从 `01` 开始编号。
- 每个任务在文件顶部记录 `Status:`、`Type:`，并在 `Blocked by` 段记录依赖。
- `TASKS.md` 只保留状态、标题和详细任务链接，避免两套验收标准漂移。
- 讨论记录追加到任务文件底部的 `## Comments`。

当技能要求“发布到 issue tracker”时，创建或更新上述 Markdown 文件；除非用户明确授权，不调用 `gh issue create`。
