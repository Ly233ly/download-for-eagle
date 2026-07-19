# 31 通用任务预览

状态：完成  
验收：A127

## 目标

所有站点使用同一预览能力链；Behance、Tmall、Douyin 等只作为测试样本，不成为域名分支。

## 实现与验收

- 创建方案时把通用 `video` 当前帧或播放器矩形裁剪以 `planId` 绑定到 popup 内存。
- popup 重开后从本机任务 `preview_path` 恢复 FFmpeg 抽取的实际视频帧。
- 认证接口只读取程序 `预览` 根中的 PNG，限制为 2 MB；不接受客户端路径，不写长期 data URL。
- 自动检查确认任务 UI 不含示例域名判断；Chrome 现场确认 Tmall 标准 `<video>` 可被通用选择器识别。
