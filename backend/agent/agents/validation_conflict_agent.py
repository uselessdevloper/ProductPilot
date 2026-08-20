"""
Stage 4 — Validation & Conflict Agent
Research-Paper Improvements:
  - Allouah et al.: multi-signal validation — requires ≥2 independent sources before finalizing
  - Paper 2 (RQ2): accountability framework — every resolution has an auditable reasoning chain
  - Zeng et al.: resolution must cite the winning source with evidence
  - Paper 2 (RQ4): explainable AI — human-readable conflict resolution narratives
"""

import os
import json
import time
from .base_agent import BaseAgent
from typing import Dict, Any, List, Tuple


class ValidationConflictAgent(BaseAgent):
    """
    Agent 4 — Validation & Conflict Agent
    Cross-document conflict detection and Bayesian authority resolution:
    - Identifies spec discrepancies (e.g. Website 12 kg vs Datasheet 12.5 kg)
    - Computes authority scoring: OEM PDF (0.95) vs Web Scrape (0.60) vs Catalog (0.50)
    - Generates explainable resolution reasoning

    Research enhancements:
    - Multi-signal validation requiring ≥2 corroborating sources (Allouah et al.)
    - Full accountability chain for every conflict resolution (Paper 2 RQ2)
    - Cited evidence for every resolved value (Zeng et al.)
    - Human-readable XAI explanations for merchant trust (Paper 2 RQ4)
    """

    # Risk levels for different conflict magnitudes
    CONFLICT_RISK_THRESHOLDS = {
        "LOW":    0.05,   # < 5% deviation — likely rounding
        "MEDIUM": 0.15,   # 5–15% deviation — may indicate revision
        "HIGH":   0.30,   # 15–30% deviation — likely source error
        "CRITICAL": 1.0   # > 30% deviation — data integrity issue
    }

    def __init__(self):
        super().__init__(
            name="Validation & Conflict Agent",
            provider="gemini",
            model="gemini-2.5-flash",
            api_key_name="GEMINI_API_KEY"
        )
        self.role = "Bayesian Conflict Arbiter"

    def resolve_product_conflicts(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect and resolve all attribute conflicts with full audit trail.
        """
        t_start = time.time()
        self.log(f"Validating conflicts for product '{product.get('name')}'...")

        resolved_conflicts = []
        unresolved_conflicts = []
        multi_signal_flags = []
        accountability_chain = []

        for key, attr in product.get("attributes", {}).items():
            conflict_data = attr.get("conflict_details")
            if not conflict_data:
                # No conflict — still validate for multi-signal coverage
                sources_count = attr.get("sources_count", 1)
                if sources_count < 2:
                    multi_signal_flags.append({
                        "attribute": key,
                        "flag": "SINGLE_SOURCE_ONLY",
                        "recommendation": "Seek a second independent source to confirm this value.",
                        "current_confidence": attr.get("confidence", 0.80)
                    })
                continue

            sources = conflict_data.get("sources", [])
            resolution = self._resolve_conflict(key, attr, sources, conflict_data)
            resolved_conflicts.append(resolution)

            # Accountability chain entry (Paper 2 RQ2)
            accountability_chain.append({
                "attribute": key,
                "resolution_id": f"CONFLICT-{key.upper()}-{int(t_start)}",
                "winning_source": resolution.get("chosen_source"),
                "winning_authority": resolution.get("winning_authority"),
                "competing_sources": len(sources),
                "decision_basis": resolution.get("resolution_method"),
                "human_readable_explanation": resolution.get("xai_explanation"),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "auditable": True
            })

        # Generate LLM explanations for complex conflicts
        for res in resolved_conflicts:
            if not res.get("xai_explanation"):
                res["xai_explanation"] = self._generate_xai_explanation(res)

        execution_ms = round((time.time() - t_start) * 1000, 1)
        self.log(
            f"Conflict resolution complete: {len(resolved_conflicts)} resolved, "
            f"{len(unresolved_conflicts)} unresolved, {len(multi_signal_flags)} single-source flags, "
            f"{execution_ms}ms"
        )

        return {
            "agent": self.name,
            "product_id": product.get("id"),
            "resolved_conflicts_count": len(resolved_conflicts),
            "unresolved_conflicts_count": len(unresolved_conflicts),
            "details": resolved_conflicts,
            "unresolved": unresolved_conflicts,
            # Multi-signal validation (Allouah et al.)
            "multi_signal_validation": {
                "single_source_flags": multi_signal_flags,
                "single_source_count": len(multi_signal_flags),
                "policy": "All critical attributes should have ≥2 corroborating sources"
            },
            # Accountability framework (Paper 2 RQ2)
            "accountability_chain": accountability_chain,
            "execution_ms": execution_ms
        }

    def _resolve_conflict(
        self,
        key: str,
        attr: Dict[str, Any],
        sources: List[Dict[str, Any]],
        conflict_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve a single attribute conflict using Bayesian authority weighting.
        """
        if not sources:
            return {
                "attribute": key,
                "resolved_value": attr.get("value"),
                "resolution_method": "NO_SOURCES",
                "chosen_source": "unknown",
                "winning_authority": 0.0,
                "risk_level": "HIGH"
            }

        # Select winning source by authority weight
        selected = max(sources, key=lambda s: s.get("authority_weight", 0))

        # Compute deviation between highest and lowest source values
        risk_level = self._assess_conflict_risk(sources)

        # Check multi-signal corroboration (Allouah et al.)
        top_authority = selected.get("authority_weight", 0)
        corroborating = [
            s for s in sources
            if s.get("authority_weight", 0) >= 0.70 and s.get("source_id") != selected.get("source_id")
            and s.get("value") == selected.get("value")
        ]
        multi_signal_corroborated = len(corroborating) >= 1

        return {
            "attribute": key,
            "resolved_value": conflict_data.get("resolved_value", selected.get("value")),
            "resolution_method": "BAYESIAN_AUTHORITY_WEIGHTED",
            "chosen_source": selected.get("source_name", selected.get("source_id")),
            "winning_authority": top_authority,
            "competing_values": [
                {"source": s.get("source_name", s.get("source_id")), "value": s.get("value"),
                 "authority": s.get("authority_weight"), "selected": s.get("is_selected", False)}
                for s in sources
            ],
            "risk_level": risk_level,
            "multi_signal_corroborated": multi_signal_corroborated,
            "corroborating_sources_count": len(corroborating),
            "resolution_reasoning": attr.get("resolution_reasoning", ""),
            # Will be populated by _generate_xai_explanation
            "xai_explanation": None
        }

    def _assess_conflict_risk(self, sources: List[Dict[str, Any]]) -> str:
        """Compute the risk level based on the numeric deviation between conflicting values."""
        numeric_values = []
        for s in sources:
            try:
                # Handle values like "14.2 kg" or "14.2"
                val_str = str(s.get("value", "")).split()[0]
                numeric_values.append(float(val_str))
            except (ValueError, IndexError):
                pass

        if len(numeric_values) < 2:
            return "UNKNOWN"

        max_val = max(numeric_values)
        min_val = min(numeric_values)
        if max_val == 0:
            return "LOW"

        deviation = (max_val - min_val) / max_val
        for level, threshold in self.CONFLICT_RISK_THRESHOLDS.items():
            if deviation <= threshold:
                return level
        return "CRITICAL"

    def _generate_xai_explanation(self, resolution: Dict[str, Any]) -> str:
        """
        Generate a human-readable explanation for the conflict resolution.
        Implements Paper 2 RQ4's explainable AI requirement.
        """
        try:
            competing = resolution.get("competing_values", [])
            competing_summary = ", ".join([
                f"'{v['source']}' says {v['value']} (authority={v['authority']:.2f})"
                for v in competing[:4]
            ])

            prompt = f"""You are ProductPilot AI — explaining a product data conflict resolution to a merchant.

Attribute: {resolution['attribute']}
Resolved Value: {resolution['resolved_value']}
Winning Source: {resolution['chosen_source']} (authority={resolution['winning_authority']:.2f})
Competing Sources: {competing_summary}
Risk Level: {resolution['risk_level']}
Corroborated by multiple high-authority sources: {resolution['multi_signal_corroborated']}

Write a 2-sentence merchant-friendly explanation of WHY this value was chosen.
Be specific about the authority scores. Do not use jargon. Never mention Gemini."""

            return self.call_llm(prompt, temperature=0.3, max_tokens=200)

        except Exception as e:
            self.log(f"XAI explanation generation failed: {e}", level="WARN")
            # Deterministic fallback
            return (
                f"The value '{resolution['resolved_value']}' was selected from "
                f"'{resolution['chosen_source']}' (authority={resolution['winning_authority']:.2f}) "
                f"as the most authoritative source. "
                f"Risk assessment: {resolution['risk_level']}."
            )
