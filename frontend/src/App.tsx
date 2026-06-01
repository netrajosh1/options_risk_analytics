import { useEffect, useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const defaultTicker = 'AAPL';

interface OptionRow {
  contractSymbol: string;
  strike: number;
  lastPrice: number;
  bid: number;
  ask: number;
  impliedVolatility: number;
  expiration: string;
  type: string;
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
  rho: number;
}

interface Greeks {
  delta: number;
  gamma: number;
  vega: number;
  theta: number;
  rho: number;
}

function App() {
  const [ticker, setTicker] = useState(defaultTicker);
  const [chain, setChain] = useState<OptionRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [greeks, setGreeks] = useState<Greeks | null>(null);
  const [surfaceData, setSurfaceData] = useState({ x: [] as number[], y: [] as string[], z: [] as number[][] });

  useEffect(() => {
    fetchOptionChain(defaultTicker);
  }, []);

  const fetchOptionChain = async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/option_chain?ticker=${encodeURIComponent(symbol)}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Unable to fetch option chain');
      setChain(data.options || []);
      setGreeks(data.portfolioGreeks ?? null);
      setSurfaceData(buildSurface(data.options || []));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setChain([]);
      setGreeks(null);
      setSurfaceData({ x: [], y: [], z: [] });
    } finally {
      setLoading(false);
    }
  };

  const buildSurface = (options: OptionRow[]) => {
    const expirations = Array.from(new Set(options.map((o) => o.expiration))).sort();
    const strikes = Array.from(new Set(options.map((o) => o.strike))).sort((a, b) => a - b);
    const matrix = expirations.map((exp) => {
      return strikes.map((strike) => {
        const match = options.find((row) => row.expiration === exp && row.strike === strike && row.type === 'call');
        return match ? match.impliedVolatility : NaN;
      });
    });
    return { x: strikes, y: expirations, z: matrix };
  };

  const aggregated = useMemo(() => {
    if (!greeks) return null;
    return [
      { label: 'Delta', value: greeks.delta },
      { label: 'Gamma', value: greeks.gamma },
      { label: 'Vega', value: greeks.vega },
      { label: 'Theta', value: greeks.theta },
      { label: 'Rho', value: greeks.rho }
    ];
  }, [greeks]);

  return (
    <div className="app-shell">
      <header className="header">
        <div>
          <h1>Options Trading & Risk Analytics</h1>
          <p>Analyze live option chains, Black-Scholes pricing, Greeks, and portfolio risk.</p>
        </div>
        <div>
          <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} placeholder="Ticker" />
          <button onClick={() => fetchOptionChain(ticker)} disabled={loading || !ticker.trim()}>
            {loading ? 'Loading…' : 'Fetch Chain'}
          </button>
        </div>
      </header>

      {error && <div className="card" style={{ borderColor: '#f87171' }}>{error}</div>}

      <div className="grid grid-2" style={{ marginTop: 24 }}>
        <section className="card">
          <h2>Top Option Chain</h2>
          <table>
            <thead>
              <tr>
                <th>Strike</th>
                <th>Type</th>
                <th>Last</th>
                <th>IV</th>
                <th>Delta</th>
                <th>Gamma</th>
              </tr>
            </thead>
            <tbody>
              {chain.slice(0, 12).map((row) => (
                <tr key={row.contractSymbol}>
                  <td>{row.strike.toFixed(2)}</td>
                  <td>{row.type}</td>
                  <td>{row.lastPrice.toFixed(2)}</td>
                  <td>{(row.impliedVolatility * 100).toFixed(1)}%</td>
                  <td>{row.delta.toFixed(3)}</td>
                  <td>{row.gamma.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="card">
          <h2>Portfolio Greeks</h2>
          {aggregated ? (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
              {aggregated.map((item) => (
                <li key={item.label} style={{ marginBottom: 10 }}>
                  <strong>{item.label}:</strong> {item.value.toFixed(4)}
                </li>
              ))}
            </ul>
          ) : (
            <p>No Greeks available yet.</p>
          )}
        </section>
      </div>

      <section className="card" style={{ marginTop: 24 }}>
        <h2>Implied Volatility Surface</h2>
        <Plot
          data={[
            {
              x: surfaceData.x,
              y: surfaceData.y,
              z: surfaceData.z,
              type: 'surface',
              colorscale: 'Portland'
            }
          ]}
          layout={{
            title: 'IV Surface',
            autosize: true,
            scene: {
              xaxis: { title: 'Strike' },
              yaxis: { title: 'Expiration' },
              zaxis: { title: 'Implied Volatility' }
            },
            margin: { l: 50, r: 50, b: 40, t: 50 }
          }}
          style={{ width: '100%', minHeight: '520px' }}
        />
      </section>
    </div>
  );
}

export default App;
