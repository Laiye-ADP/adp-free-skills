---
name: agentic-doc-parse-and-extract
description: Help users parse documents, extract structured fields, and process batches through Laiye ADP APIs. Guide region selection, API key setup, credit and application discovery; prefer existing apps and guide field definition, prompt generation, and custom extraction app creation when no suitable app exists.
---

# Laiye ADP Agentic Document Processing Skill

## Overview

ADP (Agentic Document Processing) is Laiye's intelligent document processing product. It converts PDFs, images, scans, and business documents into text, tables, and structured fields for expense reimbursement, order entry, contract information management, identity document recognition, and related workflows.

This Skill understands the user's goal through conversation, recommends suitable ADP capabilities, and processes documents through APIs. Users do not need to install a CLI or write integration code; they provide an API key, files, and their requirements.

This file defines the business workflow and agent interaction rules. Engineers will add endpoints, request parameters, and implementation details. Actual execution must use connected capabilities and their real responses.

## Applicable Scenarios

| Scenario | Example request | Recommended approach |
| --- | --- | --- |
| Invoice and receipt recognition | “Read this invoice” or “Summarize these expense receipts” | Match an existing receipt app and extract fields; verification depends on actual application support |
| Common documents such as orders and identity documents | “Extract order line items” or “Read this ID” | Match an existing app and process directly |
| Full text and layout parsing | “Read this scan” or “Extract PDF text and tables” | Recommend document parsing and return text, tables, or layout |
| Nonstandard documents or custom fields | “Extract contract payment terms” or “I only need these fields from this form” | Check existing coverage first; create a custom extraction app if needed |
| Batch documents | “Process these files together” or “Organize this folder” | Match apps by document type and process within the account concurrency limit |
| Capability advice and account queries | “What can ADP process?”, “How many credits remain?”, or “Which apps do I have?” | Explain capabilities first; obtain credentials when account access is needed |

## Intent Recognition and Communication

- Determine whether the user wants advice, account information, or actual document processing.
- Distinguish full-text/layout parsing from field extraction. Recommend extraction directly when only fields are needed.
- Select capabilities based on content, business goals, and requested fields, not only filenames or extensions.
- Respond in the user's language. Reuse supplied region, credentials, files, and field requirements instead of repeatedly asking.
- For advice-only requests, explain first without requiring a key or file. Guide the necessary setup when actual processing is requested.
- Keep guidance brief and understandable without requiring the user to understand endpoint names or parameter schemas.

## Step 1: Select a Region and Obtain an API Key

### Recommend a Region

Recommend China for Chinese conversations and Global for English or other languages. An explicitly stated or previously verified account region takes priority.

Language is only a recommendation signal, not proof of account location. Clearly show both registration/sign-in links:

| Version | Registration / sign-in |
| --- | --- |
| China | [Register or sign in to ADP China](https://adp.laiye.com/?utm_source=github) |
| Global | [Register or sign in to ADP Global](https://adp-global.laiye.com/?utm_source=github) |

### Obtain Credentials

1. Check for an available API key already authorized by the user and reuse it.
2. If absent, guide registration or sign-in in the appropriate region, followed by the `API_Key` page under the profile menu. Ask the user to supply the key through a secure mechanism supported by the environment.
3. Explain that the next step is checking credits and available apps before recommending a processing approach.
4. Never echo or publicly store the key. On authentication failure, suggest checking the key and account region; do not treat a network problem as proof of an invalid key.

English guidance example:

> I can help process your documents. I recommend [ADP Global](https://adp-global.laiye.com/?utm_source=github) for this conversation. If your account is registered in China, use [ADP China](https://adp.laiye.com/?utm_source=github). Get your API key from the API_Key page under your profile and provide it securely. I will then check your credits and available applications.

Chinese guidance example:

> 我可以帮你处理文档。根据当前沟通语言，推荐使用 [ADP 国内版](https://adp.laiye.com/?utm_source=github)；如果你的账户注册在海外版，请使用 [ADP 海外版](https://adp-global.laiye.com/?utm_source=github)。登录后在个人头像菜单的 API_Key 页面获取密钥，并通过安全方式提供。接下来我会查询你的积分和可用应用。

## Step 2: Query Credits and Applications

After obtaining valid credentials, query:

- **Credits:** Available credits and whether processing can continue. Do not promise a file count when the actual cost is unknown.
- **Account type:** Free or paid, to determine batch concurrency.
- **Applications:** Available preset and custom apps, including names, labels, and capability information needed for matching.

Briefly report the region, available credits, relevant capabilities, and concurrency limit. Prioritize applications related to the user's goal; show the full list when requested.

Handling rules:

- Suitable app available: Recommend it and request files, or proceed if files were already provided.
- No suitable app: Explain that a custom app can be created from the desired fields and follow the custom workflow in Step 3.
- Insufficient credits: Provide the current account region's recharge entry and pause new billable processing.
- Failed or incomplete query: State what is unknown and retain other valid results. Never invent balances, plans, or apps.
- Unknown account type: Temporarily use 2 concurrent documents and disclose that the type is unconfirmed.
- A free account does not imply all API calls are free; use actual account and product rules for pricing and allowances.

## Step 3: Request Files and Select a Processing Path

If files are missing, request an upload, accessible file link, or local path. Otherwise use existing inputs.

Identify the desired output: full text and tables, complete structured results, or selected fields. Ask only questions that affect processing.

### Path A: An Existing App Can Handle the Request

1. Check whether actual app capabilities cover the document type and requested fields; a similar name is insufficient.
2. Prefer an explicitly selected suitable app or a previously verified suitable app from the current conversation. Otherwise select the best field coverage; where capabilities are equivalent, prefer an explicitly marked high-speed version.
3. Briefly identify the chosen capability, then call the connected processing function directly without per-file confirmation.
4. Wait for completion and return results. For large or long-running documents, provide progress and retain task records for later queries.
5. Distinguish recognition from invoice verification. Report verification only when the app supports it and returns a conclusion; successful recognition does not imply successful verification.

### Path B: No App Covers the Extraction Requirements

First confirm that existing apps cannot satisfy the goal; the absence of an identical app name is not enough. Then follow this sequence:

**1. Clarify the desired fields**

Explain that a reusable custom extraction app can be created and ask which information the user needs. Suggest fields based on the document to make the request easier to describe.

For example:

> The available apps do not fully cover your contract extraction needs. Which information would you like? Possible fields include contract number, parties, signing date, contract amount, and payment terms. If you need line items, you can also specify item name, quantity, and unit price.

Reuse fields already specified. Clarify only ambiguous meanings, date or amount formats, and whether line items are needed. If the user is unsure, offer suggestions for selection rather than treating them as confirmed requirements.

**2. Generate extraction prompts**

Call prompt generation using the user's field requirements and a representative sample. Ensure the prompt covers the goal without silently adding or removing explicitly requested fields.

**3. Create a custom application**

Pass the fields and prompts to the app-creation capability, including necessary configuration conversion, to create a reusable app. Retain its name and identifier for current and future processing.

When the user has requested extraction and the requirements are clear, continue without repeated confirmation. For advice-only requests, explain the proposed workflow without creating an app.

**4. Perform extraction**

Use the new app to process the supplied documents. Reuse one app for the same document type and field requirements rather than creating one per file.

**5. Return results**

Present extracted fields and values, explain missing values and items needing attention, and describe which future documents can reuse the app.

If any step fails, report the stage and next action. If app creation succeeds but extraction fails, retain the app information to avoid duplicate creation.

## Step 4: Process Multiple Files in a Batch

When the user supplies multiple files, organize batch processing automatically without requiring separate requests for each file.

| Account type | Maximum concurrent documents |
| --- | --- |
| Free | 2 |
| Paid | 10 |

Batch rules:

1. Establish the file count and required capabilities. Reuse apps for similar documents, match mixed types independently, and create a custom app once for any group that requires one.
2. Submit within the account limit and queue the remainder. All document groups share the same account limit; do not multiply concurrency by the number of groups.
3. Concurrency counts documents still being processed. An asynchronous task continues to occupy a slot after its identifier is returned and releases it only when processing ends. An unavailable result does not mean the task has ended.
4. Preserve mappings between each source, selected app, status, and result to prevent mismatched results or overwrites from duplicate basenames.
5. Retain successful results when individual files fail. Adjust or pause new submissions on insufficient credits, invalid authentication, or explicit service limits.
6. If a request times out and acceptance is unknown, mark it as “submission pending confirmation.” Do not blindly resubmit and risk duplicate processing or charges.

## Step 5: Return Results and Guide Reuse

- **Single file:** Return the result with a short explanation, using JSON, a table, or readable text as requested.
- **Batch:** Report total, succeeded, failed, processing, pending-confirmation, and not-submitted counts, followed by per-file results or result files.
- **Integrity:** Preserve original extracted information and distinguish API values from agent summaries, calculations, or formatting.
- **Exceptions:** Clearly identify missing fields, low confidence, verification exceptions, and failures. Do not turn absent information into asserted facts.
- **Reuse:** If a custom app was created, explain that similar future documents can use it directly; reassess configuration when field goals change.
- **Truthful status:** Report queries, app creation, or processing as complete only when actual responses support it. If technical capabilities are not connected yet, explain that guidance is available without claiming execution.

## Technical Handoff Checklist

The following capabilities are needed to implement this framework. Engineers will supply endpoints and parameters.

| Capability | Business input | Business output |
| --- | --- | --- |
| Authentication and region resolution | Selected region and API key | Authentication status and account region |
| Credits and plan query | Authenticated account | Available credits, account type, effective concurrency limit |
| Application discovery and matching | User intent, available apps, app configuration where needed | Available apps and a recommendation or custom-app requirement |
| File intake | Uploads, file links, or local paths | Processable files and source records |
| Prompt generation | Field requirements and sample documents | Extraction prompts and configurable field descriptions |
| Custom app creation | App name, fields, and prompts | Reusable app identifier and configuration |
| Document parsing and extraction | Files, selected app, processing goal | Raw results or queryable task records |
| Batch scheduling and status queries | Files, app assignments, concurrency limit | Per-file status and results |
| Result presentation | Raw results and requested output format | Single-file output, batch summary, and exports when needed |

