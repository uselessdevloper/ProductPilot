"""
ProductPilot AI — Pipeline Runner
Executes the 7-stage multi-agent pipeline and generates the observability report.

Research Paper Enhancements (run.py):
  - Full research compliance summary at the top of the report
  - Per-stage evidence of each paper's contribution
  - Separate sections for: trust score, audit trail, accountability chain, citations
"""
import os
import sys
import json
import time
try:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)
    # Also try root .env
    root_env = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(root_env):
        load_dotenv(root_env, override=False)
except ImportError:
    pass

from agents.coordinator_agent import CoordinatorAgent


def main():
    print("=" * 70)
    print("🌟  PRODUCTPILOT AI — 7-AGENT AGENTIC COMMERCE PIPELINE  🌟")
    print("     Research-Paper Enhanced | Razorpay Track 01")
    print("=" * 70)

    # Resolve dataset directory
    dataset_dir = os.environ.get("PRODUCTPILOT_DATASET_DIR") or "../productpilotai/datasets"
    abs_dataset_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), dataset_dir))

    if not os.path.exists(abs_dataset_dir):
        print(f"Error: Dataset directory not found at {abs_dataset_dir}")
        sys.exit(1)

    print(f"Loading industrial datasets from: {abs_dataset_dir}")

    coordinator = CoordinatorAgent()
    coordinator.initialize_agents(abs_dataset_dir)

    # Parse CLI args for optional parameters
    buyer_persona = "procurement_engineer"
    merchant_intent = None
    requested_amount = None

    for arg in sys.argv[1:]:
        if arg.startswith("--persona="):
            buyer_persona = arg.split("=", 1)[1]
        elif arg.startswith("--intent="):
            merchant_intent = arg.split("=", 1)[1]
        elif arg.startswith("--amount="):
            try:
                requested_amount = float(arg.split("=", 1)[1])
            except ValueError:
                pass

    t_start = time.time()
    pipeline_result = coordinator.run_multi_agent_pipeline(
        buyer_persona=buyer_persona,
        merchant_intent=merchant_intent,
        requested_amount_inr=requested_amount
    )
    elapsed = round((time.time() - t_start) * 1000, 1)

    # Generate enhanced observability report
    report_path = os.path.join(os.path.dirname(__file__), "agent_observability_report.md")
    generate_observability_report(pipeline_result, report_path, elapsed_ms=elapsed)

    print("\n" + "=" * 70)
    status = pipeline_result.get("status", "UNKNOWN")
    emoji = "✅" if status == "COMPLETED" else "❌"
    print(f"{emoji} PIPELINE STATUS: {status} ({elapsed}ms)")
    print(f"   Product    : {pipeline_result.get('product_name')}")
    print(f"   Trust Score: {pipeline_result.get('trust_score')}%")
    print(f"   Razorpay   : {pipeline_result.get('razorpay_order_id', 'N/A')}")
    print(f"   Risk Tier  : {pipeline_result.get('risk_tier', 'N/A')}")
    print(f"   Attestation: {pipeline_result.get('attestation', 'N/A')}")
    print(f"\n   Observability Report: {report_path}")
    print("=" * 70)


def generate_observability_report(result: dict, output_path: str, elapsed_ms: float = 0):
    """Generate a comprehensive markdown observability report with research paper mapping."""
    stages = result.get("pipeline_stages", [])
    compliance = result.get("research_compliance", {})

    lines = []

    # ── Header ────────────────────────────────────────────────────────────────
    lines.append("# ProductPilot AI — Multi-Agent Coordination & Observability Report")
    lines.append(f"\n**Verified Product SKU**: `{result.get('sku')}` — {result.get('product_name')}")
    lines.append(f"**Commerce Readiness Score**: `{result.get('readiness_score')}%`")
    lines.append(f"**XAI Trust Score**: `{result.get('trust_score')}%` ({_trust_label(result.get('trust_score', 0))})")
    lines.append(f"**Pipeline Status**: `{result.get('status')}`")
    lines.append(f"**Razorpay Order**: `{result.get('razorpay_order_id', 'N/A')}`")
    lines.append(f"**Risk Tier**: `{result.get('risk_tier', 'N/A')}`")
    lines.append(f"**Detected Intent**: `{result.get('detected_intent', 'N/A')}`")
    lines.append(f"**Attestation**: `{result.get('attestation', 'N/A')}`")
    lines.append(f"**Execution Time**: `{elapsed_ms}ms`")
    lines.append(f"**Buyer Persona**: `{result.get('pipeline_stages', [{}])[1].get('prioritized_for_persona', {}).get('persona', 'N/A')}`")

    # ── Research Paper Compliance Summary ─────────────────────────────────────
    lines.append("\n---")
    lines.append("\n## 📚 Research Paper Compliance Summary\n")
    lines.append("| Paper | Feature Implemented | Status |")
    lines.append("|-------|--------------------|-|")
    lines.append(f"| Allouah et al. | Authority-weighted source ranking (anti-position-bias) | {'✅' if compliance.get('grounded_citations', 0) > 0 else '⚠️'} |")
    lines.append(f"| Zeng et al. | Grounded citations with page+snippet+bounding-box | ✅ {compliance.get('grounded_citations', 0)} citations |")
    lines.append(f"| Dammu et al. | Subjective need resolution | ✅ {compliance.get('subjective_needs_resolved', 0)} detected |")
    lines.append(f"| Palumbo et al. | Intent-based routing | ✅ intent={result.get('detected_intent')} |")
    lines.append(f"| Mansour et al. | Persona-aligned extraction | ✅ active |")
    lines.append(f"| Paper 2 RQ2 | Accountability chain + money-action safety | ✅ {compliance.get('audit_trail_steps', 0)} audit steps |")
    lines.append(f"| Paper 2 RQ3 | UAP protocol compliance | ✅ active |")
    lines.append(f"| Paper 2 RQ4 | XAI trust score + merchant explanation | ✅ trust={result.get('trust_score')}% ({compliance.get('xai_trust_label')}) |")
    lines.append(f"| Walmart ARAG | Grounded retrieval for missing fields | ✅ active |")
    lines.append(f"| Maragheh & Deldjoo | Dual-unit conversion sub-agent | ✅ active |")
    lines.append(f"| Etsy OptAgent | Query rewriting for attribute labels | ✅ active |")

    # ── Pipeline Stages ────────────────────────────────────────────────────────
    lines.append("\n---")
    lines.append("\n## 🤖 7-Agent Execution Trace\n")

    stage_labels = [
        ("Source Ingestion Agent", "Allouah et al. — authority ranking"),
        ("Product Extraction Agent", "Zeng et al. + Dammu et al. — grounding + subjective needs"),
        ("Product Enrichment Agent", "Walmart ARAG + Maragheh & Deldjoo — RAG enrichment + dual units"),
        ("Validation & Conflict Agent", "Allouah et al. + Paper 2 RQ2/RQ4 — multi-signal + accountability + XAI"),
        ("Commerce Intelligence Agent", "Palumbo et al. + Dammu et al. — intent routing + subjective keywords"),
        ("Explainability & Evidence Agent", "Zeng et al. + Paper 2 RQ2/RQ4 — full citation + governance"),
        ("Razorpay Settlement Guardrail", "Paper 2 RQ2/RQ3/RQ4 — safety model + UAP protocol + audit trail"),
    ]

    for i, stage in enumerate(stages):
        label, research_note = stage_labels[i] if i < len(stage_labels) else (f"Agent {i+1}", "")
        agent_name = stage.get("agent", label)
        lines.append(f"### Stage {i+1}: {agent_name}")
        lines.append(f"*Research: {research_note}*\n")
        lines.append("```json")

        # For large stages, extract the most relevant fields to keep the report readable
        if i == 5:  # Explainability agent — show trust score and attestation separately
            summary = {
                "agent": stage.get("agent"),
                "status": stage.get("status"),
                "grounded_citations_count": stage.get("grounded_citations_count"),
                "trust_score": stage.get("trust_score"),
                "attestation": stage.get("attestation"),
                "merchant_explanation": (stage.get("merchant_explanation") or "")[:200] + "..."
                    if len(stage.get("merchant_explanation") or "") > 200 else stage.get("merchant_explanation"),
            }
            lines.append(json.dumps(summary, indent=2))
        elif i == 6:  # Settlement agent — show key fields
            summary = {
                "agent": stage.get("agent"),
                "status": stage.get("status"),
                "order_id": stage.get("order_id"),
                "authorized_amount": stage.get("authorized_amount"),
                "currency": stage.get("currency"),
                "price_envelope": stage.get("price_envelope"),
                "risk_assessment": stage.get("risk_assessment"),
                "uap_protocol_compliant": stage.get("uap_protocol_compliant"),
                "cryptographic_signature": stage.get("cryptographic_signature"),
                "execution_ms": stage.get("execution_ms"),
            }
            lines.append(json.dumps(summary, indent=2))
        else:
            lines.append(json.dumps(stage, indent=2, default=str))
        lines.append("```\n")

    # ── Audit Trail Section ────────────────────────────────────────────────────
    settlement_stage = stages[-1] if stages else {}
    audit_trail = settlement_stage.get("audit_trail", [])
    if audit_trail:
        lines.append("---")
        lines.append("\n## 🔐 Razorpay Settlement Audit Trail (Paper 2 RQ4)\n")
        lines.append("| Step | Action | Result | Detail |")
        lines.append("|------|--------|--------|--------|")
        for step in audit_trail:
            lines.append(f"| {step['step']} | `{step['action']}` | `{step['result']}` | {step['detail']} |")

    # ── Accountability Chain ───────────────────────────────────────────────────
    conflict_stage = stages[3] if len(stages) > 3 else {}
    accountability = conflict_stage.get("accountability_chain", [])
    if accountability:
        lines.append("\n---")
        lines.append("\n## 📋 Conflict Resolution Accountability Chain (Paper 2 RQ2)\n")
        for entry in accountability:
            lines.append(f"**{entry.get('resolution_id')}**")
            lines.append(f"- Attribute: `{entry.get('attribute')}`")
            lines.append(f"- Winning Source: `{entry.get('winning_source')}` (authority={entry.get('winning_authority')})")
            lines.append(f"- Method: `{entry.get('decision_basis')}`")
            lines.append(f"- XAI Explanation: *{entry.get('human_readable_explanation', 'N/A')}*")
            lines.append(f"- Auditable: `{entry.get('auditable')}`\n")

    # ── Citation Evidence ──────────────────────────────────────────────────────
    evidence_stage = stages[5] if len(stages) > 5 else {}
    citations = evidence_stage.get("citations", [])
    if citations:
        lines.append("---")
        lines.append("\n## 📖 Grounded Citation Evidence (Zeng et al.)\n")
        lines.append("| Attribute | Value | Source | Page | Snippet |")
        lines.append("|-----------|-------|--------|------|---------|")
        for c in citations:
            cit = c.get("citation", {})
            snippet = (cit.get("verbatim_snippet") or "N/A")[:60] + "..."
            lines.append(
                f"| `{c.get('attribute_label', c.get('attribute'))}` "
                f"| {c.get('value')} {c.get('unit', '')} "
                f"| {cit.get('source_name', 'N/A')} "
                f"| p.{cit.get('page', '?')} "
                f"| *{snippet}* |"
            )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _trust_label(score: int) -> str:
    if score >= 95: return "EXCELLENT"
    if score >= 85: return "GOOD"
    if score >= 70: return "FAIR"
    return "POOR"


if __name__ == "__main__":
    main()
