<div align="center">

# 🚀 来也 ADP 国内通用票据智能抽取 · 限时免费开放

由来也科技 ADP 智能文档处理团队重磅出品，面向**中国地区财务报销、记账、票据归档、差旅自动化、系统集成场景**，提供高精度、全类型的国内通用票据智能抽取能力。全面兼容增值税发票、火车票、机票行程单、出租车票、医疗票据、财政票据、海关单据、通行费票据等常见票据类型，不论是电子 PDF、OFD、扫描件，还是图片文件，均可以**一键输出标准化 JSON 结构化数据**，大幅降低财务人力成本，打通报销、记账、对账、归档等业务自动化流程。

</div>

## ⭐ 选择 ADP 的核心优势
✅ 国内通用票据方案 | 接入简单，票据分类精准可靠
📄 覆盖 30+ 常见国内票据：支持增值税发票、交通票据、医疗票据、财政票据、海关单据等。
🎯 自动分类与结构化抽取：无需手动指定票据类型，自动输出标准 JSON。
⚡ 免登录快速体验：无需注册账号、无需 API Key，直接调用公开接口。
🔒 安全访问控制：文件 URL 支持 SSRF 防护，并提供可控免费额度。
🤖 可升级完整能力：支持解锁批量、异步、人机协同、评测、自主优化等完整 ADP 能力。

> 来也 ADP 接口**限时免费开放**，名额有限，先到先得！

## 📌 适用场景
| 用户群体 | 使用场景 |
| ---- | ---- |
| 财务团队 | 从国内发票、差旅票据、报销票据中提取关键数据，用于费用报销、财务记账与供应商结算。 |
| 智能体用户 | 一键安装 ADP Skill 至国内Coze、Workbuddy、Openclaw、Dify、Manus等主流智能体平台，实现文档自动识别。 |
| 开发者 | 通过免登录公开 API 快速验证国内票据抽取效果，再迁移至 ADP 完整服务。 |

---

## 📄 快速开始

### 步骤 1：选择接口地址
我们为国内外用户提供独立的公有云接入地址，需按区域分别配置。就近接入可保障调用高速稳定，无需注册账号、无需 API 密钥，直接向下方接口地址发起请求即可。

| 环境 | API 接口地址 |
|------|---------|
| **国内版** | `https://adp.laiye.com/public/v1/domestic-multi-bill/extract` |
| **国际版** | `https://adp-global.laiye.com/public/v1/domestic-multi-bill/extract` |

### 步骤 2：发送请求

发送 `POST` 请求，`file_url` 和 `file_base64` 二选一，不能同时传入。

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `file_url` | string | 文件公网 HTTP/HTTPS 地址；不支持内网、私有 IP 或被 SSRF 策略拦截的地址 |
| `file_base64` | string | 文件 Base64 内容；支持带 `data:` 前缀的 Data URL |

#### 方式 1：文件 URL 地址

```bash
curl -X POST "https://adp.laiye.com/public/v1/domestic-multi-bill/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://example.com/china-invoice.pdf"
  }'
```

#### 方式二：Base64 编码文件内容

```bash
curl -X POST "https://adp.laiye.com/public/v1/domestic-multi-bill/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "file_base64": "<base64-encoded-file-content>"
  }'
```

#### Python 请求示例

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

### 3. 获取结果（示例）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `success` | boolean | 请求是否成功 |
| `extraction_result` | array | 按票据类型分组后的抽取结果 |
| `aigc` | object | AIGC 处理标识信息 |
| `upgrade_message` | string | 注册升级提示 |
| `signup_url` | string | 注册页面 |

返回结果按票据类型分组。每个分组的 `field_key` 就是票据类型 `type_key`，`object_values` 中是一张或多张同类型票据实例。

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

解析建议：

- 使用分组的 `field_key` 判断票据类型。
- 使用 `object_values[].document_type` 和 `object_values[].pages` 判断单张票据实例及页码。
- 普通字段读取 `field_values`。
- 表格字段读取 `table_values`。
- 免登录版不限制字段数量，不同票据类型返回字段集合不同。
- 低置信或未知类型可能返回为 `other`。

## 支持票据类型

| `type_key` | 票据名称 |
| --- | --- |
| `air_transport` | 航空运输电子客票行程单 |
| `custom_declaration_form` | 海关报关单 |
| `customs_payment_form` | 海关缴费书 |
| `electronic_air_transport` | 电子发票航空运输电子客票行程单 |
| `electronic_motor_vehicle_sale_invoice` | 电子发票机动车销售统一发票 |
| `electronic_train_ticket` | 电子发票铁路电子客票 |
| `electronic_used_car_purchase_invoice` | 电子发票二手车销售统一发票 |
| `fiscal_paper` | 财政票据 |
| `fiscal_paper_electronic` | 电子财政票据 |
| `general_machine_invoice` | 通用机打发票 |
| `highway_passenger_invoice` | 公路客运发票 |
| `machine_printed_invoice` | 通用机打电子发票 |
| `medical_electronic_invoice` | 电子医疗票据 |
| `medical_invoice` | 医疗票据 |
| `motor_vehicle_sale_invoice` | 机动车销售统一发票 |
| `other` | 其他发票 |
| `quota_invoice` | 通用定额发票 |
| `shipping_invoice` | 船票 |
| `tax_clearance_certificate` | 完税证明 |
| `taxi_ticket` | 出租车发票 |
| `ticket_refund_fee` | 火车票退票费 |
| `train_ticket` | 火车票 |
| `travel_transport` | 网约车行程单 |
| `vat_invoice_sales_list` | 增值税销货清单 |
| `used_car_purchase_invoice` | 二手车销售统一发票 |
| `vat_special_invoice` | 增值税专用发票 |
| `vat_electronic_special_invoice` | 增值税电子专用发票 |
| `vat_electronic_invoice` | 增值税电子普通发票 |
| `vat_common_invoice` | 增值税普通发票 |
| `blockchain_electronic_invoice` | 区块链电子发票 |
| `vat_electronic_invoice_new` | 电子发票普通发票 |
| `vat_electronic_special_invoice_new` | 电子发票增值税专用发票 |
| `vat_electronic_toll_invoice` | 增值税电子普通发票（通行费） |
| `vat_roll_invoice` | 增值税普通发票（卷票） |
| `vehicle_toll` | 过路过桥费发票、汽车通行费 |

对于 `vat_electronic_invoice_new` 和 `vat_electronic_special_invoice_new`，如果票面内容属于旅客运输服务或货物运输服务，结果中可能包含对应的运输明细表格。

## ⚠️ 使用限制

| 限制项 | 规则说明 |
|------|---------------------|
| 登录认证 | 不需要登录，不需要 API Key |
| 文件大小 | 小于 2 MB |
| 文件页数 | 不超过 2 页 |
| 支持格式 | PDF、OFD、JPG、JPEG、PNG |
| URL 权限 | 仅支持公网 HTTP/HTTPS 链接，不允许内网、私有 IP |
| 单IP每分钟 | 30 次（60秒内） |
| 单IP每日 | 50 次（一天） |
| 全局每日限额 | 5000 次 |
| 批量处理 | 不支持 |
| 异步任务 | 不支持 |
| 人机协同 | 不支持 |
| 评测流程 | 不支持 |
| 自主优化 | 不支持 |
| 税局验真 | 免登录版不执行 |

超出限制将返回 HTTP `429`，响应中附带注册引导信息。

```json
{
  "code": "rate_limited_day",
  "message": "当日免费额度已用尽，请次日再来。",
  "upgrade_message": "注册账号每月可享100次免费额度，解锁更多字段、更强性能、全税种识别与模型自主优化能力",
  "signup_url": "https://adp-global.laiye.com/?utm_source=promotions"
}
```

## ❌ 错误码对照表

| HTTP 状态码 | 错误码 | 说明 |
|-------------|--------|------|
| 400 | `invalid_input` | 未传文件，或同时传入 `file_base64` 与 `file_url` |
| 400 | `invalid_base64` | Base64 解码失败 |
| 400 | `invalid_url` | `file_url` 不是合法 HTTP/HTTPS 地址 |
| 400 | `ssrf_blocked` | URL 指向内网、私有 IP 或被安全策略拦截 |
| 400 | `download_failed` | 文件下载失败 |
| 400 | `file_too_large` | 文件大小大于等于 2 MB |
| 400 | `unsupported_format` | 文件格式不是 PDF、OFD、JPG、JPEG、PNG |
| 400 | `invalid_file` | 文件内容无效，或无法读取页数 |
| 400 | `too_many_pages` | 页数超过 2 页 |
| 400 | `no_result` | 未识别到支持的国内通用票据类型 |
| 429 | `rate_limited_minute` | 单 IP 每分钟额度超限 |
| 429 | `rate_limited_day` | 单 IP 每日额度超限 |
| 429 | `rate_limited_global` | 全局每日免费额度耗尽 |
| 500 | `extraction_failed` | 服务端处理失败，请稍后重试 |

## 🚀 进阶能力说明

本接口采用 `domestic-multi-bill` 国内通用票据模型及预置票据类型配置，仅用于快速体验。

**升级至完整版 ADP 账号，即可解锁以下高级能力：**
- 支持处理 2MB 以上文件及更多页数文档
- 更高 API 调用频次，请求额度不限
- 可自定义提取字段与文档处理工作流
- 支持票据验真能力
- 异步批量处理
- 人工介入审核流程（HITL）
- 评测流程与模型自主优化能力
- 支持 Webhook 回调
- 对接 Claude Desktop、Cursor 等 AI 客户端，支持 MCP 工具集成

新用户注册即送 **100 免费点数**，试用全部完整版功能。国内外用户分设独立公有云接入地址，按地区分开配置，就近接入可实现跨网高速稳定调用。
  - 中国地区 [登录](https://adp.laiye.com/?utm_source=promotions)
  - 全球地区 [登录](https://adp-global.laiye.com/?utm_source=promotions)


## 📞 支持与联系
- **CLI 使用指南：** [ADP CLI 使用指南](https://laiye-tech.feishu.cn/wiki/Hz3Vw1IQki3YQtk33gLcSdwSndc)
- **API 接口文档：** [Open API 使用指南](https://laiye-tech.feishu.cn/wiki/PO9Jw4cH3iV2ThkMPW2c539pnkc)
- **ADP 产品操作手册：** [公有云操作手册](https://laiye-tech.feishu.cn/wiki/UDYIwG42pisBbFkJI39ctpeKnWh)
- **问题反馈：** [GitHub Issues](https://github.com/laiye-ai-repos/adp-skill/issues)
- **邮箱：** global_product@laiye.com
- **官网：** [来也科技](https://laiye.com)


<div align="center">
[⬆ 返回顶部](#agentic_doc_parse_and_extract)

**用 ❤️ 构建智能体 AI 的未来**
版权所有 © 2026 [来也科技（北京）有限公司] 保留所有权利。

</div>
