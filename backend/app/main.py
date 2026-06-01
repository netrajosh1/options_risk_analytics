from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .services.finance import fetch_option_chain, black_scholes, calculate_portfolio_risk

app = FastAPI(title='Options Trading & Risk Analytics API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

class BlackScholesRequest(BaseModel):
    spot: float
    strike: float
    rate: float
    sigma: float
    time_to_expiry: float
    option_type: str = 'call'

class OptionLeg(BaseModel):
    ticker: str
    option_type: str
    quantity: int
    strike: float
    expiration: str

class PortfolioRequest(BaseModel):
    legs: list[OptionLeg]

@app.get('/api/ping')
def ping():
    return {'status': 'ok'}

@app.get('/api/option_chain')
def option_chain(ticker: str = Query(..., min_length=1)):
    try:
        data = fetch_option_chain(ticker)
        return data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post('/api/black_scholes')
def black_scholes_endpoint(params: BlackScholesRequest):
    try:
        result = black_scholes(
            spot=params.spot,
            strike=params.strike,
            rate=params.rate,
            sigma=params.sigma,
            time_to_expiry=params.time_to_expiry,
            option_type=params.option_type
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post('/api/portfolio_risk')
def portfolio_risk(request: PortfolioRequest):
    try:
        analysis = calculate_portfolio_risk(request.legs)
        return analysis
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
