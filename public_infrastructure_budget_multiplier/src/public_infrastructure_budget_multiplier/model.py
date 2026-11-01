"""Transparent Monte Carlo model for infrastructure cost and schedule risk.

The model is deliberately compact and auditable. Its coefficients are starter
priors, not universal benchmarks. Agencies should replace them with calibrated
forecast errors from their own completed projects before making decisions.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from typing import Any


class ModelInputError(ValueError):
    """Raised when a submitted project cannot be modeled safely."""


PROJECT_PROFILES = {
    "road": {"label": "Road / highway", "scope": 0.08, "schedule": 0.08},
    "bridge": {"label": "Bridge / tunnel", "scope": 0.12, "schedule": 0.12},
    "rail": {"label": "Rail / transit", "scope": 0.16, "schedule": 0.16},
    "water": {"label": "Water / wastewater", "scope": 0.10, "schedule": 0.10},
    "energy": {"label": "Energy / grid", "scope": 0.12, "schedule": 0.11},
    "public_building": {"label": "Public building", "scope": 0.09, "schedule": 0.09},
    "broadband": {"label": "Broadband / digital", "scope": 0.08, "schedule": 0.08},
    "other": {"label": "Other infrastructure", "scope": 0.10, "schedule": 0.10},
}

PHASE_MULTIPLIERS = {
    "concept": 1.50,
    "planning": 1.30,
    "preliminary_design": 1.10,
    "final_design": 0.80,
    "procurement": 0.60,
    "construction": 0.40,
}

DELIVERY_MODIFIERS = {
    "design_bid_build": {"cost": 1.00, "schedule": 1.00},
    "design_build": {"cost": 0.90, "schedule": 0.84},
    "cmgc": {"cost": 0.92, "schedule": 0.90},
    "p3": {"cost": 0.88, "schedule": 0.88},
}

DEFAULTS: dict[str, Any] = {
    "name": "Untitled infrastructure project",
    "project_type": "road",
    "phase": "planning",
    "capital_cost": 250.0,
    "duration_months": 48.0,
    "labor_share_percent": 35.0,
    "labor_escalation_percent": 4.5,
    "material_escalation_percent": 4.0,
    "estimate_escalation_percent": 3.0,
    "regulatory_bodies": 3,
    "approvals_required": 6,
    "approval_complexity": 3,
    "design_completion_percent": 20.0,
    "site_uncertainty": 3,
    "stakeholder_complexity": 3,
    "delivery_method": "design_bid_build",
    "contingency_percent": 15.0,
    "simulations": 8000,
}

NUMERIC_RANGES = {
    "capital_cost": (0.01, 1_000_000.0),
    "duration_months": (1.0, 600.0),
    "labor_share_percent": (0.0, 100.0),
    "labor_escalation_percent": (-10.0, 50.0),
    "material_escalation_percent": (-10.0, 50.0),
    "estimate_escalation_percent": (-10.0, 50.0),
    "regulatory_bodies": (0, 100),
    "approvals_required": (0, 500),
    "approval_complexity": (1, 5),
    "design_completion_percent": (0.0, 100.0),
    "site_uncertainty": (1, 5),
    "stakeholder_complexity": (1, 5),
    "contingency_percent": (0.0, 200.0),
    "simulations": (1000, 50_000),
}


@dataclass(frozen=True)
class PreparedProject:
    values: dict[str, Any]
    seed: int


def _prepare(payload: dict[str, Any]) -> PreparedProject:
    if not isinstance(payload, dict):
        raise ModelInputError("Request body must be a JSON object.")

    values = {**DEFAULTS, **payload}
    values["name"] = str(values.get("name", "")).strip()[:120] or DEFAULTS["name"]

    if values["project_type"] not in PROJECT_PROFILES:
        raise ModelInputError(f"Unsupported project_type: {values['project_type']}")
    if values["phase"] not in PHASE_MULTIPLIERS:
        raise ModelInputError(f"Unsupported phase: {values['phase']}")
    if values["delivery_method"] not in DELIVERY_MODIFIERS:
        raise ModelInputError(f"Unsupported delivery_method: {values['delivery_method']}")

    integer_fields = {
        "regulatory_bodies",
        "approvals_required",
        "approval_complexity",
        "site_uncertainty",
        "stakeholder_complexity",
        "simulations",
    }
    for field, (minimum, maximum) in NUMERIC_RANGES.items():
        try:
            number = float(values[field])
        except (TypeError, ValueError) as exc:
            raise ModelInputError(f"{field} must be numeric.") from exc
        if not math.isfinite(number) or not minimum <= number <= maximum:
            raise ModelInputError(f"{field} must be between {minimum} and {maximum}.")
        values[field] = int(number) if field in integer_fields else number

    if "seed" in payload:
        try:
            seed = int(payload["seed"])
        except (TypeError, ValueError) as exc:
            raise ModelInputError("seed must be an integer.") from exc
    else:
        # Only physical/model inputs influence the random stream. A project rename,
        # contingency choice, or iteration-count change must not select a different
        # underlying scenario sequence.
        seed_exclusions = {"name", "contingency_percent", "simulations"}
        seed_payload = {key: values[key] for key in sorted(values) if key not in seed_exclusions}
        digest = hashlib.sha256(json.dumps(seed_payload, sort_keys=True).encode()).hexdigest()
        seed = int(digest[:16], 16)
    return PreparedProject(values=values, seed=seed)


def _percentile(sorted_values: list[float], percentile: float) -> float:
    index = (len(sorted_values) - 1) * percentile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return sorted_values[lower]
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _round(value: float, digits: int = 2) -> float:
    return round(value + 0.0, digits)


def estimate_project(payload: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic P50/P80/P90 estimates for a project payload."""

    prepared = _prepare(payload)
    p = prepared.values
    rng = random.Random(prepared.seed)
    profile = PROJECT_PROFILES[p["project_type"]]
    phase_multiplier = PHASE_MULTIPLIERS[p["phase"]]
    delivery = DELIVERY_MODIFIERS[p["delivery_method"]]

    base_cost = p["capital_cost"]
    base_months = p["duration_months"]
    labor_share = p["labor_share_percent"] / 100
    material_share = max(0.0, 1 - labor_share) * 0.62
    midpoint_years = base_months / 24
    maturity_gap = 1 - p["design_completion_percent"] / 100

    # Large programs tend to have more interfaces. This is deliberately capped.
    capital_complexity = max(0.0, min(0.06, math.log10(max(base_cost, 100) / 100) * 0.015))
    scope_mode = (profile["scope"] * phase_multiplier * (0.35 + 0.65 * maturity_gap))
    scope_mode = (scope_mode + capital_complexity) * delivery["cost"]

    labor_delta = (p["labor_escalation_percent"] - p["estimate_escalation_percent"]) / 100
    material_delta = (p["material_escalation_percent"] - p["estimate_escalation_percent"]) / 100
    escalation_mode = midpoint_years * (labor_share * labor_delta + material_share * material_delta)

    approval_load = math.log1p(p["approvals_required"]) * (0.35 + 0.13 * p["approval_complexity"])
    body_load = math.log1p(p["regulatory_bodies"]) * 0.55
    regulatory_mode_months = max(0.0, (approval_load + body_load - 0.7) * phase_multiplier)
    regulatory_mode_months *= delivery["schedule"]

    site_probability = min(0.58, 0.04 + 0.075 * p["site_uncertainty"] * phase_multiplier)
    site_cost_mode = 0.012 * p["site_uncertainty"] * phase_multiplier
    stakeholder_mode = 0.008 * max(0, p["stakeholder_complexity"] - 1) * phase_multiplier

    costs: list[float] = []
    durations: list[float] = []
    exceed_budget = 0
    funded_budget = base_cost * (1 + p["contingency_percent"] / 100)

    for _ in range(p["simulations"]):
        scope = rng.triangular(-0.015, scope_mode * 2.4 + 0.02, scope_mode)

        labor_rate = rng.triangular(labor_delta - 0.025, labor_delta + 0.045, labor_delta)
        material_rate = rng.triangular(material_delta - 0.035, material_delta + 0.075, material_delta)
        escalation = midpoint_years * (labor_share * labor_rate + material_share * material_rate)

        regulatory_delay = rng.triangular(0, regulatory_mode_months * 2.5 + 0.5, regulatory_mode_months)
        regulatory_cost = (regulatory_delay / max(base_months, 1)) * 0.18

        if rng.random() < site_probability:
            site_cost = rng.triangular(0.005, site_cost_mode * 3.0 + 0.01, site_cost_mode)
            site_delay = rng.triangular(0.2, base_months * site_cost_mode * 1.8 + 1, base_months * site_cost_mode)
        else:
            site_cost = 0.0
            site_delay = 0.0

        stakeholder = rng.triangular(0, stakeholder_mode * 2.8 + 0.005, stakeholder_mode)
        random_noise = rng.triangular(-0.025, 0.045, 0.005)

        cost_overrun = max(-0.12, scope + escalation + regulatory_cost + site_cost + stakeholder + random_noise)
        schedule_uncertainty = rng.triangular(
            -0.025,
            profile["schedule"] * phase_multiplier * 2.2 + 0.03,
            profile["schedule"] * phase_multiplier * (0.30 + 0.70 * maturity_gap),
        )
        stakeholder_delay = base_months * stakeholder * 0.65
        schedule_overrun = max(
            -0.10,
            (scope * 0.42 + schedule_uncertainty) * delivery["schedule"]
            + (regulatory_delay + site_delay + stakeholder_delay) / base_months,
        )

        cost = base_cost * (1 + cost_overrun)
        duration = base_months * (1 + schedule_overrun)
        costs.append(cost)
        durations.append(duration)
        exceed_budget += cost > funded_budget

    costs.sort()
    durations.sort()

    cost_points = {key: _percentile(costs, q) for key, q in (("p10", 0.10), ("p50", 0.50), ("p80", 0.80), ("p90", 0.90))}
    time_points = {key: _percentile(durations, q) for key, q in (("p10", 0.10), ("p50", 0.50), ("p80", 0.80), ("p90", 0.90))}

    driver_values = {
        "Scope & design maturity": scope_mode,
        "Labor and material escalation": escalation_mode,
        "Regulatory coordination": (regulatory_mode_months / base_months) * 0.18,
        "Site conditions": site_probability * site_cost_mode,
        "Stakeholder complexity": stakeholder_mode,
        "Capital / interface complexity": capital_complexity,
    }
    drivers = [
        {"name": name, "expected_cost_effect_percent": _round(value * 100, 1)}
        for name, value in sorted(driver_values.items(), key=lambda item: abs(item[1]), reverse=True)
    ]

    def cost_result(value: float) -> dict[str, float]:
        return {
            "amount": _round(value),
            "variance_percent": _round((value / base_cost - 1) * 100, 1),
        }

    def schedule_result(value: float) -> dict[str, float]:
        return {
            "months": _round(value, 1),
            "variance_percent": _round((value / base_months - 1) * 100, 1),
        }

    confidence_score = 100 - (
        12 * phase_multiplier
        + 10 * maturity_gap
        + 3.5 * p["site_uncertainty"]
        + 2.5 * p["approval_complexity"]
        + min(10, p["regulatory_bodies"])
    )
    confidence_score = int(max(10, min(90, round(confidence_score))))

    return {
        "model_version": "0.1.0",
        "seed": prepared.seed,
        "project": {**p, "project_type_label": profile["label"]},
        "baseline": {
            "capital_cost": _round(base_cost),
            "duration_months": _round(base_months, 1),
            "funded_budget_with_contingency": _round(funded_budget),
        },
        "cost": {key: cost_result(value) for key, value in cost_points.items()},
        "schedule": {key: schedule_result(value) for key, value in time_points.items()},
        "probability_exceeding_funded_budget_percent": _round(exceed_budget / p["simulations"] * 100, 1),
        "confidence": {
            "score": confidence_score,
            "label": "Higher" if confidence_score >= 70 else "Moderate" if confidence_score >= 45 else "Lower",
        },
        "drivers": drivers,
        "assumptions": {
            "currency": "Input currency, in millions",
            "price_basis": "Escalation is modeled above the rate embedded in the estimate",
            "contingency": "Contingency affects budget-exceedance probability, not simulated outturn cost",
            "calibration": "Starter priors; replace with local completed-project data",
        },
    }

