"""
ProductPilot AI — Multi-Agent Orchestration Coordinator (Razorpay Track 01)

Engineering Implementation Summary:
  Stage 1 (Ingestion):   Bayesian authority-weighted source ranking & citable provenance
  Stage 2 (Extraction):  Grounded spatial citations, bounding boxes & physical boundary checks
  Stage 3 (Enrichment):  ETIM 8.0 & UNSPSC taxonomy mapping + dual-unit conversion
  Stage 4 (Validation):  Probabilistic conflict arbitration & deadlocked dispute escalation
  Stage 5 (Commerce):    Intent-based task routing + multi-channel syndication scoring
  Stage 6 (Explainability): Multi-dimensional XAI trust scoring + SHA-256 state attestation
  Stage 7 (Settlement):  Tiered money-action guardrails + Razorpay programmatic order creation
"""

import json
import os
from .base_agent import BaseAgent
from .source_ingestion_agent import SourceIngestionAgent
from .product_extraction_agent import ProductExtractionAgent
from .product_enrichment_agent import ProductEnrichmentAgent
from .validation_conflict_agent import ValidationConflictAgent
from .commerce_intelligence_agent import CommerceIntelligenceAgent
from .explainability_evidence_agent import ExplainabilityEvidenceAgent
from .razorpay_settlement_agent import RazorpaySettlementAgent
from typing import List, Dict, Any, Optional


class CoordinatorAgent(BaseAgent):
    """
    ProductPilot AI — Multi-Agent Orchestration Coordinator (Razorpay Track 01)
    Executes the 7-stage cooperative intelligence & settlement pipeline.
    """

    def __init__(self):
        super().__init__(
            name="ProductPilot Coordinator",
            provider="gemini",
            model="gemini-3.6-flash",
            api_key_name="GEMINI_API_KEY"
        )
        self.ingestion_agent = SourceIngestionAgent()
        self.extraction_agent = ProductExtractionAgent()
        self.enrichment_agent = ProductEnrichmentAgent()
        self.conflict_agent = ValidationConflictAgent()
        self.commerce_agent = CommerceIntelligenceAgent()
        self.explainability_agent = ExplainabilityEvidenceAgent()
        self.settlement_agent = RazorpaySettlementAgent()

        self.catalog_data: List[Dict[str, Any]] = []
        self.sources_data: List[Dict[str, Any]] = []

    def initialize_agents(self, dataset_dir: str):
        self.log("Initializing all 7 ProductPilot specialized agents...")
        cat_file = os.path.join(dataset_dir, "industrial_catalog.json")
        src_file = os.path.join(dataset_dir, "industrial_sources.json")

        if os.path.exists(cat_file):
            with open(cat_file, "r", encoding="utf-8") as f:
                self.catalog_data = json.load(f)
            self.log(f"Loaded {len(self.catalog_data)} products from industrial catalog.")
        else:
            self.log(f"Catalog file not found: {cat_file}", level="WARN")

        if os.path.exists(src_file):
            with open(src_file, "r", encoding="utf-8") as f:
                self.sources_data = json.load(f)
            self.log(f"Loaded {len(self.sources_data)} source groups.")
        else:
            self.log(f"Sources file not found: {src_file}", level="WARN")

    def run_multi_agent_pipeline(
        self,
        product_index: int = 0,
        buyer_persona: str = "procurement_engineer",
        merchant_intent: Optional[str] = None,
        requested_amount_inr: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute the full 7-stage cooperative intelligence & settlement pipeline.

        Args:
            product_index: Which product from the catalog to process (default: flagship)
            buyer_persona: B2B buyer persona for attribute prioritization
            merchant_intent: Optional merchant intent string for intent routing
            requested_amount_inr: Optional override for Razorpay settlement amount
        """
        self.log("Starting 7-agent cooperative execution pipeline...")

        # Select the flagship product
        flagship = self.catalog_data[product_index] if self.catalog_data else {}
        if not flagship:
            self.log("No product data available — using minimal demo product.", level="WARN")
            flagship = {
                "id": "DEMO-001", "sku": "DEMO-SKU-001", "name": "Demo Product",
                "price_inr": 5000, "attributes": {}, "taxonomies": {}
            }

        # ── Stage 1: Source Ingestion ─────────────────────────────────────────
        self.log("Stage 1: Source Ingestion Agent")
        ingestion_res = self.ingestion_agent.process_sources(self.sources_data)

        # ── Stage 2: Product Extraction ───────────────────────────────────────
        self.log("Stage 2: Product Extraction Agent")
        extraction_res = self.extraction_agent.extract_product_entities(
            flagship, buyer_persona=buyer_persona
        )

        # ── Stage 3: Product Enrichment ───────────────────────────────────────
        self.log("Stage 3: Product Enrichment Agent")
        enrichment_res = self.enrichment_agent.enrich(flagship)

        # ── Stage 4: Conflict Resolution ──────────────────────────────────────
        self.log("Stage 4: Validation & Conflict Agent")
        conflict_res = self.conflict_agent.resolve_product_conflicts(flagship)

        # ── Stage 5: Commerce Intelligence ───────────────────────────────────
        self.log("Stage 5: Commerce Intelligence Agent")
        commerce_res = self.commerce_agent.generate_commerce_profile(
            flagship, merchant_intent=merchant_intent
        )

        # ── Stage 6: Explainability & Grounding ───────────────────────────────
        self.log("Stage 6: Explainability & Evidence Agent")
        grounding_res = self.explainability_agent.ground_evidence(flagship)

        # ── Stage 7: Razorpay Settlement ──────────────────────────────────────
        self.log("Stage 7: Razorpay Settlement & Bounded Guardrail Agent")
        amount = requested_amount_inr or flagship.get("price_inr", 68500.0)
        settlement_res = self.settlement_agent.validate_and_create_order(
            flagship, requested_amount_inr=amount
        )

        # ── Pipeline Summary ──────────────────────────────────────────────────
        pipeline_success = settlement_res.get("status") == "BOUNDED_VERIFIED"
        trust_score = grounding_res.get("trust_score", {}).get("overall_score", 0)
        attestation = grounding_res.get("attestation", {})

        self.log(
            f"Pipeline complete: "
            f"product='{flagship.get('name')}', "
            f"trust={trust_score}%, "
            f"order={settlement_res.get('order_id', 'FAILED')}, "
            f"success={pipeline_success}"
        )

        return {
            "status": "COMPLETED" if pipeline_success else "FAILED",
            "pipeline_stages": [
                ingestion_res,
                extraction_res,
                enrichment_res,
                conflict_res,
                commerce_res,
                grounding_res,
                settlement_res
            ],
            "product_name": flagship.get("name"),
            "sku": flagship.get("sku"),
            "readiness_score": enrichment_res.get("completeness_score", flagship.get("commerce_readiness_score", 0)),
            "trust_score": trust_score,
            "razorpay_order_id": settlement_res.get("order_id"),
            "risk_tier": settlement_res.get("risk_assessment", {}).get("tier", "UNKNOWN"),
            "detected_intent": commerce_res.get("detected_intent"),
            "attestation": attestation.get("short_signature", "NOT_ATTESTED"),
            # Research paper compliance summary
            "research_compliance": {
                "grounded_citations": grounding_res.get("grounded_citations_count", 0),
                "conflicts_resolved": conflict_res.get("resolved_conflicts_count", 0),
                "multi_signal_flags": len(conflict_res.get("multi_signal_validation", {}).get("single_source_flags", [])),
                "subjective_needs_resolved": extraction_res.get("subjective_need_resolution", {}).get("detected_subjective_needs", 0),
                "intent_routing_active": bool(commerce_res.get("detected_intent")),
                "audit_trail_steps": len(settlement_res.get("audit_trail", [])),
                "xai_trust_label": grounding_res.get("trust_score", {}).get("label", "UNKNOWN")
            }
        }
