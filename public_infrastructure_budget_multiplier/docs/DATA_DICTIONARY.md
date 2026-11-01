# Data dictionary

All monetary values use **millions of a single, consistent currency**. The model does not perform currency conversion.

| Field | Type / range | Meaning |
|---|---:|---|
| `name` | text, 1–120 chars | Human-readable project name. |
| `project_type` | enum | `road`, `bridge`, `rail`, `water`, `energy`, `public_building`, `broadband`, or `other`. |
| `phase` | enum | `concept`, `planning`, `preliminary_design`, `final_design`, `procurement`, or `construction`. |
| `capital_cost` | 0.01–1,000,000 | Current base estimate in millions, excluding the contingency entered below. |
| `duration_months` | 1–600 | Current planned duration to completion. |
| `labor_share_percent` | 0–100 | Share of base cost exposed to labor escalation. |
| `labor_escalation_percent` | −10–50 | Expected annual labor escalation. |
| `material_escalation_percent` | −10–50 | Expected annual materials escalation. |
| `estimate_escalation_percent` | −10–50 | Annual escalation already embedded in the base estimate. |
| `regulatory_bodies` | 0–100 | Distinct bodies expected to review, permit, fund, or approve. |
| `approvals_required` | 0–500 | Discrete approvals or permits on the current register. |
| `approval_complexity` | 1–5 | Relative difficulty, novelty, interdependence, and uncertainty of approvals. |
| `design_completion_percent` | 0–100 | Approximate share of design complete. |
| `site_uncertainty` | 1–5 | Relative uncertainty in geotechnical, utility, access, contamination, and existing-condition information. |
| `stakeholder_complexity` | 1–5 | Relative number, alignment, and influence of stakeholders. |
| `delivery_method` | enum | `design_bid_build`, `design_build`, `cmgc`, or `p3`. |
| `contingency_percent` | 0–200 | Funding held above the base estimate. Used only to calculate budget-exceedance probability. |
| `simulations` | 1,000–50,000 | Number of Monte Carlo iterations; defaults to 8,000. |
| `seed` | integer, optional | Explicit seed. If omitted, a stable seed is derived from the inputs. |

## Output fields

- `cost.p10`, `p50`, `p80`, `p90`: outturn amount and variance from baseline.
- `schedule.p10`, `p50`, `p80`, `p90`: outturn months and variance from baseline.
- `probability_exceeding_funded_budget_percent`: share of scenarios above baseline plus contingency.
- `confidence`: an input-maturity indicator, not statistical confidence or model accuracy.
- `drivers`: approximate expected cost contribution from each modeled component.
- `seed` and `model_version`: reproducibility metadata.

