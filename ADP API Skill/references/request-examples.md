# ADP API 请求示例

以下示例使用占位符，不要把真实 API Key 写入代码或提交到仓库。

## 查询应用列表

```bash
curl -G "https://adp.laiye.com/open/agentic_doc_processor/laiye/v1/app-list" \
  -H "X-API-KEY: ${ADP_API_KEY}" \
  --data-urlencode "offset=0" \
  --data-urlencode "limit=1000" \
  --data-urlencode "with_extra=1"
```

## 上传工作流文件

```bash
curl -X POST "https://adp.laiye.com/open/agentic_engine/laiye/files/upload" \
  -H "X-API-Key: ${ADP_API_KEY}" \
  -F "chunk=@BL.pdf"
```

## 同步文档抽取

适用于单个小文件或用户明确要求快速返回。同步响应可能没有 `task_id`，应直接检查顶层 `code`、`message`、`data`，不要强行进入任务轮询。

```bash
curl -X POST \
  "https://adp.laiye.com/open/agentic_doc_processor/laiye/v1/app/doc/extract" \
  -H "X-API-KEY: ${ADP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "<extract_app_id>",
    "file_url": "<file_url>"
  }'
```

## 异步文档解析

适用于大文件、长流程或批处理中的长任务；只有创建响应返回任务 ID 后才轮询。

```bash
curl -X POST \
  "https://adp.laiye.com/open/agentic_doc_processor/laiye/v1/app/doc/recognize/create/task" \
  -H "X-API-KEY: ${ADP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "<parse_app_id>",
    "file_url": "<file_url>"
  }'
```

## 同步运行工作流

```bash
curl -X POST \
  "https://adp.laiye.com/open/agentic_engine/laiye/v1/app/run" \
  -H "X-API-Key: ${ADP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "<workflow_app_id>",
    "files": [
      {
        "url": "<uploaded_download_url>",
        "name": "BL.pdf",
        "mime_type": "application/pdf",
        "size": 123456
      }
    ],
    "inputs": {}
  }'
```

## 异步运行工作流

```bash
curl -X POST \
  "https://adp.laiye.com/open/agentic_engine/laiye/v1/app/run/create/task" \
  -H "X-API-Key: ${ADP_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": "<workflow_app_id>",
    "files": [],
    "inputs": {}
  }'
```

查询异步工作流：

```bash
curl -X GET \
  "https://adp.laiye.com/open/agentic_engine/laiye/v1/app/run/query/task/<run_id>" \
  -H "X-API-Key: ${ADP_API_KEY}"
```

## 批量提交账本（伪代码）

```text
for each source_file:
  upload -> file_id/download_url
  choose sync for small/fast, async for long task
  record source_file + file_id + (task_id/run_id if returned) + submitted_at
  if accepted: never submit this source_file again
  if async id exists: poll and record output/error

output = {
  summary: {total, succeeded, failed, submission_unknown, pending},
  results: [{source_file, file_id, task_id/run_id, status, duration_ms, result/error}]
}
```
