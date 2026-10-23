# AI-Based Financial Planning

A simple base project with four modules:

1. **Goal Planner** - monthly SIP needed for an inflation-adjusted goal.
2. **Retirement Planner** - corpus needed vs. projected, and the extra SIP to close the gap.
3. **Expense Forecast** - Linear Regression predicts the next months of spending (with a range).
4. **Health & Allocation** - 0-100 financial health score, emergency fund target, asset allocation.

## Run
```
pip install -r requirements.txt
streamlit run app.py
```

## Files
- `planner.py` - all logic
- `app.py` - Streamlit interface

## Next steps
Use real bank-statement data for forecasting, try ARIMA/Prophet, add Monte Carlo simulation of returns, or an LLM chat advisor.

*Educational use only; not financial advice.*
