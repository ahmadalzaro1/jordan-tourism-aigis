# AutoResearch Program — Jordan Tourism AI-GIS

## Objective

Autonomously improve the analytics engine by:
1. Reading the tourism data
2. Generating a hypothesis about what analytics would be useful
3. Implementing the analytics
4. Evaluating whether it improves the system
5. Keeping if it helps, discarding if not
6. Repeating

## Rules

1. **Only modify files in `backend/app/analytics/`** and `backend/app/api/routes/analytics.py`
2. **Never break existing functionality** — run `evaluate.py` before and after each change
3. **Each experiment must produce a measurable output** — a number that can be compared
4. **Document every experiment** in `docs/autoresearch_log.md`
5. **Quality score must improve or stay the same** — if it drops, revert the change

## Evaluation Metric

The system is scored on a composite **Analytics Quality Score** (0-100):

| Component | Weight | What It Measures |
|-----------|--------|-----------------|
| Data coverage | 20% | How much of the data is used by analytics |
| Insight depth | 20% | Number of distinct insights generated |
| Forecast accuracy | 20% | MAPE (lower = better) |
| Correlation discovery | 15% | Number of statistically significant correlations found |
| Actionability | 15% | Can a policymaker use the output to make a decision? |
| Reproducibility | 10% | Same input = same output |

## Experiment Categories

Each experiment falls into one of these:

### Category 1: New Indicator
- Propose a new indicator formula
- Implement it
- Evaluate if it adds insight depth

### Category 2: Correlation Discovery
- Test a new variable pair for correlation
- If significant (|r| > 0.4), add to the indicator set

### Category 3: Segmentation
- Try grouping data by a new dimension (season, cluster, hotel class)
- Evaluate if segmentation reveals patterns hidden in aggregate data

### Category 4: Forecast Enhancement
- Try a new forecast configuration (different order, different features)
- Evaluate if MAPE improves

### Category 5: Simulation Refinement
- Add a new scenario type or refine existing ones
- Evaluate if simulation produces more actionable outputs

### Category 6: Data Quality
- Discover a data quality issue
- Add validation or cleaning step
- Evaluate if data quality score improves

## How to Run

```bash
# Single experiment
cd backend && python3 scripts/run_experiment.py

# Continuous loop (runs until stopped)
cd backend && python3 scripts/autoresearch_loop.py

# Evaluate current state
cd backend && python3 scripts/evaluate.py
```

## Log Format

Each experiment in `docs/autoresearch_log.md`:

```
## Experiment #N — [Category] [Description]
**Date:** YYYY-MM-DD HH:MM
**Hypothesis:** [What we think will happen]
**Changes:** [Files modified, what changed]
**Before score:** [X/100]
**After score:** [Y/100]
**Result:** KEPT / DISCARDED
**Learning:** [What we learned]
```
