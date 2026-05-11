# samse-expense

Anomaly detection agent for corporate expense reports.

## What it does

The tool analyzes a set of expense entries and flags the ones that look suspicious. It combines rule-based checks with a machine learning model, then produces an HTML report with a plain-language explanation of each anomaly.

## How it works

Two detection layers run in parallel:

**Rule-based checks**
- Amounts above defined thresholds
- Duplicate entries (same amount, same date, same category)
- Expenses submitted outside business hours or on weekends
- Missing required fields

**Machine learning**
- Isolation Forest, an unsupervised algorithm that detects statistical outliers
- No labeled data required — it learns what "normal" looks like from the data itself

Results are merged and ranked by confidence. Claude (via OpenRouter) then writes a short narrative explanation for each flagged item, making the report readable by non-technical finance staff.

## Stack

- Python
- scikit-learn (Isolation Forest)
- Claude (via OpenRouter) for report narration
- HTML report output

## Author

Sonam — [github.com/scrumier](https://github.com/scrumier)
