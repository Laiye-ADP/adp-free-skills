# Error Handling Reference / 错误处理参考

## 错误码说明（待技术补充）

由技术补充各接口的错误码及处理规则，供 Agent 判断失败原因并引导用户恢复。需区分 HTTP 状态码与业务错误码，覆盖认证失败、积分不足、文件不支持、应用或模板不可用、并发超限、队列已满、处理失败及超时等情况。

| 错误码 | 含义及触发条件 | 用户提示文案 | Agent 处理方式 | 是否可重试及条件 |
| --- | --- | --- | --- | --- |
| 待技术填写 | 待技术填写 | 待技术填写 | 待技术填写 | 待技术填写 |

处理规则需明确任务是否已接收、是否需要用户操作，以及重试是否可能导致重复处理或扣费。遇到未收录的错误码时，保留实际错误信息，说明当前无法确认的原因，不猜测含义或盲目重试。

## Error Codes (To Be Completed by Engineering)

Engineers should document endpoint error codes and recovery rules so the agent can identify failures and guide recovery. Distinguish HTTP status codes from business error codes. Cover authentication failures, insufficient credits, unsupported files, unavailable apps or templates, concurrency limits, full queues, processing failures, and timeouts.

| Error code | Meaning and triggering conditions | User-facing message | Agent action | Retry eligibility and conditions |
| --- | --- | --- | --- | --- |
| To be completed | To be completed | To be completed | To be completed | To be completed |

Rules must clarify whether the task was accepted, whether user action is required, and whether retrying could cause duplicate processing or charges. For undocumented codes, retain the actual error information and explain what remains unknown without guessing meanings or blindly retrying.

