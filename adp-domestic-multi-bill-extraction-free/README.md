<div align="center">

# 🚀 Laiye ADP Domestic Multi-Bill Extraction · Free for Limited Time

Developed by the Laiye ADP (Agentic Document Processing) team, this solution delivers high-precision intelligent extraction for common China domestic invoices, bills and vouchers, tailored for **finance reimbursement, bookkeeping, bill archiving, travel expense automation and system integration scenarios**. It supports VAT invoices, transportation tickets, fiscal bills, medical invoices, customs documents, toll invoices, taxi tickets, train tickets and other common reimbursement documents, and returns standardized structured JSON data to facilitate business workflow integration and downstream automation.

</div>

## ⭐ Why choose ADP?
✅ China Domestic Bill Solution  
📄 Supports 30+ common China invoice and bill types  
🎯 Automatic document classification and structured extraction  
⚡ No login, no API key, ready for quick trials  
🔒 Public URL SSRF protection and controlled free quotas  
🤖 Upgrade path to full ADP workflows and optimization  

> Laiye ADP APIs are **100% free** for a limited time. Limited quota available, first come, first served!

## 📌 Target Scenarios
| User Group | Usage Scenario |
| ---- | ---- |
| Finance Teams | Extract key data from China domestic invoices and reimbursement documents for expense claims, bookkeeping and supplier settlement. |
| Agent Users | Install ADP Skill with one click on OpenAI GPTs, Anthropic Claude, Google Gemini Agent Builder, Microsoft Copilot Studio and Hermes for automated document parsing. |
| Developers | Call the no-login public API to quickly verify China invoice and bill extraction before integrating the full ADP service. |

## 📄 Quick Start Guide

### Step 1: Select Base URL
We offer dedicated public cloud access endpoints for domestic and international users, with separate regional configurations. Connecting to the nearest node ensures fast and stable network calls. No account registration or API Key is required — you may send requests directly to the endpoints listed below.

| Environment | API Endpoint |
|------|---------|
| **China** | `https://adp.laiye.com/public/v1/domestic-multi-bill/extract` |
| **Global** | `https://adp-global.laiye.com/public/v1/domestic-multi-bill/extract` |

Users in Chinese Mainland should prefer the China endpoint.

### Step 2: Send Request

Send a `POST` request with exactly one of `file_url` or `file_base64`.

| Field | Type | Description |
| --- | --- | --- |
| `file_url` | string | Public HTTP/HTTPS file URL. Private network and internal IP URLs are blocked. |
| `file_base64` | string | Base64-encoded file content. Data URL prefixes are accepted. |

#### Method 1: File URL

```bash
curl -X POST "https://adp.laiye.com/public/v1/domestic-multi-bill/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://example.com/china-invoice.pdf"
  }'
```

#### Method 2: Base64 Encoded File Content

```bash
curl -X POST "https://adp.laiye.com/public/v1/domestic-multi-bill/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "file_base64": "<base64-encoded-file-content>"
  }'
```

#### Request Example in Python:

```python
import base64
import requests

with open("china_invoice.pdf", "rb") as f:
    file_base64 = base64.b64encode(f.read()).decode("utf-8")

response = requests.post(
    "https://adp.laiye.com/public/v1/domestic-multi-bill/extract",
    json={"file_base64": file_base64},
    timeout=180,
)
print(response.json())
```

### Step 3: Result Example

| Field | Type | Description |
| --- | --- | --- |
| `success` | boolean | Whether the request succeeded. |
| `extraction_result` | array | Extraction results grouped by document type. |
| `aigc` | object | AIGC processing label information. |
| `upgrade_message` | string | Upgrade prompt for the full ADP product. |
| `signup_url` | string | Registration page URL. |

Example:

```json
{
  "success": true,
  "extraction_result": [
    {
      "field_key": "vat_electronic_invoice_new",
      "field_name": "电子发票普通发票",
      "object_values": [
        {
          "document_type": "vat_electronic_invoice_new",
          "pages": [0],
          "extraction_result": [
            {
              "field_key": "invoice_number",
              "field_name": "发票号码",
              "field_values": [
                {
                  "field_value": "24142000000000000000",
                  "field_confidence": 0.98
                }
              ]
            }
          ]
        }
      ]
    }
  ],
  "upgrade_message": "注册即可获得100积分/月，解锁全部能力，含多层税率计算+识别能力自主进化+更多字段与更高性能",
  "signup_url": "https://adp.laiye.com/"
}
```

Parsing guidance:

- The top-level `extraction_result` is grouped by document type.
- Each group's `field_key` is the document `type_key`.
- Each `object_values` item represents one recognized bill instance.
- Normal fields use `field_values`; table fields use `table_values`.
- The free API has no field-count limit. Returned fields vary by document type.
- Unknown or low-confidence documents may be returned as `other`.

## Supported Document Types

| `type_key` | Document type |
| --- | --- |
| `air_transport` | Air transport itinerary |
| `custom_declaration_form` | Customs declaration form |
| `customs_payment_form` | Customs payment form |
| `electronic_air_transport` | Electronic air transport itinerary invoice |
| `electronic_motor_vehicle_sale_invoice` | Electronic motor vehicle sales invoice |
| `electronic_train_ticket` | Electronic railway ticket invoice |
| `electronic_used_car_purchase_invoice` | Electronic used car sales invoice |
| `fiscal_paper` | Fiscal bill |
| `fiscal_paper_electronic` | Electronic fiscal bill |
| `general_machine_invoice` | General machine-printed invoice |
| `highway_passenger_invoice` | Highway passenger invoice |
| `machine_printed_invoice` | General machine-printed electronic invoice |
| `medical_electronic_invoice` | Electronic medical invoice |
| `medical_invoice` | Medical invoice |
| `motor_vehicle_sale_invoice` | Motor vehicle sales invoice |
| `other` | Other invoice or bill |
| `quota_invoice` | Fixed-amount invoice |
| `shipping_invoice` | Ship ticket |
| `tax_clearance_certificate` | Tax clearance certificate |
| `taxi_ticket` | Taxi invoice |
| `ticket_refund_fee` | Train ticket refund fee |
| `train_ticket` | Train ticket |
| `travel_transport` | Ride-hailing itinerary |
| `vat_invoice_sales_list` | VAT sales list |
| `used_car_purchase_invoice` | Used car sales invoice |
| `vat_special_invoice` | VAT special invoice |
| `vat_electronic_special_invoice` | VAT electronic special invoice |
| `vat_electronic_invoice` | VAT electronic ordinary invoice |
| `vat_common_invoice` | VAT ordinary invoice |
| `blockchain_electronic_invoice` | Blockchain electronic invoice |
| `vat_electronic_invoice_new` | Fully digital ordinary invoice |
| `vat_electronic_special_invoice_new` | Fully digital VAT special invoice |
| `vat_electronic_toll_invoice` | VAT electronic toll invoice |
| `vat_roll_invoice` | VAT roll invoice |
| `vehicle_toll` | Road, bridge, and vehicle toll invoice |

For `vat_electronic_invoice_new` and `vat_electronic_special_invoice_new`, subtype-specific tables may be returned for passenger transport services or cargo transport services.

## ⚠️ Usage Limits

| Item | Requirement / Limit |
|------|---------------------|
| Authentication | No login, no API key |
| File Size | Less than 2 MB |
| Page Count | Up to 2 pages |
| Supported Formats | PDF, OFD, JPG, JPEG, PNG |
| URL Accessibility | Publicly accessible HTTP/HTTPS URL. Private network or internal IP addresses are not supported |
| Per IP per minute | 30 requests (within any consecutive 60 seconds) |
| Per IP per day | 50 requests |
| Daily pool | 5,000 requests |
| Batch processing | Not supported |
| Async tasks | Not supported |
| Human collaboration | Not supported |
| Evaluation workflow | Not supported |
| Self-optimization | Not supported |
| Tax authority verification | Not performed in the free public API |

When the limit is exceeded, the API returns HTTP `429` with registration guidance included in the response.

```json
{
  "code": "rate_limited_day",
  "message": "Daily free usage limit has been used up. Please come back tomorrow.",
  "upgrade_message": "Sign up for 100 monthly free credits, more fields, higher performance, multi-tax support & self-optimization",
  "signup_url": "https://adp-global.laiye.com/?utm_source=promotions"
}
```

## ❌ Error Codes

| HTTP Status Code | code | Description |
|-------------|------|------|
| 400 | `invalid_input` | No file was provided, or both `file_base64` and `file_url` were provided. |
| 400 | `invalid_base64` | `file_base64` cannot be decoded. |
| 400 | `invalid_url` | `file_url` is not a valid HTTP/HTTPS URL. |
| 400 | `ssrf_blocked` | `file_url` points to a private, internal, or blocked address. |
| 400 | `download_failed` | The file could not be downloaded. |
| 400 | `file_too_large` | File size is greater than or equal to 2 MB. |
| 400 | `unsupported_format` | File format is not PDF, OFD, JPG, JPEG, or PNG. |
| 400 | `invalid_file` | File content is invalid or page count cannot be determined. |
| 400 | `too_many_pages` | File has more than 2 pages. |
| 400 | `no_result` | No supported China domestic bill type was recognized. |
| 429 | `rate_limited_minute` | The single-IP per-minute quota was exceeded. |
| 429 | `rate_limited_day` | The single-IP daily quota was exceeded. |
| 429 | `rate_limited_global` | The global daily free pool was exhausted. |
| 500 | `extraction_failed` | Server processing failed. Retry later or use the full ADP product. |

## 🚀 Advanced Usage

This API uses the fixed `domestic-multi-bill` model with preset document-type configurations, designed exclusively for a quick experience.

**Upgrade to the full ADP account to unlock these premium capabilities:**
- Process files larger than 2MB and documents with more pages
- Higher API call frequency & unlimited request quotas
- Customizable extraction fields and document workflows
- Tax authority verification for supported invoice types
- Asynchronous batch processing
- Human-in-the-loop (HITL) review workflow
- Evaluation workflow and autonomous optimization
- Webhook callback support
- MCP tool integration for AI clients (Claude Desktop, Cursor, etc.)

New users will receive **100 free credits** upon registration to experience all full-function features. We provide independent Public Cloud access addresses for domestic and international users, which need to be configured separately by region. Accessing from a nearby location can better ensure high-speed and stable invocation across the network.
  - Users in Chinese Mainland [Log in](https://adp.laiye.com/?utm_source=promotions)
  - Users outside Chinese Mainland [Log in](https://adp-global.laiye.com/?utm_source=promotions)


## 🛠️ Support & Contact
- **CLI User Guide:** [ADP CLI User Guide](https://laiye-tech.feishu.cn/wiki/YIaawiK2DimisZk5KfDc8a8cnLh)
- **API Documentation:** [Open API User Guide](https://laiye-tech.feishu.cn/wiki/S1t2wYR04ivndKkMDxxcp2SFnKd)
- **ADP Product Manual:** [Public Cloud Manual](https://laiye-tech.feishu.cn/wiki/OfexwgVUQiOpEek4kO7c7NEJnAe)
- **Issue Tracker:** [GitHub Issues](https://github.com/Laiye-ADP/adp-skills/issues)
- **Email:** global_product@laiye.com
- **Website:** [Laiye ADP](https://laiye.com/en/product/adp-platform)


<div align="center">
[⬆ Back to Top](#agentic_doc_parse_and_extract)

**Build the Future of Agentic AI with ❤️**
Copyright © 2026 [Laiye Technology (Beijing) Co., Ltd.] All rights reserved.

</div>
