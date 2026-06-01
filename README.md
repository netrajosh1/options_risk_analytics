# Options Trading & Risk Analytics Platform

A full-stack prototype for live option chain analysis, Black-Scholes pricing, Greeks visualization, Monte Carlo simulation, and portfolio risk management.

## Tech stack

- Frontend: React, TypeScript, Vite, Plotly
- Backend: FastAPI, Python, NumPy, SciPy, pandas, yfinance
- Data: Yahoo Finance

## Features

- Enter stock tickers and fetch option chain data
- Calculate theoretical option prices using Black-Scholes
- Visualize Greeks: Delta, Gamma, Vega, Theta, Rho
- Run Monte Carlo simulations for option price distributions
- Compare theoretical prices to market prices
- Build a volatility surface for strikes and expirations
- Compute portfolio aggregated Greeks and VaR

## Run locally

### Backend

```bash
cd options-risk-analytics-platform/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd options-risk-analytics-platform/frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

## Notes

- This project is designed to highlight quantitative finance, mathematical modeling, and software engineering.
- Replace the data source or add API keys if you want Polygon / Alpaca support.
