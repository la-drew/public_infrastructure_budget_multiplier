# Methodology

## Purpose and interpretation

public_infrastructure_budget_multiplier estimates a **planning range**, not a single predicted outcome. P80 cost means 80% of simulated outturn costs are at or below that value under the stated inputs and model assumptions. It does not mean the project has an objectively measured 80% chance of meeting that figure.

The model is most useful for:

1. testing whether a funding or schedule allowance is broadly consistent with stated uncertainty;
2. identifying assumptions that deserve more investigation; and
3. comparing projects using a consistent, inspectable method.

It is not appropriate for bids, quantity takeoffs, audited financial reporting, legal conclusions, or final investment decisions.

## Calculation overview

Each simulation produces a cost overrun ratio and schedule overrun ratio:

```text
cost overrun = scope + escalation + regulatory carrying cost
             + site event + stakeholder effect + residual uncertainty

schedule overrun = delivery modifier × (0.42 × scope + schedule uncertainty)
                 + (regulatory delay + site delay + stakeholder delay)
                   / planned duration
```

The result is converted back to the user's baseline:

```text
outturn cost = baseline capital cost × (1 + cost overrun)
outturn duration = planned duration × (1 + schedule overrun)
```

The samples are sorted and empirical percentiles are reported. The random seed is derived from normalized inputs, so identical inputs return identical results.

## Components

### Scope and design maturity

Each asset type has an editable scope prior. It is multiplied by:

- project phase (1.50 at concept, falling to 0.40 during construction);
- the incomplete share of design;
- a capped capital/interface factor for projects over 100 million; and
- the selected delivery-method modifier.

This captures a general proposition—not a universal law—that less mature definitions and more interfaces produce wider ranges.

### Escalation exposure

Only escalation **above the rate already embedded in the estimate** is modeled. Exposure is measured to the planned construction midpoint:

```text
years to midpoint = planned months / 24

escalation = years to midpoint × (
  labor share × (labor rate − embedded rate)
  + material share × (material rate − embedded rate)
)
```

Material share is initially estimated as 62% of the non-labor share. This is a starter assumption to replace with a project cost breakdown when available.

### Regulatory coordination

Approval and regulatory-body counts use logarithmic scaling so the 20th approval contributes less incremental uncertainty than the first few. Approval complexity and phase affect the mode of a triangular delay distribution. Delay also creates a small time-related cost exposure.

This is not a legal or jurisdiction-specific approval-duration model. A project team should replace it with an approval register and empirical durations.

### Site and stakeholder events

Site uncertainty controls both the probability and impact of a differing-condition event. Stakeholder complexity adds a smaller continuous cost and delay distribution. Both effects decrease as the project advances.

### Contingency

Contingency is treated as funding capacity, not a cost. It does not increase simulated outturn cost. The model compares each simulated outturn with:

```text
funded budget = baseline cost × (1 + contingency percentage)
```

The share of simulations above that amount is the displayed budget-exceedance probability.

## Distributions and dependence

The MVP uses bounded triangular distributions because they are inspectable and useful when a full empirical distribution is unavailable. Scope, regulatory delay, and site events affect both cost and time in the same simulation, introducing a practical correlation between the two outcomes.

Triangular bounds and modes are visible in [`src/public_infrastructure_budget_multiplier/model.py`](../src/public_infrastructure_budget_multiplier/model.py). They should be calibrated, versioned, and backtested.

## Calibration workflow

For production use:

1. Assemble completed projects with a consistently defined decision baseline and outturn.
2. Segment by asset class, jurisdiction, phase, scale, and delivery method.
3. Calculate cost and schedule forecast error; document scope and price-base changes separately.
4. Fit or empirically resample component distributions.
5. Backtest on held-out projects and compare expected percentile coverage with observed outcomes.
6. Review calibration periodically and keep an auditable model-version history.

Avoid training on incomparable baselines. For example, a concept estimate and contract-award estimate are different forecast origins.

## Evidence base

- The [GAO Cost Estimating and Assessment Guide](https://www.gao.gov/products/gao-20-195g) describes comprehensive, well-documented, accurate, and credible estimates and includes risk and uncertainty analysis.
- [FHWA cost-estimating guidance](https://www.fhwa.dot.gov/majorprojects/cost_estimating/guidance.cfm) recommends quantifying uncertainty, documenting assumptions, expressing early estimates as ranges or confidence levels, and avoiding false precision.
- [FHWA contingency guidance](https://www.fhwa.dot.gov/majorprojects/financial_plans/contingency_fund.cfm) identifies probability, severity, and expected value as useful risk variables and distinguishes construction, design, management, and specialized contingencies.
- [HM Treasury optimism-bias guidance](https://www.gov.uk/government/publications/green-book-supplementary-guidance-optimism-bias) recommends empirically based adjustments from past or similar projects and reducing adjustments as risks are demonstrably mitigated.

The MVP coefficients are original starter assumptions informed by these principles. They are not official coefficients and should not be presented as such.

