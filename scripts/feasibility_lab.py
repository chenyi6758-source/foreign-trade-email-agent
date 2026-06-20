from __future__ import annotations

import asyncio
import html
import json
import os
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

os.environ["DATABASE_URL"] = "sqlite:///./data/feasibility_test.db"
os.environ["OPENAI_API_KEY"] = ""
os.environ["LLM_API_KEY"] = ""
os.environ["SMTP_HOST"] = ""
os.environ["WHATSAPP_PROVIDER"] = "disabled"
os.environ["COMPANY_NAME"] = "Demo Export Co."
os.environ["COMPANY_PRODUCTS"] = "CNC aluminum parts, industrial valves, custom metal components"
os.environ["SALES_EMAIL"] = "sales@demo-export.test"
os.environ["UNSUBSCRIBE_SECRET"] = "feasibility-unsubscribe-secret"

from app.config import get_settings
from app.db import ensure_database, get_db, rows_to_dicts
from app.services.ai_reply import generate_auto_reply, generate_outreach_draft
from app.services.compliance import append_unsubscribe, cold_outreach_allowed, is_opted_out
from app.services.crm import pipeline_summary, update_lead
from app.services.deliverability import deliverability_status
from app.services.leads import LeadSignal, record_message, upsert_lead
from app.services.prospecting import import_prospect_csv


REPORT_CSS = """
body{font-family:Inter,Segoe UI,Arial,sans-serif;margin:0;background:#f6f8f8;color:#1f282b}
header{padding:28px 36px;background:#fff;border-bottom:1px solid #dde5e7}
h1{margin:0;font-size:28px}p{line-height:1.55}.wrap{padding:24px 36px;display:grid;gap:18px}
section{background:#fff;border:1px solid #dde5e7;border-radius:8px;padding:18px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
.metric{background:#eef7f4;border:1px solid #cfe5df;border-radius:8px;padding:14px}
.metric strong{display:block;font-size:28px;color:#126b5e}
table{width:100%;border-collapse:collapse;font-size:14px}th,td{padding:10px;border-bottom:1px solid #eef2f3;text-align:left;vertical-align:top}
.pass{color:#0b7a4b;font-weight:700}.warn{color:#9a5b00;font-weight:700}.fail{color:#b42318;font-weight:700}
pre{white-space:pre-wrap;background:#f2f5f6;border-radius:6px;padding:12px;overflow:auto}
@media(max-width:900px){.grid{grid-template-columns:1fr}.wrap,header{padding:18px}}
"""


def reset_database() -> None:
    db_path = PROJECT_ROOT / "data" / "feasibility_test.db"
    if db_path.exists():
        db_path.unlink()
    ensure_database()


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def status_label(status: str) -> str:
    css = {"PASS": "pass", "WARN": "warn", "FAIL": "fail"}.get(status, "warn")
    return f'<span class="{css}">{html.escape(status)}</span>'


def write_report(result: dict) -> Path:
    rows = "\n".join(
        "<tr>"
        f"<td>{status_label(check['status'])}</td>"
        f"<td>{html.escape(check['name'])}</td>"
        f"<td>{html.escape(check['detail'])}</td>"
        "</tr>"
        for check in result["checks"]
    )

    leads_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(str(lead.get('name') or lead.get('company') or 'Unknown'))}</td>"
        f"<td>{html.escape(str(lead.get('channel') or ''))}</td>"
        f"<td>{html.escape(str(lead.get('email') or lead.get('phone') or ''))}</td>"
        f"<td>{html.escape(str(lead.get('score') or 0))}</td>"
        f"<td>{html.escape(str(lead.get('tags') or ''))}</td>"
        "</tr>"
        for lead in result["sample_leads"]
    )

    report_html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Foreign Trade Autopilot 可行性测试报告</title>
  <style>{REPORT_CSS}</style>
</head>
<body>
  <header>
    <h1>Foreign Trade Autopilot 可行性测试报告</h1>
    <p>生成时间：{html.escape(result["generated_at"])}。本测试完全离线运行，不需要真实邮箱、WhatsApp、OpenAI 或外部资讯 API。</p>
  </header>
  <main class="wrap">
    <section class="grid">
      <div class="metric"><strong>{result["metrics"]["leads"]}</strong>线索数</div>
      <div class="metric"><strong>{result["metrics"]["messages"]}</strong>消息记录</div>
      <div class="metric"><strong>{result["metrics"]["drafts"]}</strong>待审草稿</div>
      <div class="metric"><strong>{result["metrics"]["pass_rate"]}%</strong>通过率</div>
    </section>
    <section>
      <h2>测试结论</h2>
      <p>{html.escape(result["verdict"])}</p>
    </section>
    <section>
      <h2>检查项</h2>
      <table>
        <thead><tr><th>状态</th><th>项目</th><th>说明</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    <section>
      <h2>样例线索</h2>
      <table>
        <thead><tr><th>客户</th><th>渠道</th><th>联系方式</th><th>评分</th><th>标签</th></tr></thead>
        <tbody>{leads_rows}</tbody>
      </table>
    </section>
    <section>
      <h2>自动回复样例</h2>
      <pre>{html.escape(result["sample_reply"])}</pre>
    </section>
  </main>
</body>
</html>"""
    report_path = PROJECT_ROOT / "data" / "feasibility_report.html"
    report_path.write_text(report_html, encoding="utf-8")
    return report_path


async def run_lab() -> dict:
    get_settings.cache_clear()
    reset_database()
    settings = get_settings()

    checks: list[dict[str, str]] = []

    email_text = (
        "Hi, please send quotation, MOQ and sample lead time for CNC aluminum parts. "
        "We are an importer in Germany."
    )
    email_lead = upsert_lead(
        LeadSignal(
            channel="email",
            name="Alice Buyer",
            email="alice.buyer@example.com",
            company="A&B Import GmbH",
            message=f"RFQ for CNC parts\n{email_text}",
        )
    )
    record_message(email_lead["id"], "email", "inbound", "alice.buyer@example.com", settings.sales_email, email_text, "RFQ for CNC parts")
    sample_reply = await generate_auto_reply(email_text, "Alice", "email", settings)
    record_message(email_lead["id"], "email", "outbound", settings.sales_email, "alice.buyer@example.com", sample_reply, "Re: RFQ for CNC parts", "drafted")
    checks.append(
        {
            "name": "邮件入站与自动回复",
            "status": "PASS" if "Demo Export Co." in sample_reply and "quotation" in sample_reply.lower() else "FAIL",
            "detail": "已模拟客户询价邮件，生成回复草稿并写入消息表。",
        }
    )

    whatsapp_text = "Need price for industrial valves, 500 pcs monthly. Can you quote?"
    whatsapp_lead = upsert_lead(
        LeadSignal(channel="whatsapp", name="Carlos", phone="+15551234567", company="LatAm Valve Distributor", message=whatsapp_text)
    )
    record_message(whatsapp_lead["id"], "whatsapp", "inbound", "+15551234567", "company-whatsapp", whatsapp_text)
    whatsapp_reply = await generate_auto_reply(whatsapp_text, "Carlos", "whatsapp", settings)
    record_message(whatsapp_lead["id"], "whatsapp", "outbound", "company-whatsapp", "+15551234567", whatsapp_reply, status="drafted")
    checks.append(
        {
            "name": "WhatsApp 入站与自动回复",
            "status": "PASS" if "Carlos" in whatsapp_reply and "specifications" in whatsapp_reply.lower() else "FAIL",
            "detail": "已模拟 WhatsApp 客户询盘，生成回复草稿。真实发送需要配置 Twilio 或 Meta。",
        }
    )

    csv_path = PROJECT_ROOT / "examples" / "prospects.csv"
    imported = import_prospect_csv(csv_path.read_text(encoding="utf-8"), source="feasibility-csv")
    checks.append(
        {
            "name": "CSV 获客导入",
            "status": "PASS" if len(imported) >= 2 else "FAIL",
            "detail": f"已从 examples/prospects.csv 导入 {len(imported)} 条潜在线索。",
        }
    )

    with get_db() as conn:
        top_lead = conn.execute("SELECT * FROM leads ORDER BY score DESC LIMIT 1").fetchone()
    checks.append(
        {
            "name": "线索评分",
            "status": "PASS" if top_lead and top_lead["score"] >= 50 else "FAIL",
            "detail": f"最高分线索为 {top_lead['score'] if top_lead else 0} 分，询价、MOQ、报价等意图词会提高评分。",
        }
    )

    updated_lead = update_lead(
        email_lead["id"],
        {
            "stage": "qualified",
            "owner": "Sales A",
            "priority": "high",
            "next_follow_up_at": "2099-01-01T09:00:00",
            "notes": "Demo follow-up after RFQ.",
            "deal_value": 12000,
        },
    )
    pipeline = pipeline_summary()
    checks.append(
        {
            "name": "CRM 跟进阶段",
            "status": "PASS" if updated_lead and updated_lead["stage"] == "qualified" else "FAIL",
            "detail": f"已更新负责人、阶段、优先级、下次跟进和预计金额；漏斗阶段数 {len(pipeline)}。",
        }
    )

    subject, body = await generate_outreach_draft(
        recipient="procurement@example.com",
        product="industrial valves",
        pain_point="supplier comparison for monthly purchasing",
        market="Mexico",
        settings=settings,
    )
    body = append_unsubscribe(body, settings)
    allowed, compliance_note = cold_outreach_allowed(settings, "unknown")
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO outreach_drafts(channel, recipient, subject, body, status, compliance_note)
            VALUES ('email', ?, ?, ?, 'pending_approval', ?)
            """,
            ("procurement@example.com", subject, body, compliance_note),
        )
    checks.append(
        {
            "name": "获客草稿与合规拦截",
            "status": "PASS" if not allowed and "STOP" in body else "FAIL",
            "detail": "陌生客户默认只生成待审核草稿，并自动追加退订说明，不会自动群发。",
        }
    )

    with get_db() as conn:
        draft_count = conn.execute("SELECT COUNT(*) AS total FROM outreach_drafts WHERE status = 'pending_approval'").fetchone()["total"]
    checks.append(
        {
            "name": "人工审核队列",
            "status": "PASS" if draft_count >= 1 else "FAIL",
            "detail": f"待审核草稿 {draft_count} 条，可在发送前编辑标题和正文。",
        }
    )

    with get_db() as conn:
        conn.execute("INSERT INTO opt_outs(email, reason) VALUES (?, ?)", ("blocked@example.com", "test opt-out"))
    checks.append(
        {
            "name": "退订/黑名单检查",
            "status": "PASS" if is_opted_out(email="blocked@example.com") else "FAIL",
            "detail": "系统能识别退订邮箱，发送前可拦截。",
        }
    )

    deliverability = deliverability_status(settings)
    checks.append(
        {
            "name": "邮件送达率基础检查",
            "status": "PASS" if deliverability["manual_dns_records"] else "FAIL",
            "detail": "已生成 SPF、DKIM、DMARC、退订链接和发送频控检查清单。",
        }
    )

    checks.append(
        {
            "name": "真实外部集成",
            "status": "WARN",
            "detail": "SMTP、WhatsApp、OpenAI、RSS 实时资讯需要填入真实账号和网络环境后做联调。",
        }
    )

    with get_db() as conn:
        leads = rows_to_dicts(conn.execute("SELECT * FROM leads ORDER BY score DESC, updated_at DESC").fetchall())
        messages = rows_to_dicts(conn.execute("SELECT * FROM messages ORDER BY created_at DESC").fetchall())
        drafts = rows_to_dicts(conn.execute("SELECT * FROM outreach_drafts ORDER BY created_at DESC").fetchall())

    pass_count = sum(1 for check in checks if check["status"] == "PASS")
    hard_checks = [check for check in checks if check["status"] != "WARN"]
    pass_rate = round(pass_count / max(len(hard_checks), 1) * 100)
    verdict = (
        "本 MVP 适合作为实习/试点项目：离线闭环已打通，能演示自动建线索、自动回复、线索评分、CSV 获客导入、合规草稿审核。"
        "下一阶段应接入真实邮箱入站 webhook、WhatsApp Business、目标行业资讯源和 CRM。"
    )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "metrics": {
            "leads": len(leads),
            "messages": len(messages),
            "drafts": len(drafts),
            "pass_rate": pass_rate,
        },
        "checks": checks,
        "sample_leads": leads[:8],
        "sample_reply": sample_reply,
        "verdict": verdict,
    }


async def main() -> None:
    result = await run_lab()
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    json_path = data_dir / "feasibility_report.json"
    save_json(json_path, result)
    html_path = write_report(result)

    print("Foreign Trade Autopilot feasibility lab")
    print(f"PASS rate: {result['metrics']['pass_rate']}%")
    print(f"Leads: {result['metrics']['leads']}")
    print(f"Messages: {result['metrics']['messages']}")
    print(f"Drafts: {result['metrics']['drafts']}")
    print(f"HTML report: {html_path}")
    print(f"JSON report: {json_path}")
    print()
    for check in result["checks"]:
        print(f"[{check['status']}] {check['name']} - {check['detail']}")


if __name__ == "__main__":
    asyncio.run(main())
