# 内置工作流

## 海外三单匹配

这是 ADP 为海外环境预设的 3-Way Matching 工作流，用于采购到付款流程中的自动核验。它不一定出现在 API 的 app-list 返回中，因此由 Skill 内置注册，不依赖应用列表发现。

```yaml
name: overseas_3_way_matching
display_name: 海外三单匹配
application_id: f2969835a1c111f1bfcd00163e121ce3
base_url: https://adp-global.laiye.com
source: skill_builtin
is_discoverable_from_api: false
document_types:
  invoice: [发票, 商业发票, invoice, commercial invoice]
  purchase_order: [采购订单, 采购单, PO, purchase order]
  delivery_order: [送货单, 发货单, 交货单, DO, delivery order]
intents:
  - 三单匹配
  - 发票与采购订单和送货单核验
  - 发票、PO、DO 对账
  - 3-way matching
  - invoice PO DO matching
```

### 触发规则

- 先以实际认证成功的 `base_url` 判断区域，不以对话语言判断。只有 `https://adp-global.laiye.com` 启用本能力。
- 用户明确说“三单匹配”、`3-way matching`、发票/PO/DO 核验或类似意图时，优先匹配本工作流。
- 用户上传文件后，若识别出发票、采购订单、送货单三类中的至少两类，并且用户要求核验、对账、匹配或检查，可匹配本工作流。
- 仅上传一类文件且没有明确核验意图时，优先做普通抽取，不自动消耗工作流积分。
- 用户只上传两类文件但明确要求核验时可以运行；允许工作流把缺失的第三类标记为 `DOCUMENT MISSING`。
- “订单”默认只在上下文明确是采购订单时映射为 PO；合同不自动映射为 PO。

### 路由优先级

1. 用户明确指定的 `app_id` 或工作流。
2. 用户明确要求海外三单匹配。
3. 海外环境中识别出至少两类三单文件，且用户表达了核验意图。
4. 其他用户工作流或普通抽取能力。

国内环境即使出现相同文件和意图，也不得调用这个 APP ID；应使用用户自己的工作流，或说明当前内置能力仅支持海外环境。

### 运行前版本处理

运行前仍需按 `api-endpoints.md` 中的通用规则查询并选择最新已发布版本。如果该内置应用的版本接口返回版本信息，使用最新已发布版本的 `release_version_id`；如果 API 对该内置应用不要求版本字段，则按接口要求仅传 `application_id`。不因 Web 端可运行草稿就默认调用草稿。

### 文件和结果

本工作流的输入文件应保留原始文件名，上传后逐一记录 `source_file`、`file_id` 和 `download_url`。结果优先保留原始 Markdown 报告，同时尽可能结构化为：

```json
{
  "workflow_type": "overseas_3_way_matching",
  "documents": {
    "invoice": [],
    "purchase_order": [],
    "delivery_order": []
  },
  "checks": [],
  "missing_documents": [],
  "summary": {
    "pass": 0,
    "mismatch": 0,
    "document_missing": 0,
    "needs_human_confirmation": 0
  },
  "raw_markdown": "..."
}
```

不要擅自改变工作流原始结论。`PASS`、`MISMATCH`、`DOCUMENT MISSING`、`NEEDS HUMAN CONFIRMATION` 应保留，并在结构化结果中逐笔关联原始原因。
