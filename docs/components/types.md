The following types of evaluation criteria are defined.

```python exec="true" session="index" showcode="false"
import pandas as pd
from scenario_evaluation_criteria import load_criteria

criteria_types = load_criteria("criteria-types")


def _format_outcomes(outcomes):
    return "<br>".join(f"`{key}`: {desc}" for key, desc in outcomes.items())


rows = [
    {
        "type": f"`{name}`",
        "description": spec["description"],
        "evaluation outcomes": _format_outcomes(spec["evaluation_outcomes"]),
    }
    for name, spec in criteria_types.items()
]

print(
    pd.DataFrame(rows)
    .rename(columns=lambda x: x.upper())
    .to_markdown(index=False)
)
```
