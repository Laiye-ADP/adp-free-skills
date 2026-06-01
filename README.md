<div align="center">

# 📄 Laiye Agentic Document Processing (ADP) Skill Collection

ADP is an Agentic Document Processing (ADP) product independently developed by Laiye. It deeply integrates Vision-Language Model (VLM), Large Language Model (LLM) and agent autonomous decision-making technologies, thoroughly revolutionizing traditional document processing modes. It upgrades the long-standing rule-based mechanical field extraction to goal-driven full-process intelligent automation. Free from the core pain points of traditional OCR and IDP solutions that heavily rely on manual labeling, template adaptation and rule maintenance, ADP features powerful generalization and self-adaptation capabilities. It efficiently handles complex documents with varied layouts, multiple languages and diverse scenarios in enterprise businesses, helping enterprises cut costs, improve efficiency and enhance quality in document processing.

[English](README.md) | [Simplified Chinese](README-CN.md)

</div>

---

> 📢 News  
Laiye ADP Global Invoice Extraction · Free for Limited Time，Spots are limited, available on a first-come, first-served basis. [Learn more about: ADP Global Invoice Extraction Free Skill](adp-global-invoice-extraction-free/SKILL.md)

---
## ✨ Core Advantages
Compared with traditional document processing solutions, ADP leverages agent technology and multimodal models to deliver higher accuracy and broader document compatibility without data labeling or model training.

1. **Integrated Multimodal Capabilities for Fast Deployment with Zero Labeling & Training**
Combining VLM visual understanding and LLM semantic comprehension, this is the core enabler of zero labeling and training. It eliminates the need for massive sample labeling, repeated model training and manual rule configuration required by traditional tools. You can define extraction requirements in natural language, with no need to set fields one by one or adapt to fixed templates. Only one sample is needed to support new document types, greatly shortening launch cycles and cutting labor costs from repeated iterations. It accurately interprets document logic, hierarchy and business content, and handles complex scenarios including borderless tables, mixed layouts, handwritten text, stamps, watermarks, blurry photos, layered PDFs and scanned files to fully restore original document information.

2. **Unified Model for All Languages, Global Coverage**
There is no need to deploy and maintain separate OCR models for different minor languages. A single ADP model supports over a hundred languages, including Simplified & Traditional Chinese, English, French, languages of Southeast Asia, European countries and mixed-language documents. No extra language packs or dedicated language adaptation are required, fully meeting global document processing demands for domestic and overseas businesses.

3. **Self-learning & Continuous Improvement for Better Accuracy Over Time**
Built on a brand-new agent architecture, ADP supports fully automated optimization. The system automatically records all recognition errors, learns and adjusts itself continuously, then presents optimized results. Users only need to decide whether to apply the updates. No manual labeling or retraining is required, solving the issue of static traditional models that fail to adapt to document format changes.

4. **Low Learning Curve, Plug-and-Play with Skills**
Easy to get started with no complicated operations. Equipped with built-in Skills for plug-and-play use. Featuring conversational workflow, simply tell the ADP agent your requirements, and it will automatically arrange and generate complete workflows without manual intervention.


## ⚖️ ADP vs Traditional OCR/IDP: Core Differences
A full comparison in working mechanism, deployment cost, compatibility and iteration mode shows that ADP is a comprehensive upgrade over traditional document processing solutions:

| Comparison Dimension | Traditional OCR/IDP Solutions | ADP Agentic Document Processing Solution |
|:---|:---|:---|
| **Core Working Logic** | Mechanical character recognition + fixed rule-based field extraction; only identifies text coordinates without understanding business semantics | In-depth semantic understanding + goal-driven agent execution; comprehends document structure and business logic to complete processing tasks autonomously |
| **Deployment Barrier** | High threshold; requires extensive sample labeling, manual field configuration, rule writing and model training & iteration | Low threshold; no labeling or training needed. Configure requirements via natural language for immediate launch |


## 🏗️ Brand-new ADP Product Architecture: Resolve Complex Document Issues from Point to Whole

ADP adopts a three-tier progressive architecture to manage the full lifecycle of document processing on one single platform, ranging from basic single-field extraction to enterprise-wide end-to-end automation and long-term capability accumulation.

| Tier | Positioning | Business Example |
|:---|:---|:---|
| 🎯 **Point: Basic Parsing & Extraction** | "Understand documents and extract fields accurately", supporting structured processing of single documents such as invoices, orders and contracts | Extract amount, date and supplier information from overseas invoices in one go |
| 📈 **Line: End-to-end Document Workflow** | Connect multiple steps including verification, calculation and format conversion into automated workflows | Full workflow: Invoice extraction → Contract matching → Amount verification → ERP data synchronization |
| 🔁 **Surface: Human-machine Collaborative Iteration** | Manual review and correction drive continuous learning and optimization to form a data flywheel | After several corrections on amount formats, the system automatically adapts to decimal notation on Italian invoices and becomes increasingly accurate |

> Core Value: Realize ad-hoc single-field extraction, enterprise-wide end-to-end automation and long-term exclusive capability accumulation all on one platform.


# 🛠️ Introduction to ADP Skills
This skill calls capabilities via the official ADP CLI tool. Agents can complete calls with simple commands instead of connecting to APIs or writing complex interactive codes. Compared with API-based skills, CLI avoids cumbersome work including interface debugging, data assembly and logic coding, simplifies integration and enables various agents to quickly invoke document processing capabilities.

## 🛠️ ADP Skill Classification
This repository aggregates all document processing capabilities of ADP. All skills are divided into three categories by positioning: General, Scenario-based and Specialized Function, for flexible selection based on business demands.

| Type Name | Capability Description | Target Users & Scenarios | Skill Example |
|:---|:---|:---|:---|
| 🧩 **General** | Integrates full ADP capabilities, including document parsing, document extraction (custom extraction & out-of-the-box extraction), workflow and human-machine collaboration | Users requiring comprehensive document processing capabilities | [Agentic Document Parsing & Extraction](agentic-doc-parse-and-extract/SKILL.md) |
| 🎯 **Specialized Function** | Encapsulates individual atomic capabilities of ADP. Lightweight with single function and no extra combination required | Users with single-type document processing demands and pursuing simplified invocation | [Chinese Resident ID Card Recognition & Extraction](id-card-recognition-and-extract/SKILL.md) |
| 📂 **Scenario-based** | Focuses on vertical business scenarios. Combines ADP capabilities with upstream and downstream functions to deliver end-to-end solutions beyond pure document processing | Users demanding complete business workflows and one-stop scenario-based solutions | [Invoice Collection & Summary from Mailbox](invoice-extractor-from-mail/SKILL.md) |

## 📋 ADP Skills 速览表

### Limited Free Skills
| Skill Name | Skill Description | Link |
| ---- | ---- | ---- |
| Global Invoice Free Edition | Limited-time offer: For **global cross-border finance, automation, and system integration scenarios**, provides high-precision, full-format, multi-language intelligent extraction for invoices, bills, and receipts. Fully compatible with structured standard documents, unstructured overseas purchase invoices, and consumer receipts. Whether it’s electronic PDFs, scanned copies, or image files, it can **output standardized JSON structured data with one click**, significantly reducing financial labor costs and seamlessly connecting end-to-end processes for business automation, smart reconciliation, and data entry. | [ADP Global Invoice Extraction Free Skill](adp-global-invoice-extraction-free/SKILL.md) |

### General SKills
| Skill name | Skill description | Link |
| ---- | ---- | ---- |
| Agentic Document Parsing & Extraction | Enables AI-powered parsing and key information extraction from high-frequency documents including invoices, orders, receipts, long texts, and common Chinese identity & credential documents. Supports reusable custom templates for non-standard business files. Features batch concurrent processing and human-in-the-loop review with customizable audit rules to automate document workflows for finance, administration, HR data entry and other departments. | [Agentic Document Parsing & Extraction](agentic-doc-parse-and-extract/SKILL.md) |

### Specialized Function SKills
| Skill name | Skill description | Link |
| ---- | ---- | ---- |
| global-invoice-recognition-and-extraction | Multi-language, multi-currency global invoice recognition and extraction — accurately extracts invoice number, date, supplier, buyer, currency, tax amount, total amount, and line items, outputting structured JSON. Zero-configuration, out-of-the-box, suitable for accounts payable automation, expense reimbursement, and cross-border trade document processing. | [global-invoice-recognition-and-extraction](global-invoice-recognition-and-extraction\SKILL.md) |
| Universal Document Parsing | Supports parsing of more than ten file formats including PDFs, images, scanned documents and Office files. It can output standard structured JSON or well-formatted Markdown as needed: key fields are extracted into JSON data, while original layouts such as headings, tables, lists and paragraphs are fully preserved when converted to Markdown. Zero configuration required and ready for immediate use. It caters to various business scenarios including document storage and retrieval, automated data pipelines, cross-system integration, content migration, document organization and LLM context preparation. | [JSON Output](pdf-to-structured-json\SKILL.md) 、[Markdown Output](pdf-to-structured-markdown\SKILL.md)|
| purchase-order-recognition-and-extraction | Accurately extracts all fields from purchase orders and sales orders in various formats, including document number, order date, seller, buyer/customer, customer address, consignee, delivery address, currency, total amount, as well as line item details such as material code, material description, quantity, tax rate, tax-inclusive unit price, tax-inclusive amount and delivery date. Outputs results in standard JSON format. Ready to use with no extra configuration, ideal for scenarios such as e-commerce order entry, supply chain reconciliation and warehouse management automation. | [purchase-order-recognition-and-extraction](purchase-order-recognition-and-extraction\SKILL.md)  |



### Scenario-based SKills
| Skill name | Skill description | Link |
| ---- | ---- | ---- |
| invoice-extractor-from-mail | Designed for AP finance teams in cross-border trade enterprises. Automatically fetches invoice attachments from email (IMAP/OAuth) or local files, batch-extracts key fields (invoice number, amount, currency, etc.) via ADP, and exports results to Excel or business systems — no manual data entry required. | [invoice-extractor-from-mail](invoice-extractor-from-mail\SKILL.md) |

# ADP Skills General Operation Steps

## Step 1: Install ADP CLI

```bash
# Method 1: npm (Recommended, cross-platform)
npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli
```

```bash
# Method 2: Shell Script (Linux / macOS, for environments without npm)
curl -fsSL https://raw.githubusercontent.com/laiye-ai/adp-cli/main/scripts/adp-init.sh | bash
```

```bash
# Method 3: PowerShell Script (Windows, for environments without npm)
irm https://raw.githubusercontent.com/laiye-ai/adp-cli/main/scripts/adp-init.ps1 | iex
```

You may also download precompiled binary packages from [GitHub Releases](https://github.com/laiye-ai/adp-cli/releases).


## Step 2: Obtain ADP API Key and Complete Authentication Configuration

### 1. Access ADP Portal to Get Credentials
We provide independent public cloud access endpoints for users in Chinese mainland and overseas regions. Please configure accordingly based on your location. Nearby access ensures stable and high-speed network calls. Meanwhile, as the developer of ADP, Laiye has obtained **ISO/IEC 27001:2022 Information Security Management System Certification** and completed **SOC 2 Independent Audit**, delivering full-process security and compliance protection for your document data.

| Region | Login Address | API Base URL |
|-----|----------|--------------|
| Chinese Mainland | [https://adp.laiye.com/](https://adp.laiye.com/?utm_source=github) | `https://adp.laiye.com/` |
| Global Regions | [https://adp-global.laiye.com/](https://adp-global.laiye.com/?utm_source=github) | `https://adp-global.laiye.com/` |

### 2. Register / Log in to Obtain API Key
New users need to register for an ADP account first. Each new account is entitled to 100 free credits per month.
- After logging in, click your avatar to enter the `API_Key` page directly.

### 3. Complete Authentication Configuration

```bash
adp config set --api-key <your-api-key>
adp config set --api-base-url https://adp.laiye.com
```

### 4. Verify Configuration

```bash
adp config get
```

**Notes**:
1. After configuring the API Key and API Base URL, it is recommended to store the information in environment variables to avoid repeated configuration.
2. If you have not completed the above configuration, please follow the steps above.

## Step 3: Obtain ADP APP ID

ADP applications fall into two categories. The out-of-the-box applications are fully trained and optimized by the ADP team. You can call APIs directly without additional data labeling or model training. If out-of-the-box applications cannot meet your requirements for specific document types, you may create custom applications independently. The two types are distinguished by the `app_type` field.

| `app_type` | Type & Description |
| ---------- | --------- |
| `0` | Out-of-the-box (OOTB) Application: Built-in platform application with `app_id` starting with `ootb_`. Ready for direct use without extra creation |
| `1` | Custom Application: Document extraction application created by users with self-defined `app_id` |


## 📜 License
This product is free to use, copy and distribute for non-commercial purposes. Commercial use requires prior written authorization. All intellectual property rights of the product belong to us. Retain all original statements and clearly mark modifications during distribution. Users shall be solely liable for all risks arising from use. Any violation will result in immediate termination of the license. This license is governed by the laws of the People's Republic of China. For full license terms, please refer to [License](license.md).


## 📞 Support & Contact
- **CLI User Guide:** [ADP CLI User Guide](https://laiye-tech.feishu.cn/wiki/YIaawiK2DimisZk5KfDc8a8cnLh)
- **API Documentation:** [Open API User Guide](https://laiye-tech.feishu.cn/wiki/S1t2wYR04ivndKkMDxxcp2SFnKd)
- **ADP Product Manual:** [Public Cloud Manual](https://laiye-tech.feishu.cn/wiki/OfexwgVUQiOpEek4kO7c7NEJnAe)
- **Issue Tracker:** [GitHub Issues](https://github.com/laiye-ai/adp-cli/issues)
- **Email:** global_product@laiye.com
- **Website:** [Laiye ADP](https://laiye.com/en/product/adp-platform)
---

<div align="center">

**Built with ❤️ for the Agentic AI Future**  
Copyright © 2026 [Laiye Technology (Beijing) Co., Ltd.] All rights reserved.

[⬆ Back to Top](#-laiye-agentic-document-processing-adp)

</div>
