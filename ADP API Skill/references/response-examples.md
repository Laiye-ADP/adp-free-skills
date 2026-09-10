# ADP API 返回示例

示例中的密钥、用户标识和租户标识均已省略或脱敏。

## 应用列表

```json
{
  "code": "success",
  "message": "",
  "data": {
    "range": { "offset": 0, "size": 1000, "total": 1 },
    "list": [
      {
        "id": "app_abc123",
        "app_name": "文档解析",
        "app_type": 0,
        "ai_function": 1407,
        "ai_engine": 0,
        "app_label": ["文档解析", "OCR"],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "engine_type": "extract"
      }
    ]
  }
}
```

工作流运行记录在提交前应额外保存：

```json
{
  "application_id": "workflow_abc123",
  "release_version_id": "release_20260904_01",
  "release_status": "published",
  "release_selected_by": "latest_published"
}
```

如果积分不足，结果应包含可操作的引导，而不是只返回错误文字：

```json
{
  "status": "insufficient_credits",
  "message": "当前区域积分不足，未继续提交任务。",
  "login_url": "https://adp.laiye.com"
}
```

`app_type=0` 表示系统预设，`app_type=1` 表示自定义应用。

## 文件上传

```json
{
  "code": "success",
  "data": {
    "id": "file_abc123",
    "file_name": "document.pdf",
    "file_size": 123456,
    "content_type": "application/pdf",
    "download_url": "https://adp.laiye.com/web/agentic_engine/laiye/file/file_abc123"
  }
}
```

## 异步任务创建

```json
{
  "code": "success",
  "data": {
    "run_id": "run_abc123",
    "status": "running",
    "output": null,
    "error": null
  }
}
```

## 工作流完成结果

```json
{
  "code": "success",
  "data": {
    "run_id": "run_abc123",
    "status": "succeeded",
    "output": {
      "text": "{\"result\": \"...\"}",
      "output_object": {
        "result": "..."
      },
      "output_schema_valid": true
    },
    "error": null
  }
}
```

## 批量结果格式

```json
{
  "summary": {
    "total": 2,
    "succeeded": 1,
    "failed": 1,
    "pending": 0
  },
  "results": [
    {
      "index": 1,
      "source_file": "BL.pdf",
      "file_id": "file_1",
      "task_id": "task_1",
      "status": "succeeded",
      "result": {}
    },
    {
      "index": 2,
      "source_file": "contract.pdf",
      "file_id": "file_2",
      "task_id": "task_2",
      "status": "failed",
      "error": { "code": "...", "message": "..." }
    }
  ]
}
```
