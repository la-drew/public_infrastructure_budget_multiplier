# Contributing

Thank you for helping make infrastructure uncertainty more transparent.

## Before opening a pull request

1. Open an issue describing the decision problem, proposed behavior, and any evidence behind a model change.
2. Keep the core usable without paid services or proprietary data.
3. Add tests for behavioral changes.
4. Document new coefficients, units, sources, assumptions, and limitations.
5. Run `PYTHONPATH=src python -m unittest discover -s tests -v`.

Model changes need extra care. A coefficient should not be presented as generally applicable because it performed well for one organization or asset class. Prefer configurable calibration, report out-of-sample performance, and retain model-version metadata.

## Development

```bash
python -m pip install -e .
public_infrastructure_budget_multiplier
```

The interface is plain HTML, CSS, and JavaScript in `web/`. The model and dependency-free server are in `src/public_infrastructure_budget_multiplier/`.

## Pull requests

Keep pull requests focused. Include:

- a short user-facing summary;
- tests performed;
- before/after screenshots for interface changes; and
- calibration or validation evidence for model changes.

