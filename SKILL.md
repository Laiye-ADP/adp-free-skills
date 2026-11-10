---
name: agentic-doc-parse-and-extract
description: Help users parse documents, extract structured fields, and process files in batches through Laiye ADP APIs. Guide region selection, API key authorization, and credit and application queries based on user intent; prioritize existing apps, or guide field definition, prompt generation, and custom extraction app creation when no suitable app exists.
---

# Laiye ADP Agentic Document Processing Skill

ADP (Agentic Document Processing) is Laiye's intelligent document processing product. It converts PDFs, images, scans, and other business documents into text, tables, and structured fields for expense reimbursement, order entry, contract information management, identity document recognition, and related scenarios.

This file defines the business workflow and agent interaction rules. Engineers will supply endpoints, request parameters, and implementation details. Actual execution must rely on connected capabilities and their real responses.

## Workflow Overview

```text
Does the user have a specific document processing task?
├── No → Introduce ADP use cases
└── Yes
    ├── Authenticate and discover capabilities
    │   ├── Obtain the user's API key and authenticate
    │   ├── Check whether credits are sufficient
    │   └── Query templates and applications to identify capabilities the user can use directly
    ├── Receive files and match a solution to the user's intent
    │   ├── Document parsing
    │   │   ├── Suitable app exists → Parse directly
    │   │   └── No suitable app, but a suitable template exists → Copy template → Parse
    │   ├── Document extraction
    │   │   ├── Suitable app exists → Extract directly
    │   │   ├── No suitable app, but a suitable template exists → Copy template → Extract
    │   │   └── Neither exists → Define fields → Generate prompts → Create app → Extract
    │   └── Workflow
    │       ├── Suitable workflow app exists → Run directly
    │       └── No suitable workflow app, but a suitable template exists → Copy template → Run
    └── Return results
        ├── Single result → Return directly in the requested format
        ├── Multiple results → Save to the specified folder
        └── Multiple results requiring consolidation → Summarize in Excel
```

## User Scenarios and Intent Recognition

Identify the capability needed from the user's desired outcome before selecting an app. Each example below maps to a recommended action. When files and a clear goal are already available, proceed directly and ask only for information that affects app selection or processing results.

| Capability | Example user request | Recommended action |
| --- | --- | --- |
| Document parsing | I cannot copy text from this scanned contract. Extract all its content. | Parse the full text while preserving headings, paragraphs, and table structure. The goal is to recover content; there is no need to ask for extraction fields or create an extraction app. |
| Document parsing | Convert these PDFs to Markdown in a batch so I can add them to a knowledge base. | Parse the documents in a batch and output Markdown per file, preserving source-to-result mappings. Follow the specified format without asking for fields. |
| Document extraction | Extract and consolidate the numbers, dates, and amounts from these invoices. | Determine from file content whether each is a Chinese domestic receipt or an overseas invoice and match the appropriate app. Process mixed types separately within the account concurrency limit, consolidate requested fields, and retain source references. |
| Document extraction | Extract this order's line items, including names, quantities, and unit prices. | Match an order extraction app and extract directly, returning one row per item. Do not parse the full text first or immediately create an app just because the user specified fields. |
| Document extraction | Extract the parties, contract amount, and payment terms from this contract. | Check whether existing apps cover these fields. If none matches, reuse the stated requirements, generate prompts, create an app, and extract. Clarify only ambiguous fields. |
| Workflow | Review this travel expense claim for missing attachments, differences between receipt and claim amounts, and expenses over the limit. | Match an expense reimbursement review workflow and process documents for the same claim as a group. Ask for missing policies or limits. Report missing attachments, amount differences, and items over the limit with supporting evidence; do not invent reimbursement standards. |
| Workflow | Here are the contract, invoice, and acceptance report. Check whether this corporate payment meets the payment conditions. | Match an accounts payable review workflow. Associate documents for the same payment, check parties, amounts, and contractual payment conditions, and report compliance, differences, and missing evidence. Do not mix document groups from separate transactions. |
| Workflow | Check these files for risks. | Infer the business purpose from the files and context. If unclear, ask whether the review concerns reimbursement, corporate payment, or another purpose. Match a workflow and establish the review scope and criteria before execution rather than issuing a generic risk conclusion. |
| Workflow | Organize these companies' financial statements and summarize the metrics by company and year. | First check for a suitable financial statement workflow. If available, organize files by company, year, and statement type before running it. If the request only needs specified fields and no workflow fits, use document extraction. Clarify ambiguous metrics or aggregation criteria first. |
| Document classification | Classify these files as contracts, invoices, or orders and tell me each file's category. | Guide the user to define categories, descriptions, and distinguishing criteria, reusing existing clear configurations. Then request files, classify them, and return each file's category while preserving source mappings. |
| Document classification | I want to classify contracts as purchase, sales, or employment contracts. How should I set that up? | Guide category names, descriptions, and distinguishing features, clarifying easily confused categories. After configuration, request contracts and return classifications using those categories. |
| Credit query | How many credits do I have left? | After obtaining credentials, query the available credits for the current region and return the balance directly. No file upload or processing is required. A failed query does not mean a zero balance. |
| User feedback | Why can't it handle this file type? This feature is hard to use. Why can't I export the way I need? | Summarize the scenario, desired outcome, actual problem, and missing capability from context, then submit through the user feedback API. Distinguish perceived limitations from confirmed ones; one failed call does not prove a capability is unsupported. Acknowledge successful submission without promising a release date. |

Workflows depend on capabilities actually available to the user's account. If no workflow matches, explain which business process and review rules need configuration. Creating a field extraction app does not implement a complete review workflow.

## Document Formats Supported by ADP

### Supported File Formats

| Document type | File formats |
| --- | --- |
| Image | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff` |
| Office | `.xls`, `.xlsx`, `.doc`, `.docx`, `.ppt`, `.pptx` |
| Other | `.pdf`, `.ofd` |

### File Limits

| Limit | Description |
| --- | --- |
| Size limit | Up to 50 MB per file. |
| Count limit | No limit on the total number of files to process. Submit and queue files in batches within the concurrency and queue limits for the account type. Submit remaining files as capacity becomes available. |
| Page limit | Up to 260 pages per file. |

Check file format, size, and page count before submission. If a file exceeds these limits or uses an unsupported format, guide the user to convert or split it before processing. A file URL is an input method; the referenced file must still meet the format and file limits.

## Detailed Steps

### Step 1: Authorize and Query Credits and Available Applications

ADP provides separate public cloud services for users in China and overseas. Accessing a nearby service helps improve speed and stability. First-time use requires an API key to link and authorize the account. Use the conversation language to provide the appropriate registration or sign-in entry and guide the user to obtain a key.

| Conversation language | Guidance |
| --- | --- |
| Chinese | 使用前需完成授权。请 [登录 ADP](https://adp.laiye.com/?utm_source=github&from=getkey)，获取 API Key 并安全提供。 |
| Other languages | Please [sign in to ADP](https://adp-global.laiye.com/?utm_source=github&from=getkey) to get your API key and provide it securely for authorization. |

Immediately after successful authentication, perform these queries without requiring another user request:

1. **Credits and account type:** Retrieve available credits and whether the account is free or paid. Determine concurrency and queue limits using the [batch processing rules](#step-3-process-multiple-files-in-a-batch).
2. **Template list:** Retrieve available templates and their capabilities for copying when no suitable app exists.
3. **Application list:** Retrieve existing apps and their capabilities, prioritizing apps ready for direct use.

Briefly report available credits and proceed to file processing: use an existing app first, then copy a suitable template. Create a custom extraction app only when neither an app nor a template covers the extraction need. Suggest recharging when credits are insufficient. If a query fails, explain what is unknown; do not treat an unknown balance as zero or a failed list query as an empty list.

### Step 2: Request Files and Match a Processing Solution

Guide the user to provide files and a processing goal, reusing information already supplied. Use file URLs for processing calls; first obtain URLs for local files through the upload interface.

Select the appropriate capability based on file content and the goal using [User Scenarios and Intent Recognition](#user-scenarios-and-intent-recognition), then follow the table below.

| Scenario | Recommended action | Example |
| --- | --- | --- |
| Scenario 1: A suitable app already exists | Match the app's actual capabilities to the user's goal, process the files directly, and return results. | The user needs order line items and already has a suitable order extraction app. Use that app directly. |
| Scenario 2: No suitable app exists, but a suitable template is available | Match a template → Copy it to the user's account to create an app → Complete necessary configuration → Process files and return results. | The user needs to review corporate payment documents and has no corresponding app, but an accounts payable review template is available. Copy, configure, and run it. |
| Scenario 3: Neither a suitable app nor a suitable template exists | **Document extraction:** Define fields → Generate prompts → Create an app → Extract; reuse fields already specified.<br>**Document classification:** Define category names, descriptions, and distinguishing criteria → Configure and run the connected classification capability.<br>**Document parsing or workflows:** If no capability is available, explain the required configuration rather than substituting an extraction app. | The user needs contract parties, amount, and payment terms, but no existing app or template fits. Create a custom app for those fields and extract. |

Retain successfully copied or created apps for reuse instead of recreating them for similar tasks.

### Step 3: Process Multiple Files in a Batch

When multiple files are provided together, organize batch processing automatically without requiring separate requests for each file.

| Account type | Maximum concurrent documents | Queue capacity (tasks) |
| --- | --- | --- |
| Free | 2 | 10 |
| Paid | 10 | 15 |

Concurrency limits the number of documents being processed simultaneously. Queue capacity limits the queued tasks accepted by the service. Submissions exceeding queue capacity are rejected rather than automatically queued and must be resubmitted when capacity becomes available. Determine queue occupancy from actual service responses; do not simply add concurrency and queue capacity to calculate how many tasks can be submitted at once.

#### Synchronous and Asynchronous Processing

Prefer synchronous APIs by default, including ordinary batches processed in groups within the concurrency limit. Consider asynchronous APIs only for exceptionally large file counts or when the user explicitly describes a large document containing hundreds of pages. Multiple files alone are not a reason to default to asynchronous processing.

When using asynchronous APIs:

1. Save the task identifier and its source file after successful submission. A task identifier confirms submission, not completion.
2. Query the original task at the interval recommended by the API and inspect its actual state. Continue waiting while queued or running; retrieve results on success, or record the reason and release the slot on failure or cancellation. Engineers will supply polling intervals and terminal status values; do not guess them.
3. Use bounded retries with backoff for temporary query failures. When the waiting limit is reached, retain task identifiers and report processing or unconfirmed status for later queries. Keep the slot reserved or pause new submissions while status is unresolved; do not create replacement tasks.
4. Do not automatically resubmit a timed-out synchronous request through an asynchronous API. Verify acceptance first to avoid duplicate processing or charges.

#### Batch Processing Rules

1. **Match apps:** Select a solution using [Step 2](#step-2-request-files-and-match-a-processing-solution) and reuse apps for similar files.
2. **Submit in batches:** All files share the account's concurrency and queue limits. Keep files exceeding available capacity on a local pending-submission list. Use small batches when queue occupancy is unknown. Asynchronous tasks release their slots only when they actually finish.
3. **Resubmit after a full queue:** Wait for capacity before resubmitting only tasks explicitly rejected and not accepted. Do not resubmit accepted tasks; verify timed-out requests with unknown status first.
4. **Handle exceptions:** A single-file failure does not invalidate other results. Pause or adjust submissions on insufficient credits, invalid authentication, or rate limiting, avoiding repeated immediate retries.
5. **Keep records:** Record each file's source, app, status, and result. Finish with a processing summary and pending-submission list so work can resume.

### Step 4: Return Results and Guide Reuse

- **Single file:** Return results with a brief explanation in JSON, a table, or readable text as requested.
- **Batch:** Report total, succeeded, failed, processing, pending-confirmation, and not-submitted counts, then provide per-file results or result files.
- **Integrity:** Preserve original extracted information and distinguish API values from agent summaries, calculations, or formatting.
- **Exceptions:** Clearly mark missing fields, low confidence, verification exceptions, and failures. Do not fill absent information with asserted facts.
- **Reuse:** If a custom app was created, explain that similar future documents can use it directly. Reassess configuration when field requirements change.
- **Truthful status:** Report queries, creation, or processing as complete only when actual responses support it. If technical capabilities are not connected, explain that guidance is available without claiming execution.

When an API call fails or returns an error code, read the [Error Handling Reference](references/error-handling.md) to identify the cause and follow the recovery guidance.

## Other Scenarios

### User Feedback

When users complain about the product experience, ask “Why can't it…?”, or request unsupported capabilities, summarize the context and call the user feedback API:

- **Category:** Distinguish usage issues (errors, inaccurate extraction, or abnormal execution) from feature requests (new capabilities or improvements). Summarize the business scenario and desired capability for feature requests; ask about diagnostic attachments for usage issues as described below.
- **Content:** Include the business scenario, file type, desired task, actual behavior, limitations or missing capabilities, and approaches already tried. Distinguish the user's statements, confirmed facts, and unverified assessments. Do not invent context.
- **Attachment consent:** For usage issues, ask whether the user is willing to include the relevant execution logs, extraction configuration, and processed files. Submit only materials explicitly authorized by the user. After consent to include execution logs, make a call to the execution log API to retrieve the corresponding task logs before attaching them. If they decline or do not respond, submit text feedback only. Authorization to process files is not authorization to attach them to feedback.
- **Submission:** Send a relevant summary and authorized attachments, removing credentials such as API keys and unnecessary personal or financial information. Do not attach the entire conversation. Update or consolidate duplicate feedback. Report attachment upload failures separately without claiming the attachments were submitted.
- **Follow-up contact:** Prefer an existing account contact available for feedback follow-up. If none is available, request contact details and associate them with the feedback so ADP can contact the user promptly after handling the issue.
- **Outcome:** Briefly acknowledge successful submission and retain a feedback ID if returned. If the API is unavailable, fails, or leaves submission status unknown, explain and retain the summary without claiming it was recorded. Do not promise implementation or delivery dates.

Attachment consent message for usage issues:

> To help diagnose the issue faster, would you be willing to include the relevant execution logs, extraction configuration, and processed files as attachments? ADP will use these materials solely to address this issue, not for any other purpose, and will contact you as soon as the issue has been handled. You can still submit feedback without attachments.

### Remaining Credits and Recharge Guidance

When the user asks about remaining credits, query and return the available account balance without requiring files. Apply the following rules whenever credits are queried, including after first authorization or during processing:

- **Below 50 credits:** Report the actual balance and guide the user to sign in to ADP to recharge. Both package-based and custom recharge options are supported.
- **50 credits or more:** Return the balance normally without a low-balance reminder.
- **Query failed or balance unknown:** Explain that the balance could not be retrieved; do not treat it as zero.

Recharge message:

> Your remaining balance is {actual balance} credits, which is below 50. You can [sign in to ADP](https://adp.laiye.com/), click “My Account,” and open “Account Management” to recharge. Both package-based and custom recharge options are available.

Below 50 is a reminder threshold, not a processing cutoff. Whether processing can continue depends on the actual balance and the credits required by the task.

## Technical Handoff Checklist

The following capabilities are required to implement this framework. Engineers will supply the specific endpoints and parameters.

| Capability | Business input | Business output |
| --- | --- | --- |
| Authentication and region resolution | Service region selected from the conversation language, API key | Authentication status and account region |
| Credits and plan query | Authenticated account | Available credits, account type, concurrency and queue limits |
| Template and app discovery and matching | User intent, available templates, existing apps, and required configuration | Recommended app, template to copy, or need for customization |
| File intake | Uploads, file links, or local paths | Processable files and source records |
| Prompt generation | Field requirements and sample documents | Extraction prompts and configurable field descriptions |
| Custom app creation | App name, fields, and prompts | Reusable app identifier and configuration |
| Document parsing and extraction | Files, target app, processing goal | Raw results or queryable task records |
| Batch scheduling and status queries | Files, app assignments, account concurrency and queue limits | Queue occupancy, per-file acceptance status and results, resubmission list |
| Result presentation | Raw results and requested output format | Single-file output, batch summary, and exports when needed |
| User feedback | Redacted scenario, desired outcome, actual issue, and missing-capability summary | Submission status and feedback ID, if available |

