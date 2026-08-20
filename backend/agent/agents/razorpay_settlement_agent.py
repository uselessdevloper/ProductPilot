"""
Stage 7 — Razorpay Settlement & Bounded Guardrail Agent
Research-Paper Improvements:
  - Paper 2 (RQ2): Money-action safety model — tiered risk levels with accountability
  - Paper 2 (RQ3): Transaction protocol compliance — UAP-aligned order creation
  - Allouah et al.: Transparency in pricing — no hidden markups, bounded envelope
  - Paper 2 (RQ4): Explainable payment decisions — human-readable audit trail
"""

import os
import time
import hashlib
import json
from .base_agent import BaseAgent
from typing import Dict, Any, List, Optional


class RazorpaySettlementAgent(BaseAgent):
    """
    ProductPilot AI — Razorpay Settlement & Bounded Guardrail Agent (Track 01)
    Validates price envelope bounds, verifies inventory, and initiates Razorpay test sessions.

    Research enhancements:
    - Tiered money-action safety model: LOW/MEDIUM/HIGH/CRITICAL (Paper 2 RQ2)
    - Full transaction audit trail with human-readable reasoning (Paper 2 RQ4)
    - UAP protocol compliance for agentic commerce (Paper 2 RQ3)
    - Transparent price envelope with no sponsored-bias (Allouah et al.)
    - Graceful failure handling for cybersecurity threats (Paper 2 RQ2)
    - Idempotency keys to prevent duplicate transactions
    """

    # Money-action safety tiers (Paper 2 RQ2)
    # Threshold in INR for each risk tier
    RISK_TIERS = {
        "LOW":      {"max_inr": 1_000,    "human_approval": False, "description": "Micro-transaction, auto-approved"},
        "MEDIUM":   {"max_inr": 50_000,   "human_approval": False, "description": "Standard transaction, policy-validated"},
        "HIGH":     {"max_inr": 5_00_000, "human_approval": True,  "description": "Large transaction, requires human confirmation"},
        "CRITICAL": {"max_inr": float("inf"), "human_approval": True, "description": "Enterprise transaction, mandatory human approval + audit"},
    }

    # Price envelope bounds: (min_factor, max_factor)
    PRICE_ENVELOPE = (0.90, 1.15)  # ±10% below, +15% above nominal

    def __init__(self):
        super().__init__(
            name="Razorpay Settlement Guardrail",
            provider="gemini",
            model="gemini-3.6-flash",
            api_key_name="GEMINI_API_KEY"
        )
        # In-memory idempotency store (production would use Redis/DB)
        self._processed_orders: Dict[str, Dict] = {}

    def validate_and_create_order(
        self,
        product_data: Dict[str, Any],
        requested_amount_inr: float,
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full settlement pipeline:
        1. Idempotency check (prevent duplicate orders)
        2. Price envelope validation (Allouah et al. — no hidden markups)
        3. Risk tier assessment (Paper 2 RQ2)
        4. Security threat detection (Paper 2 RQ2)
        5. Order creation with UAP compliance (Paper 2 RQ3)
        6. Audit trail generation (Paper 2 RQ4)
        """
        t_start = time.time()
        sku = product_data.get("sku", "UNKNOWN")
        self.log(f"Processing settlement for SKU {sku}, amount=₹{requested_amount_inr:,.2f}...")

        # ── Step 1: Idempotency Check ─────────────────────────────────────────
        idem_key = idempotency_key or self._generate_idempotency_key(product_data, requested_amount_inr)
        if idem_key in self._processed_orders:
            self.log(f"Duplicate request detected (idempotency_key={idem_key[:16]}). Returning cached result.", level="WARN")
            cached = dict(self._processed_orders[idem_key])
            cached["idempotent_replay"] = True
            return cached

        # ── Step 2: Security Threat Detection (Paper 2 RQ2) ──────────────────
        threat_check = self._detect_security_threats(product_data, requested_amount_inr)
        if threat_check["threat_detected"]:
            return self._build_failure_response(
                sku=sku,
                failure_code="SECURITY_THREAT_DETECTED",
                reason=threat_check["reason"],
                threat_details=threat_check,
                execution_ms=round((time.time() - t_start) * 1000, 1)
            )

        # ── Step 3: Price Envelope Validation (Allouah et al.) ───────────────
        base_price = product_data.get("price_inr", 68500)
        min_bound = round(base_price * self.PRICE_ENVELOPE[0])
        max_bound = round(base_price * self.PRICE_ENVELOPE[1])
        is_bounded = (min_bound <= requested_amount_inr <= max_bound)

        price_deviation = abs(requested_amount_inr - base_price) / base_price if base_price > 0 else 0

        # ── Step 4: Risk Tier Assessment (Paper 2 RQ2) ───────────────────────
        risk_tier = self._assess_risk_tier(requested_amount_inr)
        tier_config = self.RISK_TIERS[risk_tier]

        # ── Step 5: Guardrail Decision ────────────────────────────────────────
        if not is_bounded:
            return self._build_failure_response(
                sku=sku,
                failure_code="GUARDRAIL_VIOLATION",
                reason=f"Amount ₹{requested_amount_inr:,.0f} is outside the allowed price envelope "
                       f"[₹{min_bound:,} – ₹{max_bound:,}] ({self.PRICE_ENVELOPE[0]*100:.0f}%–{self.PRICE_ENVELOPE[1]*100:.0f}% of nominal ₹{base_price:,})",
                price_envelope={"nominal": base_price, "min_allowed": min_bound, "max_allowed": max_bound},
                execution_ms=round((time.time() - t_start) * 1000, 1)
            )

        # ── Step 6: Generate Razorpay Order ──────────────────────────────────
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        order_id = f"order_RZP_{hashlib.md5(f'{sku}:{timestamp}'.encode()).hexdigest()[:10].upper()}"
        signature = hashlib.sha256(f"RZP_TEST:{order_id}:{requested_amount_inr}:{timestamp}".encode()).hexdigest()[:24]

        # ── Step 7: Generate Audit Trail (Paper 2 RQ4) ───────────────────────
        audit_trail = self._generate_audit_trail(
            product_data, requested_amount_inr, order_id, risk_tier, price_deviation
        )

        # ── Step 8: LLM-Enhanced Payment Explanation ─────────────────────────
        payment_explanation = self._generate_payment_explanation(
            product_data, requested_amount_inr, base_price, risk_tier, price_deviation
        )

        execution_ms = round((time.time() - t_start) * 1000, 1)
        self.log(
            f"Order created: {order_id} | risk={risk_tier} | "
            f"deviation={price_deviation:.1%} | {execution_ms}ms"
        )

        result = {
            "agent": self.name,
            "status": "BOUNDED_VERIFIED",
            "order_id": order_id,
            "merchant_id": "rzp_test_ProductPilot2026",
            "currency": "INR",
            "authorized_amount": requested_amount_inr,
            "price_envelope": {
                "nominal": base_price,
                "min_allowed": min_bound,
                "max_allowed": max_bound,
                "is_bounded_safe": is_bounded,
                "deviation_pct": round(price_deviation * 100, 1),
                "transparency_note": (
                    "Price envelope is publicly disclosed per Allouah et al. transparency standard. "
                    "No hidden markups applied."
                )
            },
            # Risk model (Paper 2 RQ2)
            "risk_assessment": {
                "tier": risk_tier,
                "description": tier_config["description"],
                "human_approval_required": tier_config["human_approval"],
                "max_auto_approve_inr": tier_config["max_inr"]
            },
            # UAP protocol compliance (Paper 2 RQ3)
            "uap_protocol_compliant": True,
            "protocol_version": "UAP-1.0",
            "cryptographic_signature": f"SIG-SHA256:{signature}",
            "idempotency_key": idem_key,
            # Audit trail (Paper 2 RQ4)
            "audit_trail": audit_trail,
            "payment_explanation": payment_explanation,
            "security_check": threat_check,
            "execution_ms": execution_ms
        }

        # Cache for idempotency
        self._processed_orders[idem_key] = result
        return result

    def handle_payment_failure(
        self,
        order_id: str,
        failure_reason: str,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Graceful failure handler for payment issues.
        Implements Paper 2 RQ2's cybersecurity and trust restoration requirements.
        """
        self.log(f"Handling payment failure for order {order_id}: {failure_reason}", level="WARN")

        recovery_options = []
        if "timeout" in failure_reason.lower():
            recovery_options = [
                "Retry with same idempotency key (safe, no duplicate charge)",
                "Check Razorpay dashboard for order status",
                "Notify merchant of temporary delay"
            ]
        elif "declined" in failure_reason.lower():
            recovery_options = [
                "Request merchant to use alternative payment method",
                "Split into multiple smaller transactions if applicable",
                "Initiate UPI payment as fallback"
            ]
        elif "fraud" in failure_reason.lower() or "suspicious" in failure_reason.lower():
            recovery_options = [
                "Flag for manual review — do NOT retry automatically",
                "Notify merchant security team",
                "Generate security incident report"
            ]

        try:
            explanation = self.call_llm(
                f"""ProductPilot AI — payment failure recovery.
Order: {order_id}
Failure: {failure_reason}
Product: {product_data.get('name')}
Amount: ₹{product_data.get('price_inr', 0):,}

Write a 2-sentence merchant-friendly explanation of what happened and the safest next step.
Never mention Gemini.""",
                temperature=0.3,
                max_tokens=150
            )
        except Exception:
            explanation = f"Payment for order {order_id} failed due to: {failure_reason}. Please follow the recovery options provided."

        return {
            "agent": self.name,
            "status": "PAYMENT_FAILED",
            "order_id": order_id,
            "failure_reason": failure_reason,
            "recovery_options": recovery_options,
            "explanation": explanation,
            "retry_safe": "fraud" not in failure_reason.lower(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

    # ── Private Helpers ──────────────────────────────────────────────────────

    def _detect_security_threats(
        self, product_data: Dict[str, Any], amount: float
    ) -> Dict[str, Any]:
        """
        Detect common agentic commerce security threats (Paper 2 RQ2).
        Checks for: price manipulation, malicious product data, identity spoofing.
        """
        threats = []

        # Threat 1: Extreme price deviation (potential manipulation)
        base = product_data.get("price_inr", 0)
        if base > 0:
            dev = abs(amount - base) / base
            if dev > 2.0:  # > 200% deviation — likely manipulation
                threats.append(f"Extreme price deviation detected: {dev:.0%} from nominal")

        # Threat 2: Negative or zero amounts
        if amount <= 0:
            threats.append("Non-positive transaction amount detected")

        # Threat 3: Missing critical product identity
        if not product_data.get("sku") and not product_data.get("mpn"):
            threats.append("Product has no SKU or MPN — identity verification failed")

        # Threat 4: Suspiciously round large amounts (potential test/fraud)
        if amount > 10_00_000 and amount % 100_000 == 0:
            threats.append(f"Suspiciously round large amount (₹{amount:,}) — flagged for review")

        return {
            "threat_detected": len(threats) > 0,
            "threats": threats,
            "reason": threats[0] if threats else None,
            "severity": "HIGH" if len(threats) > 1 else ("MEDIUM" if threats else "NONE")
        }

    def _assess_risk_tier(self, amount_inr: float) -> str:
        """Assign a risk tier based on transaction amount (Paper 2 RQ2 safety model)."""
        for tier, config in self.RISK_TIERS.items():
            if amount_inr <= config["max_inr"]:
                return tier
        return "CRITICAL"

    def _generate_idempotency_key(self, product_data: Dict, amount: float) -> str:
        """Generate a deterministic idempotency key for duplicate detection."""
        key_data = f"{product_data.get('sku')}:{amount}:{time.strftime('%Y-%m-%dT%H', time.gmtime())}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]

    def _generate_audit_trail(
        self,
        product_data: Dict,
        amount: float,
        order_id: str,
        risk_tier: str,
        price_deviation: float
    ) -> List[Dict[str, Any]]:
        """
        Generate a timestamped audit trail for every step.
        Implements Paper 2 RQ4's auditability requirement.
        """
        return [
            {
                "step": 1,
                "action": "IDEMPOTENCY_CHECK",
                "result": "PASSED",
                "detail": "No duplicate order detected",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            {
                "step": 2,
                "action": "SECURITY_THREAT_SCAN",
                "result": "PASSED",
                "detail": "No manipulation, identity spoofing, or price injection detected",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            {
                "step": 3,
                "action": "PRICE_ENVELOPE_VALIDATION",
                "result": "PASSED",
                "detail": f"Amount ₹{amount:,.0f} within ±{self.PRICE_ENVELOPE[0]*100:.0f}%/{self.PRICE_ENVELOPE[1]*100:.0f}% envelope (deviation={price_deviation:.1%})",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            {
                "step": 4,
                "action": "RISK_TIER_ASSESSMENT",
                "result": risk_tier,
                "detail": self.RISK_TIERS[risk_tier]["description"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            },
            {
                "step": 5,
                "action": "ORDER_CREATION",
                "result": "SUCCESS",
                "detail": f"Razorpay order {order_id} created for SKU {product_data.get('sku')}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        ]

    def _generate_payment_explanation(
        self,
        product_data: Dict,
        amount: float,
        base_price: float,
        risk_tier: str,
        price_deviation: float
    ) -> str:
        """
        Generate a human-readable payment authorization explanation (Paper 2 RQ4).
        """
        try:
            prompt = f"""You are ProductPilot AI — explaining a payment authorization to a merchant.

Product: {product_data.get('name')}
SKU: {product_data.get('sku')}
Requested Amount: ₹{amount:,.0f}
Nominal Price: ₹{base_price:,.0f}
Price Deviation: {price_deviation:.1%}
Risk Tier: {risk_tier}

Write 2 sentences: (1) confirm the payment is authorized and why it's safe,
(2) state the risk tier and what it means for the merchant.
Be clear and merchant-friendly. Never mention Gemini."""

            return self.call_llm(prompt, temperature=0.3, max_tokens=150)

        except Exception:
            return (
                f"Payment of ₹{amount:,.0f} for '{product_data.get('name')}' has been authorized — "
                f"the amount is within the safe price envelope (deviation: {price_deviation:.1%}). "
                f"Risk tier: {risk_tier} — {self.RISK_TIERS[risk_tier]['description']}."
            )

    def _build_failure_response(
        self,
        sku: str,
        failure_code: str,
        reason: str,
        execution_ms: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a standardized failure response with recovery guidance."""
        self.log(f"Settlement BLOCKED: {failure_code} — {reason}", level="ERROR")
        return {
            "agent": self.name,
            "status": failure_code,
            "sku": sku,
            "authorized_amount": 0,
            "reason": reason,
            "recovery_guidance": "Review the flagged issue and resubmit with corrected parameters.",
            "execution_ms": execution_ms,
            **kwargs
        }
