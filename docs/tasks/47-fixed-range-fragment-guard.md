# 47 固定 Range 分片双层阻断

状态：实现、定向回归、1.1.12 全量发行与当前电脑安装通过，等待 Chrome 实机闭环。

## 现场证据

- 完整任务：Vimeo HLS `playlist.m3u8`，输出 MKV，下载与 Eagle 导入成功。
- 失败任务一：URL 路径解码为 `range=9207009-13484176`，记录大小 4,277,168 字节，精确等于区间长度。
- 失败任务二：URL 路径解码为 `range=3402514-6864731`，记录大小 3,462,218 字节，同样精确等于区间长度。
- 两条任务都在 FFmpeg 打开输入阶段以 `Invalid data found when processing input` 失败；它们是片段，不是损坏的完整 MP4。

## 实现

- 扩展识别 `range/bytes=start-end` 的查询参数、路径明文与 base64url 路径段，并要求已知候选大小等于区间长度。
- 固定 Range MP4 进入既有传输分片模型：有完整清单时隐藏，仅有分片时保留一个不可提交代表并提示继续发现清单。
- 本机 `MediaCoordinator` 在写入计划前复验；旧扩展或异常客户端提交时返回 `fixed_range_fragment`，不创建数据库任务。
- 本机重试执行前再次复验，升级前已经驻留内存的失败上下文也不再调用 FFmpeg。
- 不使用 Behance、Vimeo 或其他域名白名单；普通支持 Range 的完整 URL不会因为一次 HTTP 206 就被误判，只有 URL 本身固定了区间且长度吻合才阻断。

## 验收

- 现场形式的 base64url Range MP4 在 UI 中为 `segmentOnly`，创建校验返回 `segment_only`。
- 同组加入 M3U8 后，版本列表只剩清单。
- 本机直接收到相同 URL 时同步抛出 `fixed_range_fragment`，计划表保持为空。
- 普通完整 MP4 与显式结构化分轨不受影响。

对应验收：A143。
