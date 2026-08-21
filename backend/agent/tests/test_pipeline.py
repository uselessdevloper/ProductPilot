"""
ProductPilot AI — End-to-End Test Suite
Tests every stage of the 7-agent pipeline plus research-paper-driven capabilities.

Run:  python -m pytest backend/agent/tests/test_pipeline.py -v
  or: python backend/agent/tests/test_pipeline.py   (standalone)
"""

import sys
import os
import json
import time
import hashlib
import unittest

# Allow importing agents from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.source_ingestion_agent import SourceIngestionAgent
from agents.product_extraction_agent import ProductExtractionAgent
from agents.product_enrichment_agent import ProductEnrichmentAgent
from agents.validation_conflict_agent import ValidationConflictAgent
from agents.commerce_intelligence_agent import CommerceIntelligenceAgent
from agents.explainability_evidence_agent import ExplainabilityEvidenceAgent
from agents.razorpay_settlement_agent import RazorpaySettlementAgent
from agents.coordinator_agent import CoordinatorAgent

# ─── Shared Test Fixtures ────────────────────────────────────────────────────

SAMPLE_SOURCES = [
    {
        "id": "oem_datasheets",
        "name": "OEM Technical Datasheets (PDF)",
        "type": "Technical Datasheet (PDF)",
        "authority_weight": 0.98,
        "items": [{"id": "SRC-OEM-01", "title": "ApexFlow X200 Datasheet"}]
    },
    {
        "id": "distributor_catalogs",
        "name": "Distributor Web Catalogs",
        "type": "Distributor Listing (HTML)",
        "authority_weight": 0.65,
        "items": [{"id": "SRC-DIST-01", "title": "Grainger Catalog"}]
    },
    {
        "id": "cad_drawings",
        "name": "3D CAD & Engineering Prints",
        "type": "Engineering CAD Model",
        "authority_weight": 0.94,
        "items": []
    }
]

SAMPLE_PRODUCT = {
    "id": "PROD-TEST-001",
    "sku": "APE-PUMP-TEST-001",
    "mpn": "X200-TEST",
    "name": "Industrial Pump X200 (ApexFlow Heavy-Duty Centrifugal Pump, SS304, 240V, 350 L/min)",
    "brand": "ApexFlow Industrial",
    "category": "Pumps & Fluid Handling",
    "subCategory": "Centrifugal Process Pumps",
    "price_inr": 68500,
    "description": "High-efficiency corrosion resistant centrifugal pump for chemical processing. Heavy duty stainless steel construction.",
    "taxonomies": {
        "unspsc": "40151503",
        "etim_class": "EC011492",
        "etim_version": "8.0",
        "eclass": "27-18-07-01"
    },
    "attributes": {
        "weight": {
            "name": "Net Weight",
            "value": "12.5",
            "unit": "kg",
            "status": "RESOLVED_CONFLICT",
            "confidence": 0.96,
            "sources_count": 3,
            "conflicts_count": 1,
            "resolution_reasoning": "OEM datasheet value selected over website listing.",
            "provenance": {
                "source_id": "SRC-OEM-PDF",
                "source_name": "ApexFlow X200 Technical Engineering Datasheet (50-Page PDF)",
                "source_type": "Technical Datasheet (PDF)",
                "page": 4,
                "bounding_box": [115, 230, 310, 255],
                "snippet": "Net dry operating weight: 12.5 kg (including standard mounting base)",
                "timestamp": "2026-06-18T10:00:00Z"
            },
            "conflict_details": {
                "attribute_key": "weight",
                "resolved_value": "12.5 kg",
                "sources": [
                    {
                        "source_id": "SRC-OEM-PDF",
                        "source_name": "Technical Datasheet (50-Page PDF)",
                        "source_type": "OEM Engineering Spec",
                        "authority_weight": 0.95,
                        "value": "12.5 kg",
                        "page": 4,
                        "is_selected": True
                    },
                    {
                        "source_id": "SRC-WEB",
                        "source_name": "Product Webpage",
                        "source_type": "Distributor Listing (HTML)",
                        "authority_weight": 0.6,
                        "value": "12.0 kg",
                        "page": 1,
                        "is_selected": False
                    }
                ]
            }
        },
        "material": {
            "name": "Wetted Body Material",
            "value": "Stainless Steel (SS304 / 1.4301)",
            "unit": "Grade SS304",
            "status": "VERIFIED",
            "confidence": 0.98,
            "sources_count": 2,
            "conflicts_count": 0,
            "provenance": {
                "source_id": "SRC-OEM-PDF",
                "source_name": "ApexFlow X200 Technical Engineering Datasheet",
                "source_type": "Technical Datasheet (PDF)",
                "page": 4,
                "snippet": "Pump casing material: AISI 304 Stainless Steel (SS304 / 1.4301)"
            }
        },
        "voltage": {
            "name": "Operating Voltage",
            "value": "240",
            "unit": "V AC",
            "status": "VERIFIED",
            "confidence": 0.99,
            "sources_count": 2,
            "conflicts_count": 0,
            "provenance": {
                "source_id": "SRC-OEM-PDF",
                "source_name": "ApexFlow X200 Technical Engineering Datasheet",
                "source_type": "Technical Datasheet (PDF)",
                "page": 5,
                "snippet": "Supply voltage: 240 V AC ±10%"
            }
        },
        "max_flow_rate": {
            "name": "Max Flow Rate",
            "value": "350",
            "unit": "L/min",
            "status": "VERIFIED",
            "confidence": 0.97,
            "sources_count": 3,
            "conflicts_count": 0,
            "provenance": {
                "source_id": "SRC-OEM-PDF",
                "source_name": "ApexFlow X200 Technical Engineering Datasheet",
                "source_type": "Technical Datasheet (PDF)",
                "page": 6,
                "snippet": "Peak volumetric flow rate Qmax = 350 L/min"
            }
        }
    },
    "syndication_channels": {
        "sap_commerce": {"status": "READY", "readiness_score": 100},
        "shopify_b2b": {"status": "READY", "readiness_score": 100},
        "akeneo_pim": {"status": "READY", "readiness_score": 98}
    }
}


def load_catalog_if_available():
    """Try to load the real dataset; fall back to SAMPLE_PRODUCT."""
    dataset_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "productpilotai", "datasets")
    )
    cat_path = os.path.join(dataset_dir, "industrial_catalog.json")
    src_path = os.path.join(dataset_dir, "industrial_sources.json")

    catalog = [SAMPLE_PRODUCT]
    sources = SAMPLE_SOURCES

    if os.path.exists(cat_path):
        with open(cat_path, "r") as f:
            catalog = json.load(f)
    if os.path.exists(src_path):
        with open(src_path, "r") as f:
            sources = json.load(f)

    return catalog, sources, dataset_dir


# ─── Stage 1: Source Ingestion Tests ─────────────────────────────────────────

class TestSourceIngestionAgent(unittest.TestCase):

    def setUp(self):
        self.agent = SourceIngestionAgent()

    def test_basic_ingestion_returns_correct_keys(self):
        result = self.agent.process_sources(SAMPLE_SOURCES)
        self.assertEqual(result["agent"], "Source Ingestion Agent")
        self.assertEqual(result["status"], "COMPLETED")
        self.assertIn("ingested_sources", result)
        self.assertIn("protocol_compliance", result)

    def test_sources_sorted_by_authority_descending(self):
        """Allouah et al. — sources must be ranked highest authority first (anti-position-bias)."""
        result = self.agent.process_sources(SAMPLE_SOURCES)
        sources = result["ingested_sources"]
        authorities = [s["authority_weight"] for s in sources]
        self.assertEqual(authorities, sorted(authorities, reverse=True),
                         "Sources should be sorted by authority DESC (Allouah et al.)")

    def test_citation_metadata_present(self):
        """Zeng et al. — every ingested source must have citation metadata."""
        result = self.agent.process_sources(SAMPLE_SOURCES)
        for source in result["ingested_sources"]:
            self.assertIn("citation_metadata", source,
                          f"Source '{source['name']}' missing citation_metadata (Zeng et al.)")
            self.assertIn("citable_reference", source["citation_metadata"])

    def test_conflict_risk_detection(self):
        """Allouah et al. — large authority gaps between sources should be flagged."""
        result = self.agent.process_sources(SAMPLE_SOURCES)
        # OEM (0.98) vs Distributor (0.65) = 0.33 delta > 0.20 threshold
        self.assertGreater(len(result["conflict_risk_pairs"]), 0,
                           "Should detect conflict risks between high/low authority sources")

    def test_uap_protocol_compliance(self):
        """Paper 2 RQ3 — ingestion manifest must be protocol-compliant."""
        result = self.agent.process_sources(SAMPLE_SOURCES)
        pc = result["protocol_compliance"]
        self.assertTrue(pc["sources_ranked_by_authority"])
        self.assertTrue(pc["ready_for_extraction"])

    def test_empty_sources_handled_gracefully(self):
        result = self.agent.process_sources([])
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(result["ingested_sources"], [])


# ─── Stage 2: Product Extraction Tests ───────────────────────────────────────

class TestProductExtractionAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ProductExtractionAgent()

    def test_extraction_returns_all_attributes(self):
        result = self.agent.extract_product_entities(SAMPLE_PRODUCT)
        self.assertIn("extracted_attributes", result)
        self.assertGreater(len(result["extracted_attributes"]), 0)

    def test_subjective_need_detection(self):
        """Dammu et al. — subjective needs in description should be detected and mapped."""
        result = self.agent.extract_product_entities(SAMPLE_PRODUCT)
        sn = result.get("subjective_need_resolution", {})
        # Description contains "corrosion resistant" and "chemical processing"
        self.assertGreater(sn.get("detected_subjective_needs", 0), 0,
                           "Should detect 'corrosion resistant' / 'chemical processing' subjective needs (Dammu et al.)")

    def test_buyer_persona_prioritization(self):
        """Mansour et al. — different personas should prioritize different attributes."""
        result_procurement = self.agent.extract_product_entities(
            SAMPLE_PRODUCT, buyer_persona="procurement_engineer"
        )
        result_tech = self.agent.extract_product_entities(
            SAMPLE_PRODUCT, buyer_persona="maintenance_technician"
        )
        p_attrs = result_procurement["prioritized_for_persona"]["priority_attributes"]
        t_attrs = result_tech["prioritized_for_persona"]["priority_attributes"]
        # Different personas should care about different things
        self.assertNotEqual(sorted(p_attrs), sorted(t_attrs),
                            "Different buyer personas should yield different priority attributes (Mansour et al.)")

    def test_confidence_score_within_range(self):
        result = self.agent.extract_product_entities(SAMPLE_PRODUCT)
        score = result.get("confidence_score", 0)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_sku_and_mpn_preserved(self):
        result = self.agent.extract_product_entities(SAMPLE_PRODUCT)
        self.assertEqual(result.get("sku"), SAMPLE_PRODUCT["sku"])
        self.assertEqual(result.get("mpn"), SAMPLE_PRODUCT["mpn"])


# ─── Stage 3: Product Enrichment Tests ───────────────────────────────────────

class TestProductEnrichmentAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ProductEnrichmentAgent()

    def test_enrichment_returns_taxonomy(self):
        result = self.agent.enrich(SAMPLE_PRODUCT)
        self.assertIn("taxonomies", result)
        taxonomies = result["taxonomies"]
        self.assertIn("unspsc", taxonomies)
        self.assertIn("etim_class", taxonomies)

    def test_dual_unit_conversion_kg_to_lbs(self):
        """Maragheh & Deldjoo — metric attributes must have imperial alt_values."""
        result = self.agent.enrich(SAMPLE_PRODUCT)
        enriched = result.get("enriched_attributes", {})
        weight_attr = enriched.get("weight", {})
        self.assertIn("alt_value", weight_attr,
                      "Weight attribute should have imperial alt_value (Maragheh & Deldjoo)")
        self.assertIn("lbs", weight_attr.get("alt_value", "").lower(),
                      "Weight alt_value should be in lbs")

    def test_dual_unit_conversion_lmin_to_gpm(self):
        """Maragheh & Deldjoo — flow rates should be converted to GPM."""
        result = self.agent.enrich(SAMPLE_PRODUCT)
        enriched = result.get("enriched_attributes", {})
        flow_attr = enriched.get("max_flow_rate", {})
        if flow_attr:  # Only test if attribute exists
            alt = flow_attr.get("alt_value", "")
            self.assertIn("GPM", alt.upper() if alt else "",
                          "Flow rate should have GPM alt_value (Maragheh & Deldjoo)")

    def test_label_rewriting(self):
        """Etsy OptAgent — attribute labels should be standardized."""
        result = self.agent.enrich(SAMPLE_PRODUCT)
        rewritten = result.get("rewritten_labels", {})
        self.assertGreater(len(rewritten), 0, "Should produce rewritten canonical labels")
        # "weight" should be rewritten to "Net Weight"
        self.assertEqual(rewritten.get("weight"), "Net Weight")

    def test_completeness_score_in_range(self):
        result = self.agent.enrich(SAMPLE_PRODUCT)
        score = result.get("completeness_score", 0)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_enrichment_on_minimal_product(self):
        """Walmart ARAG — agent should handle products with minimal data gracefully."""
        minimal = {"id": "MIN-001", "sku": "MIN-001", "name": "Hydraulic Pump", "attributes": {}}
        result = self.agent.enrich(minimal)
        self.assertIn("taxonomies", result)
        # Should assign UNSPSC for "pump"
        self.assertIsNotNone(result["taxonomies"].get("unspsc"))


# ─── Stage 4: Validation & Conflict Tests ────────────────────────────────────

class TestValidationConflictAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ValidationConflictAgent()

    def test_conflict_detection_and_resolution(self):
        result = self.agent.resolve_product_conflicts(SAMPLE_PRODUCT)
        self.assertEqual(result["agent"], "Validation & Conflict Agent")
        self.assertGreater(result["resolved_conflicts_count"], 0,
                           "Should resolve the weight conflict in SAMPLE_PRODUCT")

    def test_accountability_chain_generated(self):
        """Paper 2 RQ2 — every conflict must have an accountability chain entry."""
        result = self.agent.resolve_product_conflicts(SAMPLE_PRODUCT)
        chain = result.get("accountability_chain", [])
        self.assertGreater(len(chain), 0,
                           "Accountability chain must be populated (Paper 2 RQ2)")
        for entry in chain:
            self.assertIn("resolution_id", entry)
            self.assertIn("winning_source", entry)
            self.assertTrue(entry.get("auditable"),
                            "All chain entries must be auditable")

    def test_multi_signal_validation(self):
        """Allouah et al. — attributes with only one source should be flagged."""
        result = self.agent.resolve_product_conflicts(SAMPLE_PRODUCT)
        mv = result.get("multi_signal_validation", {})
        self.assertIn("single_source_flags", mv)
        self.assertIn("policy", mv)

    def test_conflict_risk_assessment(self):
        """Conflict risk should be classified as LOW/MEDIUM/HIGH/CRITICAL."""
        result = self.agent.resolve_product_conflicts(SAMPLE_PRODUCT)
        for conflict in result["details"]:
            self.assertIn(conflict["risk_level"], ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"],
                          f"Risk level '{conflict['risk_level']}' is not a valid tier")

    def test_xai_explanation_present(self):
        """Paper 2 RQ4 — every resolved conflict must have a human-readable explanation."""
        result = self.agent.resolve_product_conflicts(SAMPLE_PRODUCT)
        for conflict in result["details"]:
            self.assertIsNotNone(conflict.get("xai_explanation"),
                                 f"Conflict for '{conflict['attribute']}' missing XAI explanation (Paper 2 RQ4)")

    def test_bayesian_winner_is_highest_authority(self):
        """The winning source must always be the one with the highest authority weight."""
        result = self.agent.resolve_product_conflicts(SAMPLE_PRODUCT)
        for conflict in result["details"]:
            competing = conflict.get("competing_values", [])
            if competing:
                winner_authority = conflict.get("winning_authority", 0)
                all_authorities = [c["authority"] for c in competing if c.get("authority")]
                self.assertEqual(
                    winner_authority, max(all_authorities),
                    f"Winning source for '{conflict['attribute']}' is not highest authority (Allouah et al.)"
                )


# ─── Stage 5: Commerce Intelligence Tests ────────────────────────────────────

class TestCommerceIntelligenceAgent(unittest.TestCase):

    def setUp(self):
        self.agent = CommerceIntelligenceAgent()

    def test_commerce_profile_generation(self):
        result = self.agent.generate_commerce_profile(SAMPLE_PRODUCT)
        self.assertEqual(result["agent"], "Commerce Intelligence Agent")
        self.assertIn("b2b_title", result)
        self.assertIn("description", result)
        self.assertIn("channels", result)

    def test_intent_detection_catalog_publish(self):
        """Palumbo et al. — default intent should be catalog_publish."""
        result = self.agent.generate_commerce_profile(SAMPLE_PRODUCT)
        self.assertIn("detected_intent", result)
        self.assertIsNotNone(result["detected_intent"])

    def test_intent_detection_price_negotiation(self):
        """Palumbo et al. — price-related queries should route to price_negotiation."""
        product_with_price_context = dict(SAMPLE_PRODUCT)
        product_with_price_context["description"] = "Request INR quote for this product"
        result = self.agent.generate_commerce_profile(product_with_price_context)
        self.assertEqual(result["detected_intent"], "price_negotiation",
                         "Price-related description should trigger price_negotiation intent (Palumbo et al.)")

    def test_intent_routing_populated(self):
        """Palumbo et al. — intent routing must specify next_action and agents_to_invoke."""
        result = self.agent.generate_commerce_profile(SAMPLE_PRODUCT)
        routing = result.get("intent_routing", {})
        self.assertIn("next_action", routing)
        self.assertIn("agents_to_invoke", routing)
        self.assertIsInstance(routing["agents_to_invoke"], list)

    def test_subjective_keywords_generated(self):
        """Dammu et al. — subjective terms should produce SEO keywords."""
        result = self.agent.generate_commerce_profile(SAMPLE_PRODUCT)
        keywords = result.get("subjective_commerce_keywords", [])
        self.assertGreater(len(keywords), 0,
                           "Should generate SEO keywords from subjective product needs (Dammu et al.)")

    def test_channel_readiness_structure(self):
        """Paper 2 RQ3 — each channel should have status and readiness_score."""
        result = self.agent.generate_commerce_profile(SAMPLE_PRODUCT)
        for channel_name, channel_data in result["channels"].items():
            self.assertIn("status", channel_data, f"Channel '{channel_name}' missing status")
            self.assertIn("readiness_score", channel_data, f"Channel '{channel_name}' missing readiness_score")
            self.assertIn(channel_data["status"], ["READY", "PARTIAL", "NOT_READY"])

    def test_razorpay_ready_data(self):
        result = self.agent.generate_commerce_profile(SAMPLE_PRODUCT)
        rzp = result.get("razorpay_ready", {})
        self.assertTrue(rzp.get("ready"), "Product should be Razorpay-ready")
        self.assertEqual(rzp.get("currency"), "INR")


# ─── Stage 6: Explainability & Evidence Tests ────────────────────────────────

class TestExplainabilityEvidenceAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ExplainabilityEvidenceAgent()

    def test_grounding_returns_citations(self):
        result = self.agent.ground_evidence(SAMPLE_PRODUCT)
        self.assertEqual(result["agent"], "Explainability & Evidence Agent")
        self.assertGreater(result["grounded_citations_count"], 0)

    def test_citation_has_all_required_fields(self):
        """Zeng et al. — every citation must have source, page, snippet, bounding_box."""
        result = self.agent.ground_evidence(SAMPLE_PRODUCT)
        for citation in result["citations"]:
            cit = citation.get("citation", {})
            self.assertIsNotNone(cit.get("source_name"),
                                 f"Citation for '{citation['attribute']}' missing source_name (Zeng et al.)")
            self.assertIsNotNone(cit.get("page"),
                                 f"Citation for '{citation['attribute']}' missing page number (Zeng et al.)")
            self.assertIsNotNone(cit.get("verbatim_snippet"),
                                 f"Citation for '{citation['attribute']}' missing verbatim_snippet (Zeng et al.)")
            self.assertIsNotNone(cit.get("citable_reference"),
                                 f"Citation for '{citation['attribute']}' missing citable_reference (Zeng et al.)")

    def test_trust_score_computed(self):
        """Paper 2 RQ4 — trust score must be computed with component breakdown."""
        result = self.agent.ground_evidence(SAMPLE_PRODUCT)
        ts = result.get("trust_score", {})
        self.assertIn("overall_score", ts)
        self.assertIn("components", ts)
        self.assertIn("label", ts)
        self.assertGreater(ts["overall_score"], 0)
        self.assertIn(ts["label"], ["EXCELLENT", "GOOD", "FAIR", "POOR"])

    def test_attestation_generated(self):
        """Paper 2 RQ2 — cryptographic attestation must be present with SHA-256."""
        result = self.agent.ground_evidence(SAMPLE_PRODUCT)
        attestation = result.get("attestation", {})
        self.assertIn("cryptographic_hash", attestation)
        self.assertTrue(attestation["cryptographic_hash"].startswith("SHA256:"),
                        "Attestation must use SHA-256 (Paper 2 RQ2)")
        self.assertTrue(attestation.get("auditable"))

    def test_attestation_is_deterministic(self):
        """Same product data should always produce the same attestation hash."""
        result1 = self.agent.ground_evidence(SAMPLE_PRODUCT)
        result2 = self.agent.ground_evidence(SAMPLE_PRODUCT)
        # IDs are based on product content — should be stable
        self.assertEqual(
            result1["attestation"]["attestation_id"][:6],
            result2["attestation"]["attestation_id"][:6],
            "Attestation should be deterministic for the same product data"
        )

    def test_authority_ranking_populated(self):
        """Allouah et al. — authority ranking should expose how sources influenced decisions."""
        result = self.agent.ground_evidence(SAMPLE_PRODUCT)
        ranking = result.get("authority_ranking", [])
        self.assertGreater(len(ranking), 0,
                           "Authority ranking must be populated (Allouah et al.)")
        # Ensure selected vs rejected are both present
        selected = [r for r in ranking if r.get("selected")]
        rejected = [r for r in ranking if not r.get("selected")]
        self.assertGreater(len(selected), 0, "At least one selected source in ranking")
        self.assertGreater(len(rejected), 0, "At least one rejected source in ranking")

    def test_merchant_explanation_present(self):
        """Paper 2 RQ4 — merchant-facing explanation must be present."""
        result = self.agent.ground_evidence(SAMPLE_PRODUCT)
        explanation = result.get("merchant_explanation", "")
        self.assertIsInstance(explanation, str)
        self.assertGreater(len(explanation), 20,
                           "Merchant explanation should be a non-trivial string (Paper 2 RQ4)")


# ─── Stage 7: Razorpay Settlement Tests ──────────────────────────────────────

class TestRazorpaySettlementAgent(unittest.TestCase):

    def setUp(self):
        self.agent = RazorpaySettlementAgent()

    def test_bounded_order_creation(self):
        """Nominal price — should be BOUNDED_VERIFIED."""
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 68500.0)
        self.assertEqual(result["status"], "BOUNDED_VERIFIED")
        self.assertIsNotNone(result.get("order_id"))
        self.assertTrue(result["order_id"].startswith("order_RZP_"))

    def test_price_below_minimum_blocked(self):
        """90% lower bound — below floor should trigger GUARDRAIL_VIOLATION."""
        below_floor = SAMPLE_PRODUCT["price_inr"] * 0.85  # 15% below nominal
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, below_floor)
        self.assertEqual(result["status"], "GUARDRAIL_VIOLATION",
                         "Price below 90% floor must be blocked (Allouah et al.)")

    def test_price_above_maximum_blocked(self):
        """115% upper bound — above ceiling should trigger GUARDRAIL_VIOLATION."""
        above_ceiling = SAMPLE_PRODUCT["price_inr"] * 1.20  # 20% above nominal
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, above_ceiling)
        self.assertEqual(result["status"], "GUARDRAIL_VIOLATION",
                         "Price above 115% ceiling must be blocked (Allouah et al.)")

    def test_price_at_boundary_accepted(self):
        """Exactly at the 90% floor should be accepted."""
        at_floor = SAMPLE_PRODUCT["price_inr"] * 0.90
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, at_floor)
        self.assertEqual(result["status"], "BOUNDED_VERIFIED",
                         "Price exactly at 90% floor should be accepted")

    def test_risk_tier_low_for_small_amount(self):
        """Paper 2 RQ2 — small amounts should be LOW risk, auto-approved."""
        small_product = dict(SAMPLE_PRODUCT)
        small_product["price_inr"] = 800
        result = self.agent.validate_and_create_order(small_product, 800.0)
        if result["status"] == "BOUNDED_VERIFIED":
            risk = result["risk_assessment"]
            self.assertEqual(risk["tier"], "LOW")
            self.assertFalse(risk["human_approval_required"])

    def test_risk_tier_high_for_large_amount(self):
        """Paper 2 RQ2 — large amounts should require human approval."""
        large_product = dict(SAMPLE_PRODUCT)
        large_product["price_inr"] = 3_00_000
        result = self.agent.validate_and_create_order(large_product, 3_00_000.0)
        if result["status"] == "BOUNDED_VERIFIED":
            risk = result["risk_assessment"]
            self.assertIn(risk["tier"], ["HIGH", "CRITICAL"])
            self.assertTrue(risk["human_approval_required"])

    def test_audit_trail_all_steps_present(self):
        """Paper 2 RQ4 — audit trail must have all 5 required steps."""
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 68500.0)
        trail = result.get("audit_trail", [])
        self.assertEqual(len(trail), 5,
                         "Audit trail must have exactly 5 steps (Paper 2 RQ4)")
        actions = [step["action"] for step in trail]
        self.assertIn("IDEMPOTENCY_CHECK", actions)
        self.assertIn("SECURITY_THREAT_SCAN", actions)
        self.assertIn("PRICE_ENVELOPE_VALIDATION", actions)
        self.assertIn("RISK_TIER_ASSESSMENT", actions)
        self.assertIn("ORDER_CREATION", actions)

    def test_idempotency_prevents_duplicate_orders(self):
        """Same idempotency key should return identical order, not create new one."""
        key = "test-idempotency-key-123"
        result1 = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 68500.0, idempotency_key=key)
        result2 = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 68500.0, idempotency_key=key)
        self.assertEqual(result1["order_id"], result2["order_id"],
                         "Idempotency must return the same order ID (Paper 2 RQ2)")
        self.assertTrue(result2.get("idempotent_replay"),
                        "Second call with same key must be flagged as idempotent replay")

    def test_security_threat_zero_amount(self):
        """Zero amounts are a security threat and must be blocked."""
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 0.0)
        self.assertNotEqual(result["status"], "BOUNDED_VERIFIED",
                            "Zero-amount transactions must be blocked (Paper 2 RQ2)")

    def test_negative_amount_blocked(self):
        """Negative amounts must be blocked as security threats."""
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, -1000.0)
        self.assertNotEqual(result["status"], "BOUNDED_VERIFIED",
                            "Negative amounts must be blocked (Paper 2 RQ2)")

    def test_price_envelope_transparency(self):
        """Allouah et al. — price envelope details must be exposed, no hidden markups."""
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 68500.0)
        envelope = result.get("price_envelope", {})
        self.assertIn("nominal", envelope)
        self.assertIn("min_allowed", envelope)
        self.assertIn("max_allowed", envelope)
        self.assertIn("transparency_note", envelope,
                      "Price envelope must include a transparency note (Allouah et al.)")

    def test_uap_protocol_compliance(self):
        """Paper 2 RQ3 — order must be UAP protocol compliant."""
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 68500.0)
        self.assertTrue(result.get("uap_protocol_compliant"),
                        "Order must be UAP protocol compliant (Paper 2 RQ3)")
        self.assertIn("protocol_version", result)

    def test_payment_failure_handler(self):
        """Graceful failure recovery must be available."""
        result = self.agent.handle_payment_failure(
            "order_RZP_TEST123",
            "Payment timeout after 30s",
            SAMPLE_PRODUCT
        )
        self.assertEqual(result["status"], "PAYMENT_FAILED")
        self.assertIn("recovery_options", result)
        self.assertGreater(len(result["recovery_options"]), 0)
        self.assertTrue(result.get("retry_safe"), "Timeout failures should allow safe retry")

    def test_spend_velocity_guard_blocks_runaway_transactions(self):
        """Spend-velocity guard must block transactions when rolling 10-minute cap is exceeded."""
        # 1st order: ₹65,000 (Passes)
        res1 = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 65000.0, idempotency_key="vel-tx-1")
        self.assertEqual(res1["status"], "BOUNDED_VERIFIED")

        # 2nd order: ₹65,000 (Passes, rolling total ₹130,000 <= ₹150,000 cap)
        res2 = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 65000.0, idempotency_key="vel-tx-2")
        self.assertEqual(res2["status"], "BOUNDED_VERIFIED")

        # 3rd order: ₹65,000 (Blocks: rolling total ₹195,000 > ₹150,000 velocity limit)
        res3 = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 65000.0, idempotency_key="vel-tx-3")
        self.assertEqual(res3["status"], "VELOCITY_LIMIT_EXCEEDED")
        self.assertEqual(res3["failure_code"], "VELOCITY_LIMIT_EXCEEDED")

    def test_route_multi_vendor_splits(self):
        """Razorpay Route must calculate exact 85% OEM / 10% Distributor / 5% Platform splits."""
        # Amount ₹65,000 is within nominal price envelope [₹61,650 – ₹78,775]
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 65000.0, idempotency_key="route-tx-1")
        self.assertEqual(result["status"], "BOUNDED_VERIFIED")
        self.assertIn("route_transfers", result)
        splits = result["route_transfers"]["splits"]
        self.assertEqual(len(splits), 3)
        self.assertEqual(splits[0]["amount_inr"], 55250.0)  # 85% of 65,000
        self.assertEqual(splits[1]["amount_inr"], 6500.0)   # 10% of 65,000
        self.assertEqual(splits[2]["amount_inr"], 3250.0)   # 5% of 65,000

    def test_cryptographic_signature_format(self):
        """Signatures must follow SIG-SHA256 format for governance."""
        result = self.agent.validate_and_create_order(SAMPLE_PRODUCT, 68500.0)
        sig = result.get("cryptographic_signature", "")
        self.assertTrue(sig.startswith("SIG-SHA256:"),
                        f"Signature must start with SIG-SHA256: (got: {sig[:30]})")


# ─── Full Pipeline / Integration Tests ───────────────────────────────────────

class TestFullPipeline(unittest.TestCase):

    def setUp(self):
        self.catalog, self.sources, self.dataset_dir = load_catalog_if_available()
        self.coordinator = CoordinatorAgent()
        self.coordinator.catalog_data = self.catalog
        self.coordinator.sources_data = self.sources

    def test_full_pipeline_completes(self):
        """End-to-end: all 7 stages must complete without crashing."""
        result = self.coordinator.run_multi_agent_pipeline()
        self.assertIn(result["status"], ["COMPLETED", "FAILED"],
                      "Pipeline must return COMPLETED or FAILED (not raise)")
        self.assertEqual(len(result["pipeline_stages"]), 7,
                         "Pipeline must have exactly 7 stage results")

    def test_pipeline_with_real_dataset(self):
        """If the real datasets are present, the pipeline should return COMPLETED."""
        if not os.path.exists(os.path.join(self.dataset_dir, "industrial_catalog.json")):
            self.skipTest("Real dataset not available")
        result = self.coordinator.run_multi_agent_pipeline()
        self.assertEqual(result["status"], "COMPLETED",
                         "Full pipeline on real data should COMPLETE successfully")

    def test_all_research_compliance_fields_populated(self):
        """Every research paper compliance metric must be present in the output."""
        result = self.coordinator.run_multi_agent_pipeline()
        compliance = result.get("research_compliance", {})
        required_fields = [
            "grounded_citations", "conflicts_resolved", "multi_signal_flags",
            "subjective_needs_resolved", "intent_routing_active",
            "audit_trail_steps", "xai_trust_label"
        ]
        for field in required_fields:
            self.assertIn(field, compliance,
                          f"research_compliance missing '{field}'")

    def test_razorpay_order_id_in_pipeline_result(self):
        """A valid Razorpay order ID must be present after successful pipeline."""
        result = self.coordinator.run_multi_agent_pipeline()
        if result["status"] == "COMPLETED":
            self.assertIsNotNone(result.get("razorpay_order_id"),
                                 "Successful pipeline must produce a Razorpay order ID")

    def test_attestation_in_pipeline_result(self):
        """Pipeline must produce a cryptographic attestation."""
        result = self.coordinator.run_multi_agent_pipeline()
        attestation = result.get("attestation", "NOT_ATTESTED")
        self.assertNotEqual(attestation, "NOT_ATTESTED",
                            "Pipeline must produce a cryptographic attestation (Paper 2 RQ2)")

    def test_trust_score_above_threshold(self):
        """Trust score for well-documented product should be above 70%."""
        result = self.coordinator.run_multi_agent_pipeline()
        trust = result.get("trust_score", 0)
        self.assertGreaterEqual(trust, 70,
                                f"Trust score {trust}% is below the 70% quality threshold (Paper 2 RQ4)")

    def test_different_buyer_personas(self):
        """Pipeline should run successfully with different buyer personas."""
        for persona in ["procurement_engineer", "maintenance_technician", "catalog_manager"]:
            result = self.coordinator.run_multi_agent_pipeline(buyer_persona=persona)
            self.assertIn(result["status"], ["COMPLETED", "FAILED"],
                          f"Pipeline should not crash with persona '{persona}'")

    def test_pipeline_with_guardrail_violation_amount(self):
        """Pipeline should handle out-of-bounds amounts gracefully (not crash)."""
        result = self.coordinator.run_multi_agent_pipeline(
            requested_amount_inr=999_999.0  # Way above ceiling
        )
        # Last stage should show GUARDRAIL_VIOLATION, pipeline status FAILED
        last_stage = result["pipeline_stages"][-1]
        self.assertIn(last_stage["status"], ["GUARDRAIL_VIOLATION", "SECURITY_THREAT_DETECTED"],
                      "Out-of-bounds amount must trigger guardrail")


# ─── Test Runner ─────────────────────────────────────────────────────────────

def run_all_tests(verbose: bool = True) -> bool:
    """Run all tests and print a formatted summary."""
    print("\n" + "=" * 70)
    print("  PRODUCTPILOT AI — End-to-End Test Suite")
    print("  Research Paper: Agentic Commerce Multi-Agent Pipeline")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestSourceIngestionAgent,
        TestProductExtractionAgent,
        TestProductEnrichmentAgent,
        TestValidationConflictAgent,
        TestCommerceIntelligenceAgent,
        TestExplainabilityEvidenceAgent,
        TestRazorpaySettlementAgent,
        TestFullPipeline,
    ]

    for cls in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    total = result.testsRun
    failures = len(result.failures) + len(result.errors)
    passed = total - failures
    print(f"  RESULTS: {passed}/{total} passed | {failures} failed")
    print(f"  {'✅ ALL TESTS PASSED' if failures == 0 else '❌ SOME TESTS FAILED'}")
    print("=" * 70 + "\n")

    return failures == 0


if __name__ == "__main__":
    success = run_all_tests(verbose=True)
    sys.exit(0 if success else 1)
