#!/usr/bin/env python3
"""Create a demo-ready Lark Base workspace for order-auto-entry.

This script deliberately does not initialize lark-cli itself; run setup_check.py
first and fix CLI/auth issues there.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


TEXT_FIELDS = [
    "订单编号",
    "卖方名称",
    "买方/客户名称",
    "买方/客户地址",
    "收货方名称",
    "客户收货地址",
    "币种",
    "客户订单商品号",
    "商品名称/规格",
    "税率",
    "订单币种",
    "来源文件",
    "明细唯一键",
    "来源邮件ID",
    "来源邮箱",
    "来源邮件主题",
]

NUMBER_FIELDS = [
    ("订单总金额", 2),
    ("数量", 4),
    ("单价（含税）", 4),
    ("总金额（含税）", 2),
    ("单价含税", 4),
    ("总金额", 2),
]

DATE_FIELDS = ["订单日期", "交货日期", "到货日期"]

FORMULA_FIELD_NAMES = {
    "审核状态",
    "审核说明",
    "来也 SKU",
    "标准售价 USD",
    "报价有效期",
    "上次成交价USD",
    "客户历史订单数",
    "价差百分比",
}

AUDIT_STATUS_OPTIONS = [
    "✅ 通过",
    "⚠️ 需人工审核",
    "待审核",
]

MANUAL_ACTION_OPTIONS = ["待处理", "审核通过", "退回补资料", "暂缓"]
FLOW_STATUS_OPTIONS = ["待归档", "归档"]
OWNER_FIELD_NAME = "审核负责人"
ARCHIVE_WRITTEN_FIELD_NAME = "已写入历史"
CURRENT_USER_PLACEHOLDER = "<CURRENT_USER_OPEN_ID>"
ARCHIVE_WORKFLOW_TITLE = "审核通过订单自动归档工作流"
TABLE_RENAME_ALIASES = {
    "编码对照表": "商品匹配表",
}
FIELD_RENAME_ALIASES = {
    "商品匹配表": {
        "客户物料代码": "客户订单商品号",
        "物料代码": "客户订单商品号",
        "来也编码": "来也 SKU",
        "产品描述": "商品名称/规格",
        "描述": "商品名称/规格",
        "标准单价USD": "标准售价 USD",
        "价格有效期": "报价有效期",
    },
    "待审核订单表": {
        "物料代码": "客户订单商品号",
        "客户物料代码": "客户订单商品号",
        "描述": "商品名称/规格",
        "产品描述": "商品名称/规格",
        "来也编码": "来也 SKU",
        "标准单价USD": "标准售价 USD",
        "价格有效期": "报价有效期",
    },
    "历史订单表": {
        "物料代码": "客户订单商品号",
        "客户物料代码": "客户订单商品号",
        "来也编码": "来也 SKU",
        "描述": "商品名称/规格",
        "产品描述": "商品名称/规格",
    },
}
FORMULA_FIELD_ALIASES = {
    "审核状态": ["审核状态"],
    "审核说明": ["审核说明"],
    "来也 SKU": ["来也 SKU", "来也编码"],
    "标准售价 USD": ["标准售价 USD", "标准单价USD"],
    "报价有效期": ["报价有效期", "价格有效期"],
    "上次成交价USD": ["上次成交价USD"],
    "客户历史订单数": ["客户历史订单数"],
    "价差百分比": ["价差百分比"],
}

AUDIT_WORKBENCH_VISIBLE_FIELDS = [
    "订单编号",
    "审核状态",
    "审核说明",
    "订单日期",
    "买方/客户名称",
    "订单总金额",
    "币种",
    "客户订单商品号",
    "来也 SKU",
    "商品名称/规格",
    "数量",
    "单价（含税）",
    "总金额（含税）",
    "交货日期",
    "订单源文件",
    "审核负责人",
    "人工审核动作",
    "流转状态",
]

CODE_MAP_VISIBLE_FIELDS = [
    "来也 SKU",
    "客户名称",
    "客户订单商品号",
    "商品名称/规格",
    "标准售价 USD",
    "币种",
    "报价有效期",
    "供应商/品牌",
    "状态",
]

CODE_MAP_FIELDS = [
    {"name": "来也 SKU", "type": "text"},
    {"name": "客户名称", "type": "text"},
    {"name": "客户订单商品号", "type": "text"},
    {"name": "商品名称/规格", "type": "text"},
    {"name": "标准售价 USD", "type": "number", "style": {"type": "plain", "precision": 4, "thousands_separator": True}},
    {"name": "币种", "type": "text"},
    {"name": "报价有效期", "type": "datetime", "style": {"format": "yyyy-MM-dd"}},
    {"name": "供应商/品牌", "type": "text"},
    {"name": "状态", "type": "select", "multiple": False, "options": [{"name": "有效"}, {"name": "待维护"}]},
]

HISTORY_FIELDS = [
    {"name": "客户名称", "type": "text"},
    {"name": "历史订单编号", "type": "text"},
    {"name": "订单日期", "type": "datetime", "style": {"format": "yyyy-MM-dd"}},
    {"name": "客户订单商品号", "type": "text"},
    {"name": "来也 SKU", "type": "text"},
    {"name": "数量", "type": "number", "style": {"type": "plain", "precision": 4, "thousands_separator": True}},
    {"name": "成交单价USD", "type": "number", "style": {"type": "plain", "precision": 4, "thousands_separator": True}},
    {"name": "成交金额USD", "type": "number", "style": {"type": "plain", "precision": 2, "thousands_separator": True}},
    {"name": "审核结果", "type": "select", "multiple": False, "options": [{"name": "通过"}, {"name": "人工确认后通过"}]},
    {"name": "来源文件", "type": "text"},
]

CODE_MAP_RECORDS = [
    {
        "客户名称": "深圳蓝海智能制造有限公司",
        "客户订单商品号": "XY0006",
        "来也 SKU": "LY-SP-4000A6",
        "商品名称/规格": "Solder paste / 锡膏 WTO-LF4000A-6",
        "标准售价 USD": 52.0,
        "币种": "USD",
        "报价有效期": "2026-12-31 00:00:00",
        "供应商/品牌": "Laiye",
        "状态": "有效",
    },
    {
        "客户名称": "CÔNG TY TNHH ĐIỆN TỬ SAO VIỆT",
        "客户订单商品号": "VN-CTRL-241",
        "来也 SKU": "LY-AI-EDGE-241",
        "商品名称/规格": "Edge controller module / Bộ điều khiển biên",
        "标准售价 USD": 86.5,
        "币种": "USD",
        "报价有效期": "2026-12-31 00:00:00",
        "供应商/品牌": "Laiye",
        "状态": "有效",
    },
    {
        "客户名称": "บริษัท นิวเวฟ ออโตเมชั่น จำกัด",
        "客户订单商品号": "TH-FLOW-810",
        "来也 SKU": "LY-FLOW-810",
        "商品名称/规格": "Flow inspection module / โมดูลตรวจสอบการไหล",
        "标准售价 USD": 36.0,
        "币种": "USD",
        "报价有效期": "2026-12-31 00:00:00",
        "供应商/品牌": "Laiye",
        "状态": "有效",
    },
    {
        "客户名称": "Rheinwerk Robotics GmbH",
        "客户订单商品号": "DE-OCR-710",
        "来也 SKU": "LY-OCR-710",
        "商品名称/规格": "OCR quality inspection kit / OCR-Prüfkit",
        "标准售价 USD": 120.0,
        "币种": "USD",
        "报价有效期": "2026-02-28 00:00:00",
        "供应商/品牌": "Laiye",
        "状态": "有效",
    },
    {
        "客户名称": "ABB",
        "客户订单商品号": "ABB-NF22E-10",
        "来也 SKU": "WJ-ELE-00341",
        "商品名称/规格": "交流接触器",
        "标准售价 USD": 12.5,
        "币种": "USD",
        "报价有效期": "2026-12-31 00:00:00",
        "供应商/品牌": "ABB",
        "状态": "有效",
    },
    {
        "客户名称": "西门子",
        "客户订单商品号": "SIE-3RT1026",
        "来也 SKU": "WJ-ELE-00892",
        "商品名称/规格": "西门子接触器",
        "标准售价 USD": 18.0,
        "币种": "USD",
        "报价有效期": "2026-06-30 00:00:00",
        "供应商/品牌": "西门子",
        "状态": "有效",
    },
    {
        "客户名称": "施耐德",
        "客户订单商品号": "PHI-LC1D25",
        "来也 SKU": "WJ-ELE-01205",
        "商品名称/规格": "施耐德接触器",
        "标准售价 USD": 15.8,
        "币种": "USD",
        "报价有效期": "2026-12-31 00:00:00",
        "供应商/品牌": "施耐德",
        "状态": "有效",
    },
    {
        "客户名称": "欧姆龙",
        "客户订单商品号": "OMR-MY4N-GS",
        "来也 SKU": "WJ-ELE-02301",
        "商品名称/规格": "欧姆龙继电器",
        "标准售价 USD": 8.2,
        "币种": "USD",
        "报价有效期": "2026-09-30 00:00:00",
        "供应商/品牌": "欧姆龙",
        "状态": "有效",
    },
    {
        "客户名称": "西门子",
        "客户订单商品号": "SIE-6ES7214",
        "来也 SKU": "WJ-PLC-00156",
        "商品名称/规格": "西门子PLC模块",
        "标准售价 USD": 320.0,
        "币种": "USD",
        "报价有效期": "2026-12-31 00:00:00",
        "供应商/品牌": "西门子",
        "状态": "有效",
    },
    {
        "客户名称": "ABB",
        "客户订单商品号": "ABB-S201-C16",
        "来也 SKU": "WJ-ELE-00512",
        "商品名称/规格": "ABB断路器",
        "标准售价 USD": 22.0,
        "币种": "USD",
        "报价有效期": "2027-03-31 00:00:00",
        "供应商/品牌": "ABB",
        "状态": "有效",
    },
    {
        "客户名称": "施耐德",
        "客户订单商品号": "PHI-XB4BA21",
        "来也 SKU": "WJ-ELE-01876",
        "商品名称/规格": "施耐德按钮",
        "标准售价 USD": 6.5,
        "币种": "USD",
        "报价有效期": "2026-12-31 00:00:00",
        "供应商/品牌": "施耐德",
        "状态": "有效",
    },
    {
        "客户名称": "欧姆龙",
        "客户订单商品号": "OMR-E3Z-D61",
        "来也 SKU": "WJ-SEN-00234",
        "商品名称/规格": "欧姆龙传感器",
        "标准售价 USD": 45.0,
        "币种": "USD",
        "报价有效期": "2026-06-30 00:00:00",
        "供应商/品牌": "欧姆龙",
        "状态": "有效",
    },
    {
        "客户名称": "西门子",
        "客户订单商品号": "SIE-3SB3000",
        "来也 SKU": "WJ-ELE-02001",
        "商品名称/规格": "西门子按钮",
        "标准售价 USD": 9.8,
        "币种": "USD",
        "报价有效期": "2026-12-31 00:00:00",
        "供应商/品牌": "西门子",
        "状态": "有效",
    },
    {
        "客户名称": "施耐德",
        "客户订单商品号": "PHI-XMLA010D2S11",
        "来也 SKU": "WJ-SEN-00567",
        "商品名称/规格": "施耐德压力传感器",
        "标准售价 USD": 78.0,
        "币种": "USD",
        "报价有效期": "2026-09-30 00:00:00",
        "供应商/品牌": "施耐德",
        "状态": "有效",
    },
]

HISTORY_RECORDS = [
    {
        "客户名称": "深圳蓝海智能制造有限公司",
        "历史订单编号": "LYCN-PO-202604-008",
        "订单日期": "2026-04-18 00:00:00",
        "客户订单商品号": "XY0006",
        "来也 SKU": "LY-SP-4000A6",
        "数量": 18,
        "成交单价USD": 52.0,
        "成交金额USD": 936.0,
        "审核结果": "通过",
        "来源文件": "history-cn-202604.pdf",
    },
    {
        "客户名称": "深圳蓝海智能制造有限公司",
        "历史订单编号": "LYCN-PO-202605-014",
        "订单日期": "2026-05-22 00:00:00",
        "客户订单商品号": "XY0006",
        "来也 SKU": "LY-SP-4000A6",
        "数量": 22,
        "成交单价USD": 52.0,
        "成交金额USD": 1144.0,
        "审核结果": "通过",
        "来源文件": "history-cn-202605.pdf",
    },
    {
        "客户名称": "CÔNG TY TNHH ĐIỆN TỬ SAO VIỆT",
        "历史订单编号": "LYVN-PO-202605-009",
        "订单日期": "2026-05-19 00:00:00",
        "客户订单商品号": "VN-CTRL-241",
        "来也 SKU": "LY-AI-EDGE-241",
        "数量": 10,
        "成交单价USD": 86.5,
        "成交金额USD": 865.0,
        "审核结果": "通过",
        "来源文件": "history-vn-202605.pdf",
    },
    {
        "客户名称": "Rheinwerk Robotics GmbH",
        "历史订单编号": "LYDE-PO-202601-011",
        "订单日期": "2026-01-15 00:00:00",
        "客户订单商品号": "DE-OCR-710",
        "来也 SKU": "LY-OCR-710",
        "数量": 5,
        "成交单价USD": 120.0,
        "成交金额USD": 600.0,
        "审核结果": "人工确认后通过",
        "来源文件": "history-de-202601.pdf",
    },
    {
        "客户名称": "华为技术有限公司",
        "历史订单编号": "HW-2025-0312",
        "订单日期": "2025-03-12 00:00:00",
        "客户订单商品号": "ABB-NF22E-10",
        "来也 SKU": "WJ-ELE-00341",
        "数量": 200,
        "成交单价USD": 12.5,
        "成交金额USD": 2500.0,
        "审核结果": "通过",
        "来源文件": "history-hw-202503.pdf",
    },
    {
        "客户名称": "华为技术有限公司",
        "历史订单编号": "HW-2025-1108",
        "订单日期": "2025-11-08 00:00:00",
        "客户订单商品号": "SIE-3RT1026",
        "来也 SKU": "WJ-ELE-00892",
        "数量": 150,
        "成交单价USD": 18.0,
        "成交金额USD": 2700.0,
        "审核结果": "通过",
        "来源文件": "history-hw-202511.pdf",
    },
    {
        "客户名称": "华为技术有限公司",
        "历史订单编号": "HW-2026-0215",
        "订单日期": "2026-02-15 00:00:00",
        "客户订单商品号": "OMR-E3Z-D61",
        "来也 SKU": "WJ-SEN-00234",
        "数量": 80,
        "成交单价USD": 45.0,
        "成交金额USD": 3600.0,
        "审核结果": "通过",
        "来源文件": "history-hw-202602.pdf",
    },
    {
        "客户名称": "深圳麦米电气供应链",
        "历史订单编号": "MM-2025-0820",
        "订单日期": "2025-08-20 00:00:00",
        "客户订单商品号": "ABB-NF22E-10",
        "来也 SKU": "WJ-ELE-00341",
        "数量": 100,
        "成交单价USD": 12.5,
        "成交金额USD": 1250.0,
        "审核结果": "通过",
        "来源文件": "history-mm-202508.pdf",
    },
    {
        "客户名称": "深圳麦米电气供应链",
        "历史订单编号": "MM-2026-0118",
        "订单日期": "2026-01-18 00:00:00",
        "客户订单商品号": "SIE-3RT1026",
        "来也 SKU": "WJ-ELE-00892",
        "数量": 120,
        "成交单价USD": 18.0,
        "成交金额USD": 2160.0,
        "审核结果": "通过",
        "来源文件": "history-mm-202601.pdf",
    },
    {
        "客户名称": "比亚迪股份",
        "历史订单编号": "BYD-2025-0905",
        "订单日期": "2025-09-05 00:00:00",
        "客户订单商品号": "PHI-LC1D25",
        "来也 SKU": "WJ-ELE-01205",
        "数量": 500,
        "成交单价USD": 15.8,
        "成交金额USD": 7900.0,
        "审核结果": "通过",
        "来源文件": "history-byd-202509.pdf",
    },
    {
        "客户名称": "比亚迪股份",
        "历史订单编号": "BYD-2026-0220",
        "订单日期": "2026-02-20 00:00:00",
        "客户订单商品号": "SIE-6ES7214",
        "来也 SKU": "WJ-PLC-00156",
        "数量": 20,
        "成交单价USD": 320.0,
        "成交金额USD": 6400.0,
        "审核结果": "通过",
        "来源文件": "history-byd-202602.pdf",
    },
    {
        "客户名称": "大疆创新",
        "历史订单编号": "DJI-2025-1012",
        "订单日期": "2025-10-12 00:00:00",
        "客户订单商品号": "OMR-MY4N-GS",
        "来也 SKU": "WJ-ELE-02301",
        "数量": 300,
        "成交单价USD": 8.2,
        "成交金额USD": 2460.0,
        "审核结果": "通过",
        "来源文件": "history-dji-202510.pdf",
    },
    {
        "客户名称": "大疆创新",
        "历史订单编号": "DJI-2026-0308",
        "订单日期": "2026-03-08 00:00:00",
        "客户订单商品号": "ABB-S201-C16",
        "来也 SKU": "WJ-ELE-00512",
        "数量": 80,
        "成交单价USD": 22.0,
        "成交金额USD": 1760.0,
        "审核结果": "通过",
        "来源文件": "history-dji-202603.pdf",
    },
    {
        "客户名称": "宁德时代",
        "历史订单编号": "CATL-2025-1120",
        "订单日期": "2025-11-20 00:00:00",
        "客户订单商品号": "PHI-XB4BA21",
        "来也 SKU": "WJ-ELE-01876",
        "数量": 400,
        "成交单价USD": 6.5,
        "成交金额USD": 2600.0,
        "审核结果": "通过",
        "来源文件": "history-catl-202511.pdf",
    },
    {
        "客户名称": "立讯精密",
        "历史订单编号": "LX-2026-0312",
        "订单日期": "2026-03-12 00:00:00",
        "客户订单商品号": "PHI-XMLA010D2S11",
        "来也 SKU": "WJ-SEN-00567",
        "数量": 30,
        "成交单价USD": 78.0,
        "成交金额USD": 2340.0,
        "审核结果": "通过",
        "来源文件": "history-lx-202603.pdf",
    },
]

DEMO_RECORDS = [
    {
        "订单编号": "LYCN-PO-202606-001",
        "买方/客户名称": "深圳蓝海智能制造有限公司",
        "卖方名称": "Laiye Technology Co., Ltd.",
        "客户订单商品号": "XY0006",
        "商品名称/规格": "Solder paste / 锡膏 WTO-LF4000A-6",
        "数量": 20,
        "单价含税": 52.0,
        "总金额": 1040.0,
        "订单币种": "USD",
        "订单日期": "2026-06-10 00:00:00",
        "到货日期": "2026-07-05 00:00:00",
        "收货方名称": "深圳蓝海智能制造有限公司",
        "客户收货地址": "中国广东省深圳市南山区科技园北区 18 栋 5F",
        "来源文件": "LYCN-PO-202606-001_BlueOcean_MFG.pdf",
        "明细唯一键": "LYCN-PO-202606-001|10|XY0006|2026-07-05|52.00",
        "来也 SKU": "LY-SP-4000A6",
        "标准售价 USD": 52.0,
        "上次成交价USD": 52.0,
        "报价有效期": "2026-12-31 00:00:00",
        "价差百分比": 0,
        "客户历史订单数": 2,
        "审核状态": "✅ 通过",
        "审核说明": "客户、商品、币种、报价有效期和价格校验均通过",
        "人工审核动作": "审核通过",
        "流转状态": "归档",
        "来源邮件主题": "New PO LYCN-PO-202606-001",
        "来源邮箱": "demo-mail-cn",
        "来源邮件ID": "demo-mail-cn-001",
    },
    {
        "订单编号": "LYVN-PO-202606-018",
        "买方/客户名称": "CÔNG TY TNHH ĐIỆN TỬ SAO VIỆT",
        "卖方名称": "Laiye Technology Co., Ltd.",
        "客户订单商品号": "VN-CTRL-241",
        "商品名称/规格": "Edge controller module / Bộ điều khiển biên",
        "数量": 12,
        "单价含税": 86.5,
        "总金额": 1038.0,
        "订单币种": "USD",
        "订单日期": "2026-06-12 00:00:00",
        "到货日期": "2026-07-15 00:00:00",
        "收货方名称": "CÔNG TY TNHH ĐIỆN TỬ SAO VIỆT",
        "客户收货地址": "Lô B2, KCN Long Đức, Đồng Nai, Việt Nam",
        "来源文件": "LYVN-PO-202606-018_SaoViet_Electronics.pdf",
        "明细唯一键": "LYVN-PO-202606-018|10|VN-CTRL-241|2026-07-15|86.50",
        "来也 SKU": "LY-AI-EDGE-241",
        "标准售价 USD": 86.5,
        "上次成交价USD": 86.5,
        "报价有效期": "2026-12-31 00:00:00",
        "价差百分比": 0,
        "客户历史订单数": 2,
        "审核状态": "✅ 通过",
        "审核说明": "客户、商品、币种、报价有效期和价格校验均通过；同一张订单的下一行存在未匹配到内部商品，需要单独复核",
        "人工审核动作": "待处理",
        "流转状态": "待归档",
        "来源邮件主题": "PO from Sao Viet - two line items",
        "来源邮箱": "demo-mail-vn",
        "来源邮件ID": "demo-mail-vn-018",
    },
    {
        "订单编号": "LYVN-PO-202606-018",
        "买方/客户名称": "CÔNG TY TNHH ĐIỆN TỬ SAO VIỆT",
        "卖方名称": "Laiye Technology Co., Ltd.",
        "客户订单商品号": "VN-UNKNOWN-77",
        "商品名称/规格": "Custom sensor harness / Dây cảm biến tùy chỉnh",
        "数量": 30,
        "单价含税": 19.8,
        "总金额": 594.0,
        "订单币种": "USD",
        "订单日期": "2026-06-12 00:00:00",
        "到货日期": "2026-07-20 00:00:00",
        "收货方名称": "CÔNG TY TNHH ĐIỆN TỬ SAO VIỆT",
        "客户收货地址": "Lô B2, KCN Long Đức, Đồng Nai, Việt Nam",
        "来源文件": "LYVN-PO-202606-018_SaoViet_Electronics.pdf",
        "明细唯一键": "LYVN-PO-202606-018|20|VN-UNKNOWN-77|2026-07-20|19.80",
        "来也 SKU": "",
        "标准售价 USD": 0,
        "上次成交价USD": 86.5,
        "报价有效期": "",
        "价差百分比": 0,
        "客户历史订单数": 2,
        "审核状态": "⚠️ 需人工审核",
        "审核说明": "客户订单商品号 VN-UNKNOWN-77 没有匹配到来也 SKU，请确认商品匹配表是否已维护",
        "人工审核动作": "待处理",
        "流转状态": "待归档",
        "来源邮件主题": "PO from Sao Viet - two line items",
        "来源邮箱": "demo-mail-vn",
        "来源邮件ID": "demo-mail-vn-018",
    },
    {
        "订单编号": "LYTH-PO-202606-006",
        "买方/客户名称": "บริษัท นิวเวฟ ออโตเมชั่น จำกัด",
        "卖方名称": "Laiye Technology Co., Ltd.",
        "客户订单商品号": "TH-FLOW-810",
        "商品名称/规格": "Flow inspection module / โมดูลตรวจสอบการไหล",
        "数量": 15,
        "单价含税": 36.0,
        "总金额": 540.0,
        "订单币种": "USD",
        "订单日期": "2026-06-13 00:00:00",
        "到货日期": "2026-07-18 00:00:00",
        "收货方名称": "บริษัท นิวเวฟ ออโตเมชั่น จำกัด",
        "客户收货地址": "88/21 Moo 9, Bangna-Trad Road, Bangkok, Thailand",
        "来源文件": "TH-NW-2026-0620_NewWave_Automation.pdf",
        "明细唯一键": "LYTH-PO-202606-006|10|TH-FLOW-810|2026-07-18|36.00",
        "来也 SKU": "LY-FLOW-810",
        "标准售价 USD": 36.0,
        "上次成交价USD": 0,
        "报价有效期": "2026-12-31 00:00:00",
        "价差百分比": 0,
        "客户历史订单数": 0,
        "审核状态": "⚠️ 需人工审核",
        "审核说明": "买方 บริษัท นิวเวฟ ออโตเมชั่น จำกัด 暂无历史订单记录，请人工确认客户资质和合作条款",
        "人工审核动作": "待处理",
        "流转状态": "待归档",
        "来源邮件主题": "New PO - Thai customer",
        "来源邮箱": "demo-mail-th",
        "来源邮件ID": "demo-mail-th-006",
    },
    {
        "订单编号": "LYDE-PO-202606-027",
        "买方/客户名称": "Rheinwerk Robotics GmbH",
        "卖方名称": "Laiye Technology Co., Ltd.",
        "客户订单商品号": "DE-OCR-710",
        "商品名称/规格": "OCR quality inspection kit / OCR-Prüfkit",
        "数量": 8,
        "单价含税": 150.0,
        "总金额": 1200.0,
        "订单币种": "USD",
        "订单日期": "2026-06-14 00:00:00",
        "到货日期": "2026-07-22 00:00:00",
        "收货方名称": "Rheinwerk Robotics GmbH",
        "客户收货地址": "Hansastrasse 42, 80686 Munich, Germany",
        "来源文件": "LYDE-PO-202606-019_Rheinwerk_Robotics_GmbH.pdf",
        "明细唯一键": "LYDE-PO-202606-027|10|DE-OCR-710|2026-07-22|150.00",
        "来也 SKU": "LY-OCR-710",
        "标准售价 USD": 120.0,
        "上次成交价USD": 120.0,
        "报价有效期": "2026-02-28 00:00:00",
        "价差百分比": 0.25,
        "客户历史订单数": 2,
        "审核状态": "⚠️ 需人工审核",
        "审核说明": "该商品报价有效期到 2026-02-28，已过期，请确认是否仍按此价格接单；客户订单单价 150 USD，与标准售价 120 USD 偏差 25.0%，请复核报价",
        "人工审核动作": "待处理",
        "流转状态": "待归档",
        "来源邮件主题": "Bestellung LYDE-PO-202606-027",
        "来源邮箱": "demo-mail-de",
        "来源邮件ID": "demo-mail-de-027",
    },
]


def field_schema() -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = [{"name": "订单编号", "type": "text"}]
    for name in TEXT_FIELDS:
        if name == "订单编号":
            continue
        fields.append({"name": name, "type": "text"})
    for name, precision in NUMBER_FIELDS:
        fields.append(
            {
                "name": name,
                "type": "number",
                "style": {
                    "type": "plain",
                    "precision": precision,
                    "thousands_separator": True,
                },
            }
        )
    for name in DATE_FIELDS:
        fields.append({"name": name, "type": "datetime", "style": {"format": "yyyy-MM-dd"}})
    fields.append({"name": OWNER_FIELD_NAME, "type": "user", "multiple": False})
    fields.append({"name": "订单源文件", "type": "attachment"})
    fields.append(
        {
            "name": "人工审核动作",
            "type": "select",
            "multiple": False,
            "options": [{"name": name} for name in MANUAL_ACTION_OPTIONS],
        }
    )
    fields.append(
        {
            "name": "流转状态",
            "type": "select",
            "multiple": False,
            "options": [{"name": name} for name in FLOW_STATUS_OPTIONS],
        }
    )
    fields.append({"name": ARCHIVE_WRITTEN_FIELD_NAME, "type": "checkbox"})
    return fields


def enrich_business_order_fields(record: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(record)

    currency = enriched.get("币种") or enriched.get("订单币种")
    if currency:
        enriched["币种"] = currency
        enriched.setdefault("订单币种", currency)

    unit_price = enriched.get("单价（含税）")
    if unit_price in (None, ""):
        unit_price = enriched.get("单价含税")
    if unit_price not in (None, ""):
        enriched["单价（含税）"] = unit_price
        enriched.setdefault("单价含税", unit_price)

    line_total = enriched.get("总金额（含税）")
    if line_total in (None, ""):
        line_total = enriched.get("总金额")
    if line_total not in (None, ""):
        enriched["总金额（含税）"] = line_total
        enriched.setdefault("总金额", line_total)

    delivery_date = enriched.get("交货日期") or enriched.get("到货日期")
    if delivery_date:
        enriched["交货日期"] = delivery_date
        enriched.setdefault("到货日期", delivery_date)

    enriched.setdefault("订单总金额", line_total if line_total not in (None, "") else "")
    enriched.setdefault("买方/客户地址", "")
    enriched.setdefault("税率", "0%")
    return enriched


def demo_records_with_owner(owner_open_id: str) -> list[dict[str, Any]]:
    records = [
        {key: value for key, value in enrich_business_order_fields(record).items() if key not in FORMULA_FIELD_NAMES}
        for record in DEMO_RECORDS
    ]
    if owner_open_id:
        for record in records:
            record[OWNER_FIELD_NAME] = [{"id": owner_open_id}]
    return records


def demo_batch_payload(owner_open_id: str = "") -> dict[str, Any]:
    records = demo_records_with_owner(owner_open_id)
    fields = list(records[0].keys())
    rows = [[record.get(field) if record.get(field) != "" else null_cell_value(field) for field in fields] for record in records]
    return {"fields": fields, "rows": rows}


def batch_payload(records: list[dict[str, Any]], date_fields: set[str] | None = None) -> dict[str, Any]:
    if not records:
        return {"fields": [], "rows": []}
    date_fields = date_fields or set()
    fields = list(records[0].keys())
    rows = []
    for record in records:
        row = []
        for field in fields:
            value = record.get(field)
            if value == "" and field in date_fields:
                value = None
            row.append(value if value is not None else "")
        rows.append(row)
    return {"fields": fields, "rows": rows}


def null_cell_value(field: str) -> Any:
    # Empty date cells must be null rather than an empty string.
    if field in DATE_FIELDS:
        return None
    return ""


def run_command(args: list[str], *, execute: bool, attempts: int = 4) -> dict[str, Any]:
    printable = " ".join(json.dumps(part, ensure_ascii=False) if " " in part else part for part in args)
    if not execute:
        raise RuntimeError("Non-execution mode is disabled for this skill.")
    print(f"[run] {printable}")
    for attempt in range(1, attempts + 1):
        try:
            result = subprocess.run(args, check=True, capture_output=True, text=True)
            break
        except subprocess.CalledProcessError as error:
            combined = f"{error.stdout or ''}\n{error.stderr or ''}"
            if "800070003" in combined or "no operation produced" in combined:
                print("[noop] Lark API reported no persisted change; continuing.", file=sys.stderr)
                return {}
            lower_combined = combined.lower()
            transient = any(
                marker in lower_combined
                for marker in ("limited", "1254291", "800004135", "internal", "server", "timeout", "temporarily", "unavailable", "eof")
            )
            if not transient or attempt >= attempts:
                if error.stdout:
                    print(error.stdout, file=sys.stderr)
                if error.stderr:
                    print(error.stderr, file=sys.stderr)
                raise
            wait_seconds = 3 * attempt
            print(f"[retry] Lark API transient error; retrying in {wait_seconds}s ({attempt}/{attempts})", file=sys.stderr)
            time.sleep(wait_seconds)
    if result.stdout.strip():
        return json.loads(result.stdout)
    return {}


def progress(message: str) -> None:
    print(f"[init] {message}", flush=True)


def elapsed_seconds(started_at: float) -> str:
    return f"{time.time() - started_at:.1f}s"


def find_value(data: Any, keys: set[str], prefix: str | None = None) -> str:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and isinstance(value, str):
                if prefix is None or value.startswith(prefix):
                    return value
        for value in data.values():
            found = find_value(value, keys, prefix)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_value(value, keys, prefix)
            if found:
                return found
    return ""


def run_json_command(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=20)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}
    for candidate in (result.stdout, result.stderr):
        candidate = (candidate or "").strip()
        if not candidate:
            continue
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {"items": data}
    return {}


def current_user_open_id(args: argparse.Namespace, *, execute: bool) -> str:
    if not execute:
        return CURRENT_USER_PLACEHOLDER

    commands = [
        [args.lark_cli, "auth", "status"],
        [args.lark_cli, "auth", "list"],
        [args.lark_cli, "auth", "status", "--format", "json"],
        [args.lark_cli, "auth", "list", "--format", "json"],
    ]
    for command in commands:
        data = run_json_command(command)
        if not data:
            continue
        open_id = (
            find_value(data, {"openId"}, "ou_")
            or find_value(data, {"userOpenId"}, "ou_")
            or find_value(data, {"open_id"}, "ou_")
            or find_value(data, {"user_open_id"}, "ou_")
        )
        if open_id:
            return open_id
    return ""


def list_table_ids(base_token: str, args: argparse.Namespace, *, execute: bool) -> dict[str, str]:
    result = run_command(
        [
            args.lark_cli,
            "base",
            "+table-list",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--format",
            "json",
        ],
        execute=execute,
    )
    tables = result.get("data", {}).get("tables", []) if isinstance(result, dict) else []
    return {table.get("name", ""): table.get("id", "") for table in tables if isinstance(table, dict)}


def migrate_table_names(base_token: str, table_ids: dict[str, str], args: argparse.Namespace, *, execute: bool) -> dict[str, str]:
    updated = dict(table_ids)
    for old_name, new_name in TABLE_RENAME_ALIASES.items():
        if new_name in updated or old_name not in updated:
            continue
        old_table_id = updated[old_name]
        try:
            run_command(
                [
                    args.lark_cli,
                    "base",
                    "+table-update",
                    "--as",
                    args.identity,
                    "--base-token",
                    base_token,
                    "--table-id",
                    old_table_id,
                    "--name",
                    new_name,
                    "--format",
                    "json",
                ],
                execute=execute,
            )
            updated[new_name] = old_table_id
            updated.pop(old_name, None)
            progress(f"表名已迁移：{old_name} -> {new_name}")
        except Exception as exc:
            print(f"[warn] 表名迁移失败，将继续使用旧表并保持兼容：{old_name} -> {new_name} - {exc}", file=sys.stderr)
            updated[new_name] = old_table_id
    return updated


def delete_default_table_if_present(base_token: str, args: argparse.Namespace, *, execute: bool) -> None:
    table_ids = list_table_ids(base_token, args, execute=execute)
    default_table_id = table_ids.get("数据表")
    if not default_table_id:
        return
    run_command(
        [
            args.lark_cli,
            "base",
            "+table-delete",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            default_table_id,
            "--yes",
            "--format",
            "json",
        ],
        execute=execute,
    )


def create_table(
    base_token: str,
    name: str,
    fields: list[dict[str, Any]],
    args: argparse.Namespace,
    *,
    execute: bool,
    view: dict[str, Any] | None = None,
) -> str:
    command = [
        args.lark_cli,
        "base",
        "+table-create",
        "--as",
        args.identity,
        "--base-token",
        base_token or "<BASE_TOKEN_FROM_PREVIOUS_STEP>",
        "--name",
        name,
        "--fields",
        json.dumps(fields, ensure_ascii=False),
    ]
    if view:
        command.extend(["--view", json.dumps(view, ensure_ascii=False)])
    command.extend(["--format", "json"])
    result = run_command(command, execute=execute)
    return find_value(result, {"table_id", "id"}, "tbl")


def set_visible_fields(
    base_token: str,
    table_id: str,
    view_id: str,
    visible_fields: list[str],
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    run_command(
        [
            args.lark_cli,
            "base",
            "+view-set-visible-fields",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--view-id",
            view_id,
            "--json",
            json.dumps({"visible_fields": visible_fields}, ensure_ascii=False),
            "--format",
            "json",
        ],
        execute=execute,
    )


def set_view_filter(
    base_token: str,
    table_id: str,
    view_id: str,
    filter_config: dict[str, Any],
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    run_command(
        [
            args.lark_cli,
            "base",
            "+view-set-filter",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--view-id",
            view_id,
            "--json",
            json.dumps(filter_config, ensure_ascii=False),
            "--format",
            "json",
        ],
        execute=execute,
    )


def list_records(
    base_token: str,
    table_id: str,
    args: argparse.Namespace,
    *,
    execute: bool,
    limit: int = 200,
) -> tuple[list[str], list[str], list[list[Any]]]:
    result = run_command(
        [
            args.lark_cli,
            "base",
            "+record-list",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--limit",
            str(limit),
            "--format",
            "json",
        ],
        execute=execute,
    )
    data = result.get("data", {}) if isinstance(result, dict) else {}
    return data.get("record_id_list") or [], data.get("fields") or [], data.get("data") or []


def batch_update_same_patch(
    base_token: str,
    table_id: str,
    record_ids: list[str],
    patch: dict[str, Any],
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    if not record_ids:
        return
    for start in range(0, len(record_ids), 200):
        run_command(
            [
                args.lark_cli,
                "base",
                "+record-batch-update",
                "--as",
                args.identity,
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--json",
                json.dumps({"record_id_list": record_ids[start : start + 200], "patch": patch}, ensure_ascii=False),
                "--format",
                "json",
            ],
            execute=execute,
        )


def delete_view(
    base_token: str,
    table_id: str,
    view_id: str,
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    run_command(
        [
            args.lark_cli,
            "base",
            "+view-delete",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--view-id",
            view_id,
            "--yes",
            "--format",
            "json",
        ],
        execute=execute,
    )


def rename_view(
    base_token: str,
    table_id: str,
    view_id: str,
    new_name: str,
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    run_command(
        [
            args.lark_cli,
            "base",
            "+view-rename",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--view-id",
            view_id,
            "--name",
            new_name,
            "--format",
            "json",
        ],
        execute=execute,
    )


def configure_audit_views(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> None:
    result = run_command(
        [
            args.lark_cli,
            "base",
            "+view-list",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--format",
            "json",
        ],
        execute=execute,
    )
    views = result.get("data", {}).get("views", []) if isinstance(result, dict) else []
    view_by_name = {view.get("name", ""): view.get("id", "") for view in views if isinstance(view, dict)}
    audit_filter = {"logic": "and", "conditions": [["流转状态", "disjoint", ["归档"]]]}
    stale_markers = ("ADP", "旧版", "排障")

    for view in views:
        view_name = str(view.get("name", ""))
        view_id = str(view.get("id", ""))
        if view_id and view_name != "审核工作台" and any(marker in view_name for marker in stale_markers):
            delete_view(base_token, table_id, view_id, args, execute=execute)

    if not execute:
        set_visible_fields(base_token, table_id, "Grid View", AUDIT_WORKBENCH_VISIBLE_FIELDS, args, execute=execute)
        set_view_filter(base_token, table_id, "Grid View", audit_filter, args, execute=execute)
        rename_view(base_token, table_id, "Grid View", "审核工作台", args, execute=execute)
        return

    grid_view_id = view_by_name.get("Grid View")
    audit_view_id = view_by_name.get("审核工作台")
    if grid_view_id:
        set_visible_fields(base_token, table_id, grid_view_id, AUDIT_WORKBENCH_VISIBLE_FIELDS, args, execute=execute)
        set_view_filter(base_token, table_id, grid_view_id, audit_filter, args, execute=execute)
        if not audit_view_id:
            rename_view(base_token, table_id, grid_view_id, "审核工作台", args, execute=execute)
        elif audit_view_id:
            set_visible_fields(base_token, table_id, audit_view_id, AUDIT_WORKBENCH_VISIBLE_FIELDS, args, execute=execute)
            set_view_filter(base_token, table_id, audit_view_id, audit_filter, args, execute=execute)
        return

    if audit_view_id:
        set_visible_fields(base_token, table_id, audit_view_id, AUDIT_WORKBENCH_VISIBLE_FIELDS, args, execute=execute)
        set_view_filter(base_token, table_id, audit_view_id, audit_filter, args, execute=execute)


def configure_code_map_view(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> None:
    result = run_command(
        [
            args.lark_cli,
            "base",
            "+view-list",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--format",
            "json",
        ],
        execute=execute,
    )
    views = result.get("data", {}).get("views", []) if isinstance(result, dict) else []
    view_by_name = {view.get("name", ""): view.get("id", "") for view in views if isinstance(view, dict)}
    target_view = view_by_name.get("Grid View") or view_by_name.get("商品匹配表") or (views[0].get("id") if views else "")
    if target_view:
        set_visible_fields(base_token, table_id, target_view, CODE_MAP_VISIBLE_FIELDS, args, execute=execute)


def repair_code_map_customer_names(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> None:
    record_ids, fields, rows = list_records(base_token, table_id, args, execute=execute)
    if not record_ids or "客户名称" not in fields:
        return
    customer_index = fields.index("客户名称")
    material_index = fields.index("客户订单商品号") if "客户订单商品号" in fields else -1
    brand_index = fields.index("供应商/品牌") if "供应商/品牌" in fields else -1
    known_customer_by_material = {
        str(record.get("客户订单商品号") or ""): str(record.get("客户名称") or "")
        for record in CODE_MAP_RECORDS
        if record.get("客户订单商品号") and record.get("客户名称")
    }
    updates: dict[str, list[str]] = {}
    for record_id, row in zip(record_ids, rows):
        customer = row[customer_index] if customer_index < len(row) else ""
        if str(customer or "").strip():
            continue
        material = str(row[material_index] if 0 <= material_index < len(row) else "").strip()
        brand = str(row[brand_index] if 0 <= brand_index < len(row) else "").strip()
        repaired_customer = known_customer_by_material.get(material) or brand or "待维护客户"
        updates.setdefault(repaired_customer, []).append(record_id)
    for customer, ids in updates.items():
        batch_update_same_patch(base_token, table_id, ids, {"客户名称": customer}, args, execute=execute)


def normalize_flow_status_field_and_values(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> None:
    fields = list_fields(base_token, table_id, args, execute=execute)
    flow_field = next((field for field in fields if field.get("name") == "流转状态"), None)
    if flow_field:
        update_field_definition(
            base_token,
            table_id,
            str(flow_field.get("id") or "流转状态"),
            {
                "name": "流转状态",
                "type": "select",
                "multiple": False,
                "options": [{"name": name} for name in FLOW_STATUS_OPTIONS],
            },
            args,
            execute=execute,
        )

    record_ids, record_fields, rows = list_records(base_token, table_id, args, execute=execute)
    if not record_ids or "流转状态" not in record_fields:
        return
    status_index = record_fields.index("流转状态")
    pending_ids: list[str] = []
    archived_ids: list[str] = []
    for record_id, row in zip(record_ids, rows):
        value = row[status_index] if status_index < len(row) else ""
        values = value if isinstance(value, list) else [value]
        value_text = str(values[0] if values else "").strip()
        if value_text == "待审核" or not value_text:
            pending_ids.append(record_id)
        elif value_text == "已归档":
            archived_ids.append(record_id)
    batch_update_same_patch(base_token, table_id, pending_ids, {"流转状态": "待归档"}, args, execute=execute)
    batch_update_same_patch(base_token, table_id, archived_ids, {"流转状态": "归档"}, args, execute=execute)


def list_field_names(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> set[str]:
    result = run_command(
        [
            args.lark_cli,
            "base",
            "+field-list",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--format",
            "json",
        ],
        execute=execute,
    )
    fields = result.get("data", {}).get("fields", []) if isinstance(result, dict) else []
    return {field.get("name", "") for field in fields if isinstance(field, dict)}


def list_fields(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> list[dict[str, Any]]:
    result = run_command(
        [
            args.lark_cli,
            "base",
            "+field-list",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--format",
            "json",
        ],
        execute=execute,
    )
    fields = result.get("data", {}).get("fields", []) if isinstance(result, dict) else []
    return [field for field in fields if isinstance(field, dict)]


def field_update_payload(field: dict[str, Any], new_name: str, *, expression: str | None = None) -> dict[str, Any]:
    if expression is not None:
        return {"name": new_name, "type": "formula", "expression": expression}

    payload: dict[str, Any] = {"name": new_name}
    field_type = field.get("type")
    if field_type:
        payload["type"] = field_type
    for key in ("multiple", "options", "style", "description", "property"):
        if key in field and field[key] not in (None, ""):
            payload[key] = field[key]
    if field.get("type") == "formula" and field.get("expression"):
        payload["expression"] = field["expression"]
    return payload


def update_field_definition(
    base_token: str,
    table_id: str,
    field_id: str,
    payload: dict[str, Any],
    args: argparse.Namespace,
    *,
    execute: bool,
    formula: bool = False,
) -> None:
    command = [
        args.lark_cli,
        "base",
        "+field-update",
        "--as",
        args.identity,
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--field-id",
        field_id,
        "--json",
        json.dumps(payload, ensure_ascii=False),
        "--yes",
    ]
    if formula:
        command.append("--i-have-read-guide")
    command.extend(["--format", "json"])
    run_command(command, execute=execute)


def migrate_field_names(
    base_token: str,
    table_id: str,
    table_name: str,
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    rename_map = FIELD_RENAME_ALIASES.get(table_name, {})
    if not rename_map:
        return

    fields = list_fields(base_token, table_id, args, execute=execute)
    field_by_name = {str(field.get("name", "")): field for field in fields}
    for old_name, new_name in rename_map.items():
        if old_name not in field_by_name or new_name in field_by_name:
            continue
        field = field_by_name[old_name]
        if field.get("type") == "formula":
            continue
        field_id = str(field.get("id") or old_name)
        payload = field_update_payload(field, new_name)
        try:
            update_field_definition(base_token, table_id, field_id, payload, args, execute=execute)
            field_by_name[new_name] = {**field, "name": new_name}
            field_by_name.pop(old_name, None)
            progress(f"{table_name} 字段已迁移：{old_name} -> {new_name}")
        except Exception as exc:
            print(f"[warn] 字段迁移失败，后续会保留兼容读取：{table_name}.{old_name} -> {new_name} - {exc}", file=sys.stderr)


def validate_business_terms(
    base_token: str,
    code_table_id: str,
    audit_table_id: str,
    history_table_id: str,
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    """Stop initialization if the business-facing workspace still uses old terms."""
    if not execute:
        return

    table_ids = list_table_ids(base_token, args, execute=execute)
    if "编码对照表" in table_ids:
        raise SystemExit("初始化校验失败：Base 中仍存在旧表名“编码对照表”，应为“商品匹配表”。请删除旧表或重新运行迁移后再试。")
    if "商品匹配表" not in table_ids:
        raise SystemExit("初始化校验失败：未找到“商品匹配表”。")

    checks = [
        ("商品匹配表", code_table_id, {"来也 SKU", "客户订单商品号", "商品名称/规格", "标准售价 USD", "报价有效期"}, {"来也编码", "客户物料代码", "物料代码", "产品描述", "标准单价USD", "价格有效期"}),
        ("待审核订单表", audit_table_id, {"订单编号", "审核状态", "审核说明", "客户订单商品号", "来也 SKU", "商品名称/规格"}, {"来也编码", "物料代码", "产品描述", "标准单价USD", "价格有效期"}),
        ("历史订单表", history_table_id, {"客户订单商品号", "来也 SKU"}, {"来也编码", "物料代码", "产品描述"}),
    ]
    for table_name, table_id, required, forbidden in checks:
        names = list_field_names(base_token, table_id, args, execute=execute)
        missing = sorted(required - names)
        old_terms = sorted(forbidden & names)
        if missing:
            raise SystemExit(f"初始化校验失败：{table_name} 缺少字段：{', '.join(missing)}")
        if old_terms:
            raise SystemExit(f"初始化校验失败：{table_name} 仍存在旧字段：{', '.join(old_terms)}")


def field_id_by_name(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> dict[str, str]:
    return {
        str(field.get("name", "")): str(field.get("id", ""))
        for field in list_fields(base_token, table_id, args, execute=execute)
        if field.get("name") and field.get("id")
    }


def ensure_archive_written_field(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> None:
    existing_fields = list_field_names(base_token, table_id, args, execute=execute)
    if ARCHIVE_WRITTEN_FIELD_NAME in existing_fields:
        return
    run_command(
        [
            args.lark_cli,
            "base",
            "+field-create",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--json",
            json.dumps({"name": ARCHIVE_WRITTEN_FIELD_NAME, "type": "checkbox"}, ensure_ascii=False),
            "--format",
            "json",
        ],
        execute=execute,
    )


def ensure_storage_fields(
    base_token: str,
    table_id: str,
    field_specs: list[dict[str, Any]],
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    existing_fields = list_field_names(base_token, table_id, args, execute=execute)
    for spec in field_specs:
        name = str(spec.get("name") or "")
        if not name or name in existing_fields:
            continue
        run_command(
            [
                args.lark_cli,
                "base",
                "+field-create",
                "--as",
                args.identity,
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--json",
                json.dumps(spec, ensure_ascii=False),
                "--format",
                "json",
            ],
            execute=execute,
        )
        existing_fields.add(name)
        if execute:
            time.sleep(0.2)


def formula_field_specs() -> list[dict[str, str]]:
    effective_currency = 'IF(ISBLANK([订单币种]),[币种],[订单币种])'
    effective_unit_price = 'VALUE(""&IF(ISBLANK([单价（含税）]),[单价含税],[单价（含税）]))'
    effective_standard_price = 'VALUE(""&[标准售价 USD])'
    effective_quote_date = 'TODATE([报价有效期])'
    quote_expired = f'IFERROR(IF(ISBLANK([报价有效期]),FALSE(),IF(ISBLANK([订单日期]),{effective_quote_date}<TODAY(),{effective_quote_date}<[订单日期])),FALSE())'
    price_abnormal = 'IFERROR(ABS([价差百分比])>0.2,FALSE())'
    return [
        {
            "name": "来也 SKU",
            "expression": 'FIRST([商品匹配表].FILTER(CurrentValue.[客户订单商品号]=[客户订单商品号]).[来也 SKU])',
        },
        {
            "name": "标准售价 USD",
            "expression": 'FIRST([商品匹配表].FILTER(CurrentValue.[客户订单商品号]=[客户订单商品号]).[标准售价 USD])',
        },
        {
            "name": "报价有效期",
            "expression": 'FIRST([商品匹配表].FILTER(CurrentValue.[客户订单商品号]=[客户订单商品号]).[报价有效期])',
        },
        {
            "name": "上次成交价USD",
            "expression": 'FIRST([历史订单表].FILTER((CONTAINTEXT(CurrentValue.[客户名称],[买方/客户名称])||CONTAINTEXT([买方/客户名称],CurrentValue.[客户名称]))&&CurrentValue.[客户订单商品号]=[客户订单商品号]).SORTBY([历史订单表].[订单日期],FALSE).[成交单价USD])',
        },
        {
            "name": "客户历史订单数",
            "expression": '[历史订单表].COUNTIF(CONTAINTEXT(CurrentValue.[客户名称],[买方/客户名称])||CONTAINTEXT([买方/客户名称],CurrentValue.[客户名称]))',
        },
        {
            "name": "价差百分比",
            "expression": f'IFERROR(IF({effective_standard_price}>0,({effective_unit_price}-{effective_standard_price})/{effective_standard_price},0),0)',
        },
        {
            "name": "审核状态",
            "expression": f'IFS(ISBLANK([来也 SKU]),"🔴 未匹配到内部商品",{effective_currency}!="USD","🟡 币种异常",IFERROR([客户历史订单数]=0,FALSE()),"🟡 新客户待核",{quote_expired},"🟡 报价已过期",{price_abnormal},"🔴 价格异常",TRUE(),"✅ 通过")',
        },
        {
            "name": "审核说明",
            "expression": f'IFS(ISBLANK([来也 SKU]),"客户订单商品号 "&[客户订单商品号]&" 没有匹配到来也 SKU，请确认商品匹配表是否已维护",{effective_currency}!="USD","订单币种是 "&{effective_currency}&"，当前规则只允许 USD，请确认是否需要换算或退回修改",IFERROR([客户历史订单数]=0,FALSE()),"买方 "&[买方/客户名称]&" 暂无历史订单记录，请人工确认客户资质和合作条款",{quote_expired}&&{price_abnormal},"该商品报价有效期到 "&TEXT({effective_quote_date},"YYYY-MM-DD")&"，已过期，请确认是否仍按此价格接单；客户订单单价 "&{effective_unit_price}&" USD，与标准售价 "&{effective_standard_price}&" USD 偏差 "&[价差百分比]*100&"%，请复核报价",{quote_expired},"该商品报价有效期到 "&TEXT({effective_quote_date},"YYYY-MM-DD")&"，已过期，请确认是否仍按此价格接单",{price_abnormal},"客户订单单价 "&{effective_unit_price}&" USD，与标准售价 "&{effective_standard_price}&" USD 偏差 "&[价差百分比]*100&"%，请复核报价",TRUE(),"客户、商品、币种、报价有效期和价格校验均通过")',
        },
    ]


def create_formula_fields(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> None:
    existing_fields = list_fields(base_token, table_id, args, execute=execute)
    field_by_name = {str(field.get("name", "")): field for field in existing_fields}
    for spec in formula_field_specs():
        name = spec["name"]
        existing_field = next((field_by_name.get(alias) for alias in FORMULA_FIELD_ALIASES.get(name, [name]) if field_by_name.get(alias)), None)
        if existing_field:
            field_id = str(existing_field.get("id") or existing_field.get("name") or name)
            payload = field_update_payload(existing_field, name, expression=spec["expression"])
            try:
                update_field_definition(
                    base_token,
                    table_id,
                    field_id,
                    payload,
                    args,
                    execute=execute,
                    formula=True,
                )
                field_by_name[name] = {**existing_field, "name": name, "expression": spec["expression"], "type": "formula"}
                for alias in FORMULA_FIELD_ALIASES.get(name, []):
                    if alias != name:
                        field_by_name.pop(alias, None)
            except Exception as exc:
                print(f"[warn] 公式字段更新失败，继续保留现状：{name} - {exc}", file=sys.stderr)
            if execute:
                time.sleep(0.5)
            continue
        run_command(
            [
                args.lark_cli,
                "base",
                "+field-create",
                "--as",
                args.identity,
                "--base-token",
                base_token,
                "--table-id",
                table_id,
                "--json",
                json.dumps({"name": name, "type": "formula", "expression": spec["expression"]}, ensure_ascii=False),
                "--i-have-read-guide",
                "--format",
                "json",
            ],
            execute=execute,
        )
        field_by_name[name] = {"name": name, "type": "formula", "expression": spec["expression"]}
        if execute:
            time.sleep(0.5)


def write_records(
    base_token: str,
    table_id: str,
    payload: dict[str, Any],
    args: argparse.Namespace,
    *,
    execute: bool,
) -> None:
    run_command(
        [
            args.lark_cli,
            "base",
            "+record-batch-create",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--json",
            json.dumps(payload, ensure_ascii=False),
            "--format",
            "json",
        ],
        execute=execute,
    )
    if execute:
        time.sleep(1)


def table_has_records(base_token: str, table_id: str, args: argparse.Namespace, *, execute: bool) -> bool:
    result = run_command(
        [
            args.lark_cli,
            "base",
            "+record-list",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--limit",
            "1",
            "--format",
            "json",
        ],
        execute=execute,
    )
    data = result.get("data", {}) if isinstance(result, dict) else {}
    records = data.get("data") or data.get("records") or data.get("items") or []
    record_ids = data.get("record_id_list") or []
    return bool(records or record_ids)


def create_dashboard(base_token: str, args: argparse.Namespace, *, execute: bool) -> str:
    dashboard_result = run_command(
        [
            args.lark_cli,
            "base",
            "+dashboard-create",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--name",
            "全流程订单管理仪表盘",
            "--format",
            "json",
        ],
        execute=execute,
        attempts=6,
    )
    dashboard_id = find_value(dashboard_result, {"dashboard_id", "id"}, "blk")
    if not dashboard_id:
        return ""

    pending_filter = {
        "conjunction": "and",
        "conditions": [{"field_name": "流转状态", "operator": "isNot", "value": "归档"}],
    }
    blocks = [
        (
            "全流程订单管理",
            "text",
            {
                "text": (
                    "# 全流程订单管理\n"
                    "适合：用飞书协作，但订单仍靠邮件附件流转的制造、贸易和供应链团队。\n"
                    "解决：订单附件自动识别入库，自动匹配商品和价格规则，异常订单及时暴露给审核人。\n"
                    "价值：少录单、少漏审、可追溯；审核人从逐行核对变成只盯异常。"
                )
            },
        ),
        ("待审核订单总数", "statistics", {"table_name": "待审核订单表", "count_all": True, "filter": pending_filter}),
        ("历史订单总数", "statistics", {"table_name": "历史订单表", "count_all": True}),
        (
            "待审核订单总金额",
            "statistics",
            {
                "table_name": "待审核订单表",
                "series": [{"field_name": "总金额（含税）", "rollup": "SUM"}],
                "filter": pending_filter,
            },
        ),
        (
            "历史订单商品总数量",
            "statistics",
            {"table_name": "历史订单表", "series": [{"field_name": "数量", "rollup": "SUM"}]},
        ),
        (
            "历史订单数量趋势",
            "line",
            {
                "table_name": "历史订单表",
                "series": [{"field_name": "数量", "rollup": "SUM"}],
                "group_by": [{"field_name": "订单日期", "mode": "integrated", "sort": {"type": "group", "order": "asc"}}],
            },
        ),
        (
            "待审核订单状态分布",
            "pie",
            {
                "table_name": "待审核订单表",
                "count_all": True,
                "group_by": [{"field_name": "审核状态", "mode": "integrated"}],
                "filter": pending_filter,
            },
        ),
        (
            "客户订单金额",
            "bar",
            {
                "table_name": "待审核订单表",
                "series": [{"field_name": "总金额（含税）", "rollup": "SUM"}],
                "group_by": [
                    {
                        "field_name": "买方/客户名称",
                        "mode": "integrated",
                        "sort": {"type": "value", "order": "desc"},
                    }
                ],
                "filter": pending_filter,
            },
        ),
        (
            "历史订单客户排行",
            "bar",
            {
                "table_name": "历史订单表",
                "count_all": True,
                "group_by": [
                    {
                        "field_name": "客户名称",
                        "mode": "integrated",
                        "sort": {"type": "value", "order": "desc"},
                    }
                ],
            },
        ),
    ]
    for name, block_type, data_config in blocks:
        try:
            run_command(
                [
                    args.lark_cli,
                    "base",
                    "+dashboard-block-create",
                    "--as",
                    args.identity,
                    "--base-token",
                    base_token,
                    "--dashboard-id",
                    dashboard_id,
                    "--name",
                    name,
                    "--type",
                    block_type,
                    "--data-config",
                    json.dumps(data_config, ensure_ascii=False),
                    "--format",
                    "json",
                ],
                execute=execute,
                attempts=6,
            )
        except Exception as exc:
            print(f"[warn] 仪表盘卡片创建失败，已跳过：{name} - {exc}", file=sys.stderr)
    try:
        run_command(
            [
                args.lark_cli,
                "base",
                "+dashboard-arrange",
                "--as",
                args.identity,
                "--base-token",
                base_token,
                "--dashboard-id",
                dashboard_id,
                "--format",
                "json",
            ],
            execute=execute,
            attempts=6,
        )
    except Exception as exc:
        print(f"[warn] 仪表盘自动排版失败，仪表盘仍已创建：{exc}", file=sys.stderr)
    return dashboard_id


def collect_workflows(data: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(data, dict):
        if data.get("workflow_id") or data.get("id"):
            found.append(data)
        for value in data.values():
            found.extend(collect_workflows(value))
    elif isinstance(data, list):
        for value in data:
            found.extend(collect_workflows(value))
    return found


def archive_workflow_body(field_ids: dict[str, str]) -> dict[str, Any]:
    def ref(field_name: str) -> list[dict[str, str]]:
        field_id = field_ids.get(field_name, "")
        if not field_id:
            raise ValueError(f"Missing field id for workflow field: {field_name}")
        return [{"value_type": "ref", "value": f"$.archive_trigger.{field_id}"}]

    return {
        "client_token": f"order-auto-archive-{int(time.time())}",
        "title": ARCHIVE_WORKFLOW_TITLE,
        "steps": [
            {
                "id": "archive_trigger",
                "type": "SetRecordTrigger",
                "title": "订单标记为归档",
                "next": "add_history_record",
                "data": {
                    "table_name": "待审核订单表",
                    "record_watch_conjunction": "and",
                    "record_watch_info": [],
                    "field_watch_info": [
                        {
                            "field_name": "流转状态",
                            "operator": "is",
                            "value": [{"value_type": "option", "value": {"name": "归档"}}],
                        }
                    ],
                    "trigger_control_list": [],
                    "condition_list": [
                        {
                            "conjunction": "and",
                            "conditions": [
                                {
                                    "field_name": "审核状态",
                                    "operator": "is",
                                    "value": [{"value_type": "text", "value": "✅ 通过"}],
                                },
                                {
                                    "field_name": ARCHIVE_WRITTEN_FIELD_NAME,
                                    "operator": "isNot",
                                    "value": [{"value_type": "boolean", "value": True}],
                                },
                            ],
                        }
                    ],
                },
            },
            {
                "id": "add_history_record",
                "type": "AddRecordAction",
                "title": "写入历史订单表",
                "next": "mark_source_archived",
                "data": {
                    "table_name": "历史订单表",
                    "field_values": [
                        {"field_name": "客户名称", "value": ref("买方/客户名称")},
                        {"field_name": "历史订单编号", "value": ref("订单编号")},
                        {"field_name": "订单日期", "value": ref("订单日期")},
                        {"field_name": "客户订单商品号", "value": ref("客户订单商品号")},
                        {"field_name": "来也 SKU", "value": ref("来也 SKU")},
                        {"field_name": "数量", "value": ref("数量")},
                        {"field_name": "成交单价USD", "value": ref("单价含税")},
                        {"field_name": "成交金额USD", "value": ref("总金额")},
                        {"field_name": "审核结果", "value": [{"value_type": "option", "value": {"name": "通过"}}]},
                        {"field_name": "来源文件", "value": ref("来源文件")},
                    ],
                },
            },
            {
                "id": "mark_source_archived",
                "type": "SetRecordAction",
                "title": "标记已写入历史",
                "next": None,
                "data": {
                    "table_name": "待审核订单表",
                    "max_set_record_num": 1,
                    "field_values": [
                        {
                            "field_name": ARCHIVE_WRITTEN_FIELD_NAME,
                            "value": [{"value_type": "boolean", "value": True}],
                        }
                    ],
                    "ref_info": {"step_id": "archive_trigger"},
                },
            },
        ],
    }


def create_or_update_archive_workflow(
    base_token: str,
    audit_table_id: str,
    args: argparse.Namespace,
    *,
    execute: bool,
) -> str:
    if not execute:
        fake_fields = {name: f"fld_{index}" for index, name in enumerate(AUDIT_WORKBENCH_VISIBLE_FIELDS, 1)}
        fake_fields["来源文件"] = "fld_source_file"
        body = archive_workflow_body(fake_fields)
        run_command(
            [
                args.lark_cli,
                "base",
                "+workflow-create",
                "--as",
                args.identity,
                "--base-token",
                base_token,
                "--json",
                json.dumps(body, ensure_ascii=False),
                "--format",
                "json",
            ],
            execute=execute,
        )
        return "<workflow-id>"

    fields = field_id_by_name(base_token, audit_table_id, args, execute=execute)
    body = archive_workflow_body(fields)
    list_result = run_command(
        [
            args.lark_cli,
            "base",
            "+workflow-list",
            "--as",
            args.identity,
            "--base-token",
            base_token,
            "--format",
            "json",
        ],
        execute=execute,
    )
    existing_id = ""
    for workflow in collect_workflows(list_result):
        title = str(workflow.get("title") or workflow.get("name") or "")
        workflow_id = str(workflow.get("workflow_id") or workflow.get("id") or "")
        if title == ARCHIVE_WORKFLOW_TITLE and workflow_id.startswith("wkf"):
            existing_id = workflow_id
            break

    if existing_id:
        run_command(
            [
                args.lark_cli,
                "base",
                "+workflow-update",
                "--as",
                args.identity,
                "--base-token",
                base_token,
                "--workflow-id",
                existing_id,
                "--json",
                json.dumps(body, ensure_ascii=False),
                "--format",
                "json",
            ],
            execute=execute,
        )
        workflow_id = existing_id
    else:
        result = run_command(
            [
                args.lark_cli,
                "base",
                "+workflow-create",
                "--as",
                args.identity,
                "--base-token",
                base_token,
                "--json",
                json.dumps(body, ensure_ascii=False),
                "--format",
                "json",
            ],
            execute=execute,
        )
        workflow_id = find_value(result, {"workflow_id", "id"}, "wkf")

    if workflow_id:
        run_command(
            [
                args.lark_cli,
                "base",
                "+workflow-enable",
                "--as",
                args.identity,
                "--base-token",
                base_token,
                "--workflow-id",
                workflow_id,
                "--format",
                "json",
            ],
            execute=execute,
        )
    return workflow_id


def load_config(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "skill_name": "order-auto-entry",
        "version": "2.0.0",
        "description": "采购订单邮件收单、ADP 识别与飞书 Base 待审核录入",
        "adp_provider": "auto",
        "adp_api_base_url": "https://adp.laiye.com",
        "adp_api_key_env": "ADP_API_KEY",
        "adp_app_id": "e7ae987c67c211f1b89200505687d9c5",
        "base_token": "<FEISHU_BASE_TOKEN>",
        "code_table_id": "<CODE_MAP_TABLE_ID>",
        "history_table_id": "<HISTORY_TABLE_ID>",
        "audit_table_id": "<PENDING_AUDIT_TABLE_ID>",
        "reviewer_user_id": "<REVIEWER_USER_OPEN_ID>",
        "chat_id": "",
        "lark_identity": "user",
        "notify_identity": "bot",
        "mail_identity": "user",
        "mailbox": "me",
        "attachment_field": "订单源文件",
        "adp_cli": "adp",
        "lark_cli": "lark-cli",
        "settings": {
            "notify_on_success": True,
            "skip_duplicates": True,
            "upload_source_file": True,
            "price_variance_threshold": 0.2,
        },
    }


def save_config(path: Path, updates: dict[str, str]) -> None:
    config = load_config(path)
    config.update({key: value for key, value in updates.items() if value})
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize Lark Base workspace for order-auto-entry")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--lark-cli", default="lark-cli")
    parser.add_argument("--as", dest="identity", default="user", choices=["bot", "user"], help="创建 Base/群使用的身份")
    parser.add_argument("--base-name", default="ADP 采购订单自动审核")
    parser.add_argument("--base-token", default="", help="已有 Base token；提供后复用该 Base，不再新建 Base")
    parser.add_argument("--table-name", default="待审核订单表")
    parser.add_argument("--chat-name", default="订单录入通知")
    parser.add_argument("--chat-id", default="", help="已有通知群 chat_id；提供后不创建新群")
    parser.add_argument("--create-chat", dest="skip_chat", action="store_false", help="额外创建通知群；默认只发审核负责人私信")
    parser.add_argument("--skip-chat", dest="skip_chat", action="store_true", help=argparse.SUPPRESS)
    parser.set_defaults(skip_chat=True)
    parser.add_argument("--skip-demo-data", action="store_true", help="只创建空表，不写入默认演示订单")
    parser.add_argument("--skip-dashboard", action="store_true", help="跳过仪表盘创建；默认创建")
    parser.add_argument("--skip-archive-workflow", action="store_true", help="跳过归档自动化创建；默认创建")
    return parser.parse_args()


def main() -> int:
    started_at = time.time()
    args = parse_args()
    execute = True
    progress("开始初始化 ADP 采购订单自动审核工作台；预计耗时约 1-3 分钟。核心表会先回写配置，仪表盘/归档自动化创建失败也不会要求用户重来。")
    if not shutil.which(args.lark_cli):
        raise SystemExit(f"Command not found: {args.lark_cli}. Run scripts/setup_check.py first.")

    progress("阶段 1/6：获取当前飞书 user，用于写入审核负责人。")
    owner_open_id = current_user_open_id(args, execute=execute)
    if owner_open_id:
        progress(f"已获取当前飞书 user open_id：{owner_open_id}")
    elif execute:
        print(
            "[warn] 未拿到当前飞书 user open_id；初始化会继续，但演示记录不会自动写入“审核负责人”，后续私信通知也需要手工配置 reviewer_user_id。",
            file=sys.stderr,
        )
    config = load_config(args.config)
    configured_base_token = str(config.get("base_token") or "")
    base_token = args.base_token or (configured_base_token if not configured_base_token.startswith("<") else "")
    if base_token:
        progress(f"阶段 2/6：复用已有飞书 Base：{base_token}")
    else:
        progress("阶段 2/6：创建飞书 Base。")
        base_result = run_command(
            [
                args.lark_cli,
                "base",
                "+base-create",
                "--as",
                args.identity,
                "--name",
                args.base_name,
                "--time-zone",
                "Asia/Shanghai",
                "--format",
                "json",
            ],
            execute=execute,
        )
        base_token = find_value(base_result, {"app_token", "base_token", "token"}, "base") or find_value(
            base_result, {"app_token", "base_token", "token"}
        )

    if execute and not base_token:
        raise SystemExit("Base created but base token was not found in CLI response.")
    progress(f"Base 创建完成：{base_token}")

    progress("阶段 3/6：创建商品匹配表、历史订单表、待审核订单表。")
    existing_tables = list_table_ids(base_token, args, execute=execute) if base_token else {}
    existing_tables = migrate_table_names(base_token, existing_tables, args, execute=execute) if base_token else {}
    code_table_id = existing_tables.get("商品匹配表") or create_table(base_token, "商品匹配表", CODE_MAP_FIELDS, args, execute=execute)
    progress(f"商品匹配表就绪：{code_table_id or '商品匹配表'}")
    history_table_id = existing_tables.get("历史订单表") or create_table(base_token, "历史订单表", HISTORY_FIELDS, args, execute=execute)
    progress(f"历史订单表就绪：{history_table_id or '历史订单表'}")
    table_id = existing_tables.get(args.table_name) or create_table(
        base_token,
        args.table_name,
        field_schema(),
        args,
        execute=execute,
    )
    progress(f"待审核订单表就绪：{table_id or args.table_name}")
    delete_default_table_if_present(base_token, args, execute=execute)
    migrate_field_names(base_token, code_table_id or "商品匹配表", "商品匹配表", args, execute=execute)
    migrate_field_names(base_token, history_table_id or "历史订单表", "历史订单表", args, execute=execute)
    migrate_field_names(base_token, table_id or args.table_name, args.table_name, args, execute=execute)
    configure_code_map_view(base_token, code_table_id or "商品匹配表", args, execute=execute)

    progress("阶段 4/6：创建辅助计算字段并配置审核工作台视图。")
    ensure_storage_fields(base_token, table_id or args.table_name, field_schema(), args, execute=execute)
    ensure_archive_written_field(base_token, table_id or args.table_name, args, execute=execute)
    normalize_flow_status_field_and_values(base_token, table_id or args.table_name, args, execute=execute)
    create_formula_fields(base_token, table_id or args.table_name, args, execute=execute)
    configure_audit_views(base_token, table_id or args.table_name, args, execute=execute)
    demo_record_count = 0

    if not args.skip_demo_data:
        progress("阶段 5/6：写入演示商品匹配、历史订单和待审核订单数据。")
        if table_has_records(base_token, code_table_id or "商品匹配表", args, execute=execute):
            progress("商品匹配表已有记录，跳过默认商品匹配数据写入，避免重复。")
        else:
            write_records(
                base_token,
                code_table_id or "商品匹配表",
                batch_payload(CODE_MAP_RECORDS, {"报价有效期"}),
                args,
                execute=execute,
            )
        repair_code_map_customer_names(base_token, code_table_id or "商品匹配表", args, execute=execute)
        if table_has_records(base_token, history_table_id or "历史订单表", args, execute=execute):
            progress("历史订单表已有记录，跳过默认历史数据写入，避免重复。")
        else:
            write_records(
                base_token,
                history_table_id or "历史订单表",
                batch_payload(HISTORY_RECORDS, {"订单日期"}),
                args,
                execute=execute,
            )
        if table_has_records(base_token, table_id or args.table_name, args, execute=execute):
            progress("待审核订单表已有记录，跳过默认待审核演示数据写入，避免重复。")
        else:
            write_records(base_token, table_id or args.table_name, demo_batch_payload(owner_open_id), args, execute=execute)
            demo_record_count = len(DEMO_RECORDS)
        progress(f"演示数据写入完成：待审核订单 {demo_record_count} 条。")
    else:
        progress("阶段 5/6：已跳过演示数据写入。")

    progress("核心工作台已就绪，先回写 config.json，后续订单处理可直接使用。")
    save_config(
        args.config,
        {
            "base_token": base_token,
            "code_table_id": code_table_id,
            "history_table_id": history_table_id,
            "audit_table_id": table_id,
            "reviewer_user_id": owner_open_id,
            "lark_identity": args.identity,
            "attachment_field": "订单源文件",
        },
    )

    archive_workflow_id = ""
    if not args.skip_archive_workflow:
        progress("阶段 6/6：创建归档自动化和全流程订单管理仪表盘。")
        try:
            archive_workflow_id = create_or_update_archive_workflow(
                base_token,
                table_id or args.table_name,
                args,
                execute=execute,
            )
            progress(f"归档自动化就绪：{archive_workflow_id or '<未返回 workflow_id>'}")
        except Exception as exc:
            print(f"[warn] 归档自动化创建失败，核心工作台继续可用：{exc}", file=sys.stderr)
    else:
        progress("已按参数跳过归档自动化创建。")

    dashboard_id = ""
    if not args.skip_dashboard:
        progress("创建全流程订单管理仪表盘。")
        try:
            dashboard_id = create_dashboard(base_token, args, execute=execute)
            progress(f"仪表盘创建完成：{dashboard_id or '<未返回 dashboard_id>'}")
        except Exception as exc:
            print(f"[warn] 仪表盘创建失败，核心工作台继续可用：{exc}", file=sys.stderr)
    else:
        progress("已按参数跳过仪表盘创建。")

    chat_id = args.chat_id
    if not args.skip_chat and not chat_id:
        progress("可选步骤：创建通知群。默认流程不需要通知群，只给审核负责人发私信。")
        chat_result = run_command(
            [
                args.lark_cli,
                "im",
                "+chat-create",
                "--as",
                args.identity,
                "--name",
                args.chat_name,
                "--type",
                "private",
                "--chat-mode",
                "group",
                "--format",
                "json",
            ],
            execute=execute,
        )
        chat_id = find_value(chat_result, {"chat_id", "id"}, "oc_")

    progress("校验业务术语：商品匹配表、来也 SKU、客户订单商品号。")
    validate_business_terms(
        base_token,
        code_table_id or "商品匹配表",
        table_id or args.table_name,
        history_table_id or "历史订单表",
        args,
        execute=execute,
    )

    progress("回写仪表盘、工作流和通知配置。")
    if execute:
        if not table_id:
            raise SystemExit("Table created but table_id was not found in CLI response.")
        save_config(
            args.config,
            {
                "base_token": base_token,
                "code_table_id": code_table_id,
                "history_table_id": history_table_id,
                "audit_table_id": table_id,
                "dashboard_id": dashboard_id,
                "archive_workflow_id": archive_workflow_id,
                "chat_id": chat_id,
                "reviewer_user_id": owner_open_id,
                "lark_identity": args.identity,
                "attachment_field": "订单源文件",
            },
        )
        print(
            json.dumps(
                {
                    "ok": True,
                    "base_token": base_token,
                    "code_table_id": code_table_id,
                    "history_table_id": history_table_id,
                    "audit_table_id": table_id,
                    "dashboard_id": dashboard_id,
                    "archive_workflow_id": archive_workflow_id,
                    "chat_id": chat_id,
                    "reviewer_user_id": owner_open_id,
                    "owner_open_id": owner_open_id,
                    "demo_records_created": demo_record_count,
                    "config": str(args.config),
                    "elapsed": elapsed_seconds(started_at),
                    "next": f"下一步运行：python3 scripts/run_demo.py --config {args.config}",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
