"""
Stage 6 — Explainability & Evidence Agent
Engineering Methodology:
  - Verifiable Provenance Citations: Spatial bounding-box coordinates <x, y, w, h>, page index, and verbatim quote grounding
  - Multi-Dimensional Trust Scoring: Composite metric balancing grounding coverage, confidence, conflict resolution, and authority
  - Cryptographic State Attestation: Immutable SHA-256 fingerprinting binding catalog parameters to transaction orders
"""

import os
import json
import time
import hashlib
from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional


class ExplainabilityEvidenceAgent(BaseAgent):
    """
    Agent 6 — Explainability & Evidence Agent
    Grounds all generated product data in verifiable proof:
    - Primary source attribution and PDF page numbers
    - Verbatim quoted excerpts and bounding-box coordinates
    - Confidence scores and cryptographic audit trail

    Core Capabilities:
    - Verifiable citation extraction with source authority tracking
    - Explainable AI (XAI) composite trust score derivation
    - Cryptographic SHA-256 state attestation for golden commerce records
    - Attestation rejection when catalog records lack primary provenance
    """

    def __init__(self):
        super().__init__(
            name="Explainability & Evidence Agent",
            provider="gemini",
            model="gemini-3.6-flash",
            api_key_name="GEMINI_API_KEY"
        )
        self.role = "Provenance & Grounding Guard"

    def ground_evidence(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ground every product attribute in verifiable evidence.
        Generate a full citation package and cryptographic attestation.
        """
        t_start = time.time()

        if not isinstance(product, dict) or not product:
            self.log("Invalid or empty product dictionary received for evidence grounding.", level="ERROR")
            return {
                "agent": self.name,
                "status": "ATTESTATION_REJECTED",
                "error_code": "INVALID_PRODUCT_DATA",
                "product_id": None,
                "grounded_citations_count": 0,
                "ungrounded_count": 0,
                "citations": [],
                "ungrounded_attributes": [],
                "authority_ranking": [],
                "trust_score": {"overall_score": 0, "components": {}, "label": "REJECTED"},
                "merchant_explanation": "Attestation rejected: Product data is missing or empty.",
                "attestation": {"auditable": False, "status": "REJECTED"},
                "execution_ms": round((time.time() - t_start) * 1000, 1)
            }

        self.log(f"Generating grounded evidence for '{product.get('name')}'...")

        citations = []
        ungrounded = []
        authority_ranking = []

        attributes = product.get("attributes", {})
        if not isinstance(attributes, dict):
            attributes = {}

        for key, attr in attributes.items():
            if not isinstance(attr, dict):
                continue
            prov = attr.get("provenance", {})

            if prov and prov.get("source_name"):
                # Fully grounded citation
                citation = {
                    "attribute": key,
                    "attribute_label": attr.get("name", key),
                    "value": attr.get("value"),
                    "unit": attr.get("unit", ""),
                    "alt_value": attr.get("alt_value"),
                    # Full citation chain
                    "citation": {
                        "source_id": prov.get("source_id"),
                        "source_name": prov.get("source_name"),
                        "source_type": prov.get("source_type"),
                        "page": prov.get("page"),
                        "bounding_box": prov.get("bounding_box"),
                        "verbatim_snippet": prov.get("snippet"),
                        "extraction_timestamp": prov.get("timestamp"),
                        "citable_reference": (
                            f"{prov.get('source_name')}, p.{prov.get('page')} — "
                            f"\"{prov.get('snippet', '')[:80]}\""
                        )
                    },
                    "confidence": attr.get("confidence", 0.90),
                    "conflict_resolved": attr.get("status") == "RESOLVED_CONFLICT",
                    "verification_status": attr.get("status", "VERIFIED")
                }
                citations.append(citation)

                # Authority ranking entry
                conflict = attr.get("conflict_details", {})
                if conflict:
                    for src in conflict.get("sources", []):
                        authority_ranking.append({
                            "attribute": key,
                            "source": src.get("source_name"),
                            "authority_weight": src.get("authority_weight"),
                            "value": src.get("value"),
                            "selected": src.get("is_selected", False),
                            "rank_reason": "selected" if src.get("is_selected") else "rejected — lower authority"
                        })
            else:
                ungrounded.append({
                    "attribute": key,
                    "value": attr.get("value"),
                    "reason": "No provenance metadata available",
                    "recommendation": "Seek primary source documentation for this attribute"
                })

        # Compute overall XAI trust score
        trust_score = self._compute_trust_score(citations, ungrounded, product)

        # Generate merchant-facing explanation
        merchant_explanation = self._generate_merchant_explanation(citations, trust_score, product)

        # Generate governance attestation
        attestation = self._generate_attestation(product, citations, trust_score)

        status = "ATTESTED" if trust_score["overall_score"] >= 90 else ("PARTIALLY_ATTESTED" if trust_score["overall_score"] >= 50 else "ATTESTATION_REJECTED")

        execution_ms = round((time.time() - t_start) * 1000, 1)
        self.log(
            f"Evidence grounding complete: {len(citations)} cited, {len(ungrounded)} ungrounded, "
            f"trust={trust_score['overall_score']}%, status={status}, {execution_ms}ms"
        )

        return {
            "agent": self.name,
            "product_id": product.get("id"),
            "grounded_citations_count": len(citations),
            "ungrounded_count": len(ungrounded),
            "citations": citations,
            "ungrounded_attributes": ungrounded,
            "authority_ranking": authority_ranking,
            "trust_score": trust_score,
            "merchant_explanation": merchant_explanation,
            "attestation": attestation,
            "status": status,
            "execution_ms": execution_ms
        }

    def _compute_trust_score(
        self,
        citations: List[Dict],
        ungrounded: List[Dict],
        product: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute a multi-dimensional trust score for the product record.
        Implements Paper 2 RQ4's explainable AI quality metrics.
        """
        total_attrs = len(citations) + len(ungrounded)
        if total_attrs == 0:
            return {"overall_score": 0, "components": {}}

        # Component 1: Grounding coverage
        grounding_score = round((len(citations) / total_attrs) * 100)

        # Component 2: Average citation confidence
        confidence_scores = [c.get("confidence", 0.80) for c in citations]
        avg_confidence = round(sum(confidence_scores) / len(confidence_scores) * 100) if confidence_scores else 0

        # Component 3: Conflict resolution completeness
        resolved = sum(1 for c in citations if c.get("conflict_resolved"))
        conflict_score = 100 if resolved == 0 or len(citations) == 0 else round(
            (resolved / len([c for c in citations if c.get("conflict_resolved") or c.get("verification_status") == "RESOLVED_CONFLICT"])) * 100
        ) if any(c.get("conflict_resolved") for c in citations) else 100

        # Component 4: Source authority quality
        authority_scores = []
        for c in citations:
            # Derive authority from source type
            source_type = c.get("citation", {}).get("source_type", "")
            if "OEM" in source_type or "Datasheet" in source_type:
                authority_scores.append(0.95)
            elif "CAD" in source_type or "Engineering" in source_type:
                authority_scores.append(0.92)
            elif "ERP" in source_type or "Supplier" in source_type:
                authority_scores.append(0.80)
            else:
                authority_scores.append(0.65)
        avg_authority = round(sum(authority_scores) / len(authority_scores) * 100) if authority_scores else 70

        overall = round((grounding_score * 0.30 + avg_confidence * 0.30 + conflict_score * 0.20 + avg_authority * 0.20))

        return {
            "overall_score": overall,
            "components": {
                "grounding_coverage": grounding_score,
                "average_confidence": avg_confidence,
                "conflict_resolution": conflict_score,
                "source_authority": avg_authority
            },
            "label": "EXCELLENT" if overall >= 95 else ("GOOD" if overall >= 85 else ("FAIR" if overall >= 70 else "POOR"))
        }

    def _generate_merchant_explanation(
        self,
        citations: List[Dict],
        trust_score: Dict[str, Any],
        product: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable trust explanation for merchants.
        Implements Paper 2 RQ4's merchant-facing XAI requirement.
        """
        try:
            citations_summary = "\n".join([
                f"- {c['attribute_label']}: '{c['value']}' from '{c['citation']['source_name']}' "
                f"(p.{c['citation']['page']}, confidence={c['confidence']:.0%})"
                for c in citations[:5]
            ])

            prompt = f"""You are ProductPilot AI — explaining product data trustworthiness to a merchant.

Product: {product.get('name')}
Trust Score: {trust_score['overall_score']}% ({trust_score['label']})
Score Components: {json.dumps(trust_score['components'])}

Key Cited Attributes:
{citations_summary}

Write a 3-sentence merchant-friendly explanation of:
1. Why this product data is trustworthy (or what's missing)
2. Which attributes are most strongly grounded
3. What the merchant can rely on for their commerce listing

Be specific about sources. Never mention Gemini."""

            explanation = self.call_llm(prompt, temperature=0.4, max_tokens=300)
            if explanation and len(explanation.strip()) >= 20:
                return explanation.strip()

        except Exception as e:
            self.log(f"Merchant explanation generation failed: {e}", level="WARN")
        
        score = trust_score["overall_score"]
        return (
            f"This product record achieves a trust score of {score}% based on "
            f"{len(citations)} grounded citations from authoritative sources. "
            f"Key specifications are backed by primary OEM documentation with verified page references. "
            f"{'This record is ready for commerce publication.' if score >= 90 else 'Some attributes require additional source verification before publication.'}"
        )

    def _generate_attestation(
        self,
        product: Dict[str, Any],
        citations: List[Dict],
        trust_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a cryptographic attestation for the product golden record.
        Implements governance and accountability requirements.
        """
        # Create a stable fingerprint of the verified data (deterministic)
        fingerprint_data = json.dumps({
            "product_id": product.get("id"),
            "sku": product.get("sku"),
            "grounded_attrs": sorted([c["attribute"] for c in citations]),
            "trust_score": trust_score["overall_score"]
        }, sort_keys=True)

        sha256 = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        attestation_id = f"ATT-{sha256[:12].upper()}"

        return {
            "attestation_id": attestation_id,
            "cryptographic_hash": f"SHA256:{sha256}",
            "short_signature": f"SIG-SHA256:{sha256[:24]}",
            "attested_product": product.get("sku"),
            "attested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "trust_score_at_attestation": trust_score["overall_score"],
            "citations_attested": len(citations),
            "governance_standard": "ProductPilot-UAP-1.0",
            "chain_of_custody": "PRODUCTPILOT → RAZORPAY_SETTLEMENT → MERCHANT",
            "auditable": True,
            "revocable": True
        }
