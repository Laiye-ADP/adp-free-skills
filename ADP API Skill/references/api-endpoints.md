# ADP OpenAPI 接口速查

Base URL：

- 国内：`https://adp.laiye.com`
- 海外：`https://adp-global.laiye.com`

认证请求头：

```http
X-API-KEY: <API_KEY>
```

## 应用管理

```text
GET /open/agentic_doc_processor/{tenant_name}/v1/app-list
```

常用查询参数：`offset`、`limit`、`app_name`、`app_type`、`ai_function`、`with_extra`。

建议查询：`?offset=0&limit=1000&with_extra=1`。

## 文档解析

```text
POST /open/agentic_doc_processor/{tenant_name}/v1/app/doc/recognize
POST /open/agentic_doc_processor/{tenant_name}/v1/app/doc/recognize/create/task
GET  /open/agentic_doc_processor/{tenant_name}/v1/app/doc/recognize/query/task/{task_id}
```

## 文档抽取

```text
POST /open/agentic_doc_processor/{tenant_name}/v1/app/doc/extract
POST /open/agentic_doc_processor/{tenant_name}/v1/app/doc/extract/create/task
GET  /open/agentic_doc_processor/{tenant_name}/v1/app/doc/extract/query/task/{task_id}
```

## 工作流文件和运行

```text
POST /open/agentic_engine/laiye/files/upload
GET  /open/agentic_engine/laiye/files/{file_id}
POST /open/agentic_engine/laiye/v1/app/run
POST /open/agentic_engine/laiye/v1/app/run/create/task
GET  /open/agentic_engine/laiye/v1/app/run/query/task/{run_id}
POST /open/agentic_engine/laiye/v1/app/run/{run_id}/cancel
POST /open/agentic_engine/laiye/v1/app/run/{run_id}/rerun
```

工作流版本：

- 运行前先从官方 OpenAPI 的“应用详情/版本列表/发布版本”接口获取版本信息；不同 API 版本可能使用不同的资源路径，必须以文档中实际定义的路径和字段为准，不要猜测 URL。
- 从返回结果中过滤已发布版本，按发布时间或版本号选择最新一个，并将其 `release_version_id` 传给运行接口。
- 如果应用详情或版本接口未返回任何已发布版本，才向用户说明并询问是否测试当前草稿；不要静默降级到草稿。

工作流运行请求的关键字段：

```json
{
  "application_id": "<workflow_app_id>",
  "release_version_id": "<latest_published_release_version_id>",
  "files": [
    {
      "url": "<uploaded_download_url>",
      "name": "document.pdf",
      "mime_type": "application/pdf",
      "size": 123456
    }
  ],
  "inputs": {}
}
```

## 账户

```text
GET /open/agentic_doc_processor/{tenant_name}/v1/user/payment
```
