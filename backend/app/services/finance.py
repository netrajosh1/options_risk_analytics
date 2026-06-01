from datetime import datetime
import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
from scipy.optimize import brentq

RISK_FREE_RATE = 0.05

def black_scholes(spot: float, strike: float, rate: float, sigma: float, time_to_expiry: float, option_type: str = 'call') -> dict:
    if time_to_expiry <= 0 or sigma <= 0:
        raise ValueError('Time to expiry and sigma must be positive')

    d1 = (np.log(spot / strike) + (rate + 0.5 * sigma ** 2) * time_to_expiry) / (sigma * np.sqrt(time_to_expiry))
    d2 = d1 - sigma * np.sqrt(time_to_expiry)
    if option_type.lower() == 'call':
        price = spot * stats.norm.cdf(d1) - strike * np.exp(-rate * time_to_expiry) * stats.norm.cdf(d2)
        delta = stats.norm.cdf(d1)
    else:
        price = strike * np.exp(-rate * time_to_expiry) * stats.norm.cdf(-d2) - spot * stats.norm.cdf(-d1)
        delta = stats.norm.cdf(d1) - 1

    gamma = stats.norm.pdf(d1) / (spot * sigma * np.sqrt(time_to_expiry))
    vega = spot * stats.norm.pdf(d1) * np.sqrt(time_to_expiry)
    theta = -spot * stats.norm.pdf(d1) * sigma / (2 * np.sqrt(time_to_expiry))
    if option_type.lower() == 'call':
        theta -= rate * strike * np.exp(-rate * time_to_expiry) * stats.norm.cdf(d2)
    else:
        theta += rate * strike * np.exp(-rate * time_to_expiry) * stats.norm.cdf(-d2)
    rho = strike * time_to_expiry * np.exp(-rate * time_to_expiry) * stats.norm.cdf(d2 if option_type.lower() == 'call' else -d2)

    return {
        'price': float(price),
        'delta': float(delta),
        'gamma': float(gamma),
        'vega': float(vega / 100),
        'theta': float(theta / 365),
        'rho': float(rho / 100)
    }


def implied_volatility(spot: float, strike: float, rate: float, time_to_expiry: float, market_price: float, option_type: str = 'call') -> float:
    def objective(sigma):
        return black_scholes(spot, strike, rate, sigma, time_to_expiry, option_type)['price'] - market_price

    lower, upper = 1e-6, 5.0
    try:
        return brentq(objective, lower, upper, maxiter=200)
    except ValueError:
        return np.nan


def fetch_option_chain(ticker: str) -> dict:
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info
    df_spot = ticker_obj.history(period='2d')
    if df_spot.empty:
        raise RuntimeError('Unable to fetch quote data for ' + ticker)

    spot_price = float(df_spot['Close'].iloc[-1])
    expirations = ticker_obj.options[:5]
    options_data = []

    for expiry in expirations:
        calls = ticker_obj.option_chain(expiry).calls
        puts = ticker_obj.option_chain(expiry).puts
        for kind, df in [('call', calls), ('put', puts)]:
            for _, row in df.iterrows():
                time_to_expiry = max((datetime.strptime(expiry, '%Y-%m-%d') - datetime.utcnow()).days / 365.0, 1e-4)
                implied_vol = implied_volatility(
                    spot_price,
                    float(row['strike']),
                    RISK_FREE_RATE,
                    time_to_expiry,
                    float(row['lastPrice'] if row['lastPrice'] > 0 else row['bid']),
                    kind
                )
                greek = black_scholes(
                    spot=spot_price,
                    strike=float(row['strike']),
                    rate=RISK_FREE_RATE,
                    sigma=implied_vol if not np.isnan(implied_vol) else 0.25,
                    time_to_expiry=time_to_expiry,
                    option_type=kind
                )
                options_data.append({
                    'contractSymbol': row['contractSymbol'],
                    'strike': float(row['strike']),
                    'lastPrice': float(row['lastPrice']),
                    'bid': float(row['bid']),
                    'ask': float(row['ask']),
                    'impliedVolatility': float(implied_vol if not np.isnan(implied_vol) else 0.0),
                    'expiration': expiry,
                    'type': kind,
                    'delta': greek['delta'],
                    'gamma': greek['gamma'],
                    'theta': greek['theta'],
                    'vega': greek['vega'],
                    'rho': greek['rho']
                })

    portfolio_greeks = {
        'delta': float(np.nansum([o['delta'] for o in options_data])),
        'gamma': float(np.nansum([o['gamma'] for o in options_data])),
        'vega': float(np.nansum([o['vega'] for o in options_data])),
        'theta': float(np.nansum([o['theta'] for o in options_data])),
        'rho': float(np.nansum([o['rho'] for o in options_data]))
    }

    return {
        'ticker': ticker,
        'spot': spot_price,
        'options': options_data,
        'portfolioGreeks': portfolio_greeks
    }


def calculate_portfolio_risk(legs: list[dict]) -> dict:
    total_delta = 0.0
    total_gamma = 0.0
    total_vega = 0.0

    for leg in legs:
        ticker_obj = yf.Ticker(leg['ticker'])
        expiry = leg['expiration']
        chain = ticker_obj.option_chain(expiry)
        df = chain.calls if leg['option_type'].lower() == 'call' else chain.puts
        row = df[df['strike'] == leg['strike']].head(1)
        if row.empty:
            continue
        spot_price = float(ticker_obj.history(period='2d')['Close'].iloc[-1])
        time_to_expiry = max((datetime.strptime(expiry, '%Y-%m-%d') - datetime.utcnow()).days / 365.0, 1e-4)
        implied_vol = implied_volatility(
            spot_price,
            leg['strike'],
            RISK_FREE_RATE,
            time_to_expiry,
            float(row['lastPrice'].iloc[0]),
            leg['option_type']
        )
        greek = black_scholes(
            spot=spot_price,
            strike=leg['strike'],
            rate=RISK_FREE_RATE,
            sigma=implied_vol if not np.isnan(implied_vol) else 0.25,
            time_to_expiry=time_to_expiry,
            option_type=leg['option_type']
        )
        multiplier = float(leg.get('quantity', 1))
        total_delta += greek['delta'] * multiplier
        total_gamma += greek['gamma'] * multiplier
        total_vega += greek['vega'] * multiplier

    var = abs(total_delta) * 0.02
    return {
        'netDelta': total_delta,
        'netGamma': total_gamma,
        'netVega': total_vega,
        'valueAtRisk': var
    }
