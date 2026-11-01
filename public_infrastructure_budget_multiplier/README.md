# public_infrastructure_budget_multiplier

An explainable, dependency-free planning tool for estimating how far the cost and completion time of a public infrastructure project may vary from its current baseline.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-0b6b55) ![License: MIT](https://img.shields.io/badge/License-MIT-e96f42) ![Status: Alpha](https://img.shields.io/badge/status-alpha-3a70d6)

## What it does

- Models capital size, labor share, labor and material escalation, regulatory bodies, approvals, design maturity, site uncertainty, stakeholder complexity, and delivery method.
- Runs 8,000 seeded Monte Carlo scenarios and returns P10, P50, P80, and P90 cost and schedule outcomes.
- Shows probability of exceeding the estimate plus contingency.
- Ranks the largest modeled cost drivers.
- Saves up to 25 analyses locally for portfolio comparison and exports JSON or CSV.
- Uses no paid APIs, database, analytics, cookies, or third-party runtime packages.

> **Important:** This is a transparent planning aid, not a forecast, certified estimate, or substitute for a project-specific cost and schedule risk assessment. The included coefficients are starter priors. Calibrate them with completed-project forecast errors before using the results for decisions.

## Quick start

Requires Python 3.10 or newer.

```bash
git clone https://github.com/YOUR-ORG/public_infrastructure_budget_multiplier.git
cd public_infrastructure_budget_multiplier
python -m pip install -e .
public_infrastructure_budget_multiplier
```

Open <http://127.0.0.1:8000>. Nothing is sent to an external service.

You can also run without installing:

```bash
PYTHONPATH=src python -m public_infrastructure_budget_multiplier.server
```

## API

`POST /api/estimate` accepts a JSON object. Monetary inputs and outputs are in millions of the user's chosen currency.

```bash
curl http://127.0.0.1:8000/api/estimate \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Eastside Rapid Transit Extension",
    "project_type": "rail",
    "phase": "planning",
    "capital_cost": 1450,
    "duration_months": 84,
    "labor_share_percent": 42,
    "regulatory_bodies": 7,
    "approvals_required": 14,
    "approval_complexity": 4
  }'
```

See [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) for every field and [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for the model equations and assumptions.

## Repository structure

```text
public_infrastructure_budget_multiplier/
├── src/public_infrastructure_budget_multiplier/  # model and HTTP server
├── web/                 # accessible, responsive interface
├── tests/               # standard-library unit tests
├── data/                # fictional example projects
├── docs/                # model and field documentation
└── .github/workflows/   # continuous integration
```

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Evidence and design principles

The tool follows official guidance that early estimates should express uncertainty as ranges, explicitly identify and quantify risks, document assumptions, avoid false precision, and update estimates as the project matures:

- [GAO Cost Estimating and Assessment Guide (GAO-20-195G)](https://www.gao.gov/products/gao-20-195g)
- [FHWA Major Project Program Cost Estimating Guidance](https://www.fhwa.dot.gov/majorprojects/cost_estimating/guidance.cfm)
- [FHWA Contingency Fund Management for Major Projects](https://www.fhwa.dot.gov/majorprojects/financial_plans/contingency_fund.cfm)
- [HM Treasury Green Book: optimism bias guidance](https://www.gov.uk/government/publications/green-book-supplementary-guidance-optimism-bias)

These sources inform the method, not a claim that the starter coefficients reproduce any agency's historical data.

## Roadmap

- Import completed-project CSV data and fit organization-specific priors.
- Add jurisdiction-specific approval templates and review paths.
- Model correlated risk registers with owner, probability, impact, and mitigation.
- Add schedule-network inputs and time-dependent cash flow.
- Publish calibration diagnostics and backtesting reports.

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT. See [LICENSE](LICENSE).

