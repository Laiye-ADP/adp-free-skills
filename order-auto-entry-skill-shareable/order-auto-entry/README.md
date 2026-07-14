# order-auto-entry

采购订单自动收单与审核录入 Skill。主要说明见 `SKILL.md`，排障见 `references/`。

默认走 `adp_provider=auto`：优先复用本机 ADP CLI；没有 CLI 时才用 ADP 公有云 API Key 作为备用。推荐先安装 CLI：

```bash
npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli
adp --help
```

如果用户已经安装并配置过 ADP CLI，不要再要求用户提供 `ADP_API_KEY`。API Key 仅作为备用方式：在 `https://adp.laiye.com/` 注册或登录后，进入个人中心获取。

默认配置如下：

```json
{
  "adp_provider": "auto",
  "adp_api_base_url": "https://adp.laiye.com",
  "adp_api_key_env": "ADP_API_KEY",
  "adp_app_id": "e7ae987c67c211f1b89200505687d9c5",
  "adp_cli": "adp"
}
```

`adp_app_id` 默认使用开箱即用订单抽取应用 `e7ae987c67c211f1b89200505687d9c5`；只有要换自己的 ADP 抽取应用时，才需要修改。

```bash
python3 scripts/setup_check.py
python3 scripts/init_lark_workspace.py --config config.json
python3 scripts/run_demo.py --config config.json
python3 scripts/run_demo.py --config config.json --scenario vn-mixed
python3 scripts/run_order_audit.py ./order.pdf --config config.json
python3 scripts/run_order_audit.py --from-mail --config config.json
python3 scripts/run_order_audit.py --from-mail --config config.json --mail-since-hours 24 --mail-query "采购订单"
python3 scripts/run_order_audit.py --from-mail --config config.json --mail-since-hours 24 --poll-interval 300
```

`demo-data/orders/` 内置 4 份可上传 PDF 样本，覆盖正常通过、多行混合、新客户、报价过期且价格异常。4 份均由 HTML 生成后导出 PDF，版式各不相同；`run_demo.py` 默认会真实调用 ADP 识别这些 PDF。

用户说“运行一下”时，目标是端到端完成：ADP 识别、Base 初始化或复用、写入待审核表、上传订单源文件、发送审核负责人卡片私信。只输出 ADP 识别结果不算完成。`run_order_audit.py` 发现 Base/table 仍是占位符时，会先自动执行 `init_lark_workspace.py`；只有 Lark CLI 未授权、ADP CLI 和 API Key 都不可用，或用户指定既有 Base 但没给资源 ID 时才需要中断。缺少 ADP 运行环境时，优先引导用户安装 CLI，不要直接索要 API Key。

用户说“查询最近 24 小时邮箱订单附件”“跑邮箱通道”“给我自动审核”时，不要只列邮件摘要或附件清单。直接运行邮箱入口：它会查询最近 24 小时有附件邮件、下载 PDF/图片附件、调用 ADP、写入待审核表并通知审核负责人。成功处理过的附件会记录在 `work/mail-processed-attachments.json`，后续轮询默认跳过；需要重跑同一附件时加 `--mail-reprocess`。

初始化会创建完整工作台，预计 1-3 分钟：Base、商品匹配表、历史订单表、待审核订单表、公式字段、审核工作台视图、演示数据、归档自动化和全流程订单管理仪表盘。脚本会在核心表就绪后先回写 `config.json`，因此即使仪表盘或工作流遇到飞书临时错误，订单处理主链路仍可继续使用，用户不需要重来。仪表盘会保留一张 `全流程订单管理` 说明文本卡片，用来解释订单附件进入 ADP 识别、待审核、异常复核和归档沉淀的业务闭环。

初始化会创建 `审核负责人` 人员字段，并把演示待审核记录默认分配给当前飞书 user。待审核表默认使用 `审核工作台` 视图，前三列固定为 `订单编号`、`审核状态`、`审核说明`，后续只展示订单核心字段、商品明细、源文件、负责人、人工动作和流转状态；ADP 原始 JSON 仅保存在本地 `work/adp-order-json/` 用于开发排障。订单录入后默认给审核负责人发结构化私信，私信里包含待审核记录链接；邮箱附件会缓存到 `work/mail-order-attachments/`，再挂载到 `订单源文件` 附件列。

审核通知必须走 `run_order_audit.py` 内置的 interactive 卡片发送逻辑，不要手工发送 markdown、普通文本或 Base 链接预览消息。正确效果是白底飞书卡片，标题为“订单已自动录入”，包含订单号、买卖方、商品明细、预审结果和“打开待审核记录”按钮。

分享前不要保留个人 Base、表 ID、审核负责人 ID、通知群 ID、邮箱地址或客户文件。
