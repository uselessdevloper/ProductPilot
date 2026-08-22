"""
ProductPilot AI — Comprehensive Failure Mode & Adversarial Input Test Suite
Tests adversarial inputs, malformed data, security attacks, and graceful failure modes across all 7 agents.

Run: pytest backend/agent/tests/test_failure_modes.py -v
"""

import sys
import os
import time
import hmac
import hashlib
import pytest

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


# =============================================================================
# Agent 1: Source Ingestion Failure Modes
# =============================================================================

class TestAgent1IngestionFailureModes:
    def setup_method(self):
        self.agent = SourceIngestionAgent()

    def test_non_list_input_returns_malformed_status(self):
        """Passing non-list input should return structured MALFORMED_INPUT error without crashing."""
        result = self.agent.process_sources("not-a-list")  # type: ignore
        assert result["status"] == "MALFORMED_INPUT"
        assert result["error_code"] == "INVALID_SOURCES_DATA_TYPE"
        assert result["protocol_compliance"]["ready_for_extraction"] is False

    def test_empty_list_returns_empty_status(self):
        """Passing empty source list should return COMPLETED with 0 sources and ready_for_extraction False."""
        result = self.agent.process_sources([])
        assert result["status"] == "COMPLETED"
        assert len(result["ingested_sources"]) == 0
        assert result["protocol_compliance"]["ready_for_extraction"] is False

    def test_clamping_out_of_bounds_authority_weights(self):
        """Authority weights outside [0.0, 1.0] (e.g. -0.8 or 2.5) must be clamped safely."""
        sources = [
            {"id": "SRC-LOW", "name": "Negative Weight", "authority_weight": -0.8},
            {"id": "SRC-HIGH", "name": "Exorbitant Weight", "authority_weight": 2.5}
        ]
        result = self.agent.process_sources(sources)
        assert result["status"] == "COMPLETED"
        authorities = [s["authority_weight"] for s in result["ingested_sources"]]
        assert min(authorities) >= 0.0
        assert max(authorities) <= 1.0

    def test_non_dict_elements_skipped_with_warning(self):
        """Corrupt non-dict elements in source array should be skipped with validation warnings."""
        sources = [
            {"id": "SRC-01", "name": "Valid Doc", "authority_weight": 0.90},
            "corrupt_string_item",
            None,
            12345
        ]
        result = self.agent.process_sources(sources)  # type: ignore
        assert result["status"] == "COMPLETED"
        assert len(result["ingested_sources"]) == 1
        assert len(result["validation_warnings"]) >= 3


# =============================================================================
# Agent 2: Product Extraction Failure Modes
# =============================================================================

class TestAgent2ExtractionFailureModes:
    def setup_method(self):
        self.agent = ProductExtractionAgent()

    def test_empty_or_none_product_returns_malformed_input(self):
        """Extracting entities from empty dict or None must return structured error."""
        result = self.agent.extract_product_entities({})
        assert result["status"] == "MALFORMED_INPUT"
        assert result["error_code"] == "INVALID_PRODUCT_DATA"

    def test_negative_physical_values_flag_outlier_warning(self):
        """Negative physical specs (e.g. weight = -15 kg, voltage = -240 V) must trigger boundary warnings."""
        adversarial_product = {
            "id": "PROD-ADV-001",
            "name": "Corrupt Industrial Pump",
            "sku": "PUMP-BAD-01",
            "attributes": {
                "weight": {"name": "Weight", "value": "-15.0", "unit": "kg"},
                "voltage": {"name": "Voltage", "value": "-240", "unit": "V"},
                "max_flow_rate": {"name": "Flow", "value": "-500", "unit": "L/min"}
            }
        }
        result = self.agent.extract_product_entities(adversarial_product)
        assert result["status"] == "EXTRACTION_WITH_WARNINGS"
        assert len(result["validation_warnings"]) >= 3
        assert any("below physical minimum" in w for w in result["validation_warnings"])

    def test_exorbitant_physical_values_flag_ceiling_warning(self):
        """Unrealistically massive physical specs (e.g. 500,000 kg pump) must trigger ceiling warning."""
        adversarial_product = {
            "id": "PROD-ADV-002",
            "name": "Giant Pump",
            "sku": "PUMP-BIG-01",
            "attributes": {
                "weight": {"name": "Weight", "value": "999999", "unit": "kg"},
                "voltage": {"name": "Voltage", "value": "999999", "unit": "V"}
            }
        }
        result = self.agent.extract_product_entities(adversarial_product)
        assert result["status"] == "EXTRACTION_WITH_WARNINGS"
        assert any("exceeds physical ceiling" in w for w in result["validation_warnings"])


# =============================================================================
# Agent 3: Product Enrichment Failure Modes
# =============================================================================

class TestAgent3EnrichmentFailureModes:
    def setup_method(self):
        self.agent = ProductEnrichmentAgent()

    def test_empty_product_returns_malformed_input(self):
        """Enriching an empty dictionary must return structured error."""
        result = self.agent.enrich({})
        assert result["status"] == "MALFORMED_INPUT"
        assert result["error_code"] == "INVALID_PRODUCT_DATA"
        assert result["completeness_score"] == 0.0

    def test_unparseable_unit_strings_handled_gracefully(self):
        """Non-numeric values in convertible unit attributes must not crash unit conversion."""
        product = {
            "id": "PROD-UNIT-01",
            "name": "Odd Product",
            "attributes": {
                "weight": {"value": "N/A - See Drawing", "unit": "kg"},
                "pressure": {"value": "Variable / Consult Factory", "unit": "bar"}
            }
        }
        result = self.agent.enrich(product)
        assert "weight" in result["enriched_attributes"]
        assert "pressure" in result["enriched_attributes"]
        # alt_value shouldn't crash or exist for non-numeric
        assert "alt_value" not in result["enriched_attributes"]["weight"]


# =============================================================================
# Agent 4: Validation & Conflict Failure Modes
# =============================================================================

class TestAgent4ValidationConflictFailureModes:
    def setup_method(self):
        self.agent = ValidationConflictAgent()

    def test_empty_product_returns_malformed_input(self):
        """Conflict resolution on empty dict returns structured error."""
        result = self.agent.resolve_product_conflicts({})
        assert result["status"] == "MALFORMED_INPUT"
        assert result["resolved_conflicts_count"] == 0

    def test_deadlocked_equal_authority_conflict_escalates_to_human(self):
        """Two sources with identical authority (e.g. 0.90 vs 0.90) asserting contradictory values must escalate to human."""
        deadlocked_product = {
            "id": "PROD-DEADLOCK",
            "name": "Deadlocked Pump",
            "attributes": {
                "weight": {
                    "name": "Net Weight",
                    "conflict_details": {
                        "attribute_key": "weight",
                        "sources": [
                            {"source_id": "SRC-A", "source_name": "Datasheet Revision A", "authority_weight": 0.90, "value": "12.5 kg"},
                            {"source_id": "SRC-B", "source_name": "Datasheet Revision B", "authority_weight": 0.90, "value": "25.0 kg"}
                        ]
                    }
                }
            }
        }
        result = self.agent.resolve_product_conflicts(deadlocked_product)
        assert result["status"] == "DISPUTES_ESCALATED"
        assert result["unresolved_conflicts_count"] == 1
        unresolved = result["unresolved"][0]
        assert unresolved["escalated_to_human"] is True
        assert unresolved["resolution_method"] == "ESCALATED_HUMAN_ARBITRATION"

    def test_empty_sources_handled_gracefully(self):
        """Attribute with empty sources list in conflict details handled safely."""
        product = {
            "id": "PROD-EMPTY-SRC",
            "name": "Empty Sources",
            "attributes": {
                "weight": {
                    "name": "Weight",
                    "value": "10.0 kg",
                    "conflict_details": {"sources": []}
                }
            }
        }
        result = self.agent.resolve_product_conflicts(product)
        assert result["status"] == "COMPLETED"
        assert result["details"][0]["resolution_method"] == "NO_SOURCES"


# =============================================================================
# Agent 5: Commerce Intelligence Failure Modes
# =============================================================================

class TestAgent5CommerceFailureModes:
    def setup_method(self):
        self.agent = CommerceIntelligenceAgent()

    def test_empty_product_returns_malformed_input(self):
        """Commerce profile on empty dictionary returns structured error."""
        result = self.agent.generate_commerce_profile({})
        assert result["status"] == "MALFORMED_INPUT"
        assert result["error_code"] == "INVALID_PRODUCT_DATA"
        assert result["razorpay_ready"]["ready"] is False

    def test_missing_channels_produce_partial_ready_status(self):
        """Product missing images, taxonomies, and descriptions fails full channel readiness."""
        sparse_product = {
            "id": "PROD-SPARSE",
            "sku": "SPARSE-001",
            "price_inr": 1000
        }
        result = self.agent.generate_commerce_profile(sparse_product)
        assert result["status"] == "PARTIAL_READY"
        assert any(ch["status"] in ("PARTIAL", "NOT_READY") for ch in result["channels"].values())


# =============================================================================
# Agent 6: Explainability & Evidence Failure Modes
# =============================================================================

class TestAgent6ExplainabilityFailureModes:
    def setup_method(self):
        self.agent = ExplainabilityEvidenceAgent()

    def test_empty_product_returns_attestation_rejected(self):
        """Empty product profile rejects cryptographic attestation."""
        result = self.agent.ground_evidence({})
        assert result["status"] == "ATTESTATION_REJECTED"
        assert result["trust_score"]["overall_score"] == 0

    def test_totally_ungrounded_product_is_rejected(self):
        """Product with attributes having zero provenance cannot receive verified attestation."""
        ungrounded_product = {
            "id": "PROD-UNGROUNDED",
            "name": "Hallucinated Specs",
            "sku": "FAKE-01",
            "attributes": {
                "flow_rate": {"value": "500 L/min"},
                "pressure": {"value": "200 bar"},
                "voltage": {"value": "440 V"}
            }
        }
        result = self.agent.ground_evidence(ungrounded_product)
        assert result["grounded_citations_count"] == 0
        assert result["ungrounded_count"] == 3
        assert result["trust_score"]["overall_score"] < 50
        assert result["status"] == "ATTESTATION_REJECTED"


# =============================================================================
# Agent 7: Razorpay Settlement Failure Modes & Security Guards
# =============================================================================

class TestAgent7RazorpaySettlementFailureModes:
    def setup_method(self):
        self.agent = RazorpaySettlementAgent()
        self.sample_product = {
            "sku": "APE-X200-PUMP",
            "name": "Industrial Pump X200",
            "price_inr": 68500
        }

    def test_price_discount_hack_rejected(self):
        """Attempting a 40% discount (₹41,100 on ₹68,500 nominal) must be hard-blocked by price envelope."""
        result = self.agent.validate_and_create_order(self.sample_product, requested_amount_inr=41100)
        assert result["status"] == "GUARDRAIL_VIOLATION"
        assert "outside the allowed price envelope" in result["reason"]
        assert result["authorized_amount"] == 0

    def test_price_spike_rejected(self):
        """Attempting a 200% price spike (₹2,00,000 on ₹68,500 nominal) must be blocked."""
        result = self.agent.validate_and_create_order(self.sample_product, requested_amount_inr=200000)
        assert result["status"] == "GUARDRAIL_VIOLATION"

    def test_negative_transaction_amount_rejected_as_security_threat(self):
        """Negative transaction amounts must be blocked with SECURITY_THREAT_DETECTED."""
        result = self.agent.validate_and_create_order(self.sample_product, requested_amount_inr=-500)
        assert result["status"] == "SECURITY_THREAT_DETECTED"
        assert "Non-positive transaction amount" in result["reason"]

    def test_missing_sku_identity_rejected(self):
        """Product with no SKU or MPN fails identity verification."""
        product_no_id = {"name": "Anonymous Pump", "price_inr": 1000}
        result = self.agent.validate_and_create_order(product_no_id, requested_amount_inr=1000)
        assert result["status"] == "SECURITY_THREAT_DETECTED"
        assert "no SKU or MPN" in result["reason"]

    def test_spend_velocity_flood_blocked(self):
        """Rapid burst of transactions exceeding the rolling limit must be blocked."""
        agent = RazorpaySettlementAgent()
        # Simulate 3 approved transactions of ₹40,000 (total ₹120,000)
        for i in range(3):
            prod = {"sku": f"SKU-{i}", "price_inr": 40000}
            res = agent.validate_and_create_order(prod, requested_amount_inr=40000, idempotency_key=f"tx_{i}_{time.time()}")
            assert res["status"] == "BOUNDED_VERIFIED"

        # 4th transaction of ₹40,000 pushes rolling sum to ₹160,000 (> ₹150,000 cap)
        prod_4 = {"sku": "SKU-4", "price_inr": 40000}
        res_4 = agent.validate_and_create_order(prod_4, requested_amount_inr=40000, idempotency_key=f"tx_4_{time.time()}")
        assert res_4["status"] == "VELOCITY_LIMIT_EXCEEDED"
        assert "Velocity Anomaly Detected" in res_4["reason"]

    def test_webhook_hmac_sha256_verification_valid_and_invalid(self):
        """Valid HMAC signature passes; tampered payload or signature fails."""
        secret = "rzp_webhook_secret_key_12345"
        payload = '{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_123"}}}}'
        
        # Valid signature
        valid_sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        assert self.agent.verify_webhook_signature(payload, valid_sig, secret) is True

        # Tampered payload
        tampered_payload = '{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_FORGED"}}}}'
        assert self.agent.verify_webhook_signature(tampered_payload, valid_sig, secret) is False

        # Tampered signature
        assert self.agent.verify_webhook_signature(payload, "invalid_hex_signature", secret) is False

    def test_sub_200ms_graceful_fallback_payment_link(self):
        """Graceful fallback generates a valid payment link in sub-200ms."""
        fallback = self.agent.generate_payment_link_fallback(
            self.sample_product,
            requested_amount_inr=68500,
            reason="Agent session timeout"
        )
        assert fallback["status"] == "FALLBACK_PAYMENT_LINK_CREATED"
        assert fallback["payment_link_id"].startswith("plink_")
        assert fallback["short_url"].startswith("https://rzp.io/i/")
        assert fallback["execution_ms"] < 200.0
