import { useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowDownRight, ArrowUpRight, CalendarDays, CheckCircle2,
  Clock3, Database, RefreshCw, Wind, Zap
} from "lucide-react";
import {
  CartesianGrid, Legend, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis
} from "recharts";
import { fetchAnalysis } from "./api";

const fmt = (value, digits = 0) =>
  value == null || !Number.isFinite(Number(value))
    ? "—"
    : Number(value).toLocaleString("en-GB", {
        maximumFractionDigits: digits,
        minimumFractionDigits: digits
      });

const metricCards = [
  { key: "mae_mw", label: "Mean absolute error", unit: "MW", icon: Activity, digits: 1 },
  { key: "rmse_mw", label: "Root mean squared error", unit: "MW", icon: Zap, digits: 1 },
  { key: "bias_mw", label: "Forecast bias", unit: "MW", icon: ArrowUpRight, digits: 1 },
  { key: "wape_pct", label: "Weighted absolute error", unit: "%", icon: Wind, digits: 2 }
];

export default function App() {
  const [month, setMonth] = useState("2026-01");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadData(selectedMonth = month) {
    setLoading(true);
    setError("");
    try {
      const result = await fetchAnalysis(selectedMonth);
      setData(result);
    } catch (err) {
      setError(err.message || "Unable to load analysis.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData(month);
  }, [month]);

  const chartData = useMemo(() => {
    if (!data?.rows) return [];
    return data.rows.map((row) => ({
      ...row,
      time: new Date(row.start_time).toLocaleString("en-GB", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Europe/London"
      })
    }));
  }, [data]);

  const quality = data?.data_quality;
  const metrics = data?.metrics;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Wind size={22} /></div>
          <div>
            <strong>WIND<span>IQ</span></strong>
            <small>FORECAST INTELLIGENCE</small>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active"><Activity size={17} /> Overview</div>
        <div className="nav-item"><Wind size={17} /> Wind generation</div>
        <div className="nav-item"><Database size={17} /> Data quality</div>

        <div className="sidebar-bottom">
          <div className="source-status"><span className="status-dot" /> BMRS data source</div>
          <p>Decision-support analytics for UK wind generation.</p>
          <span className="version">PILOT · V1.0</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumbs">Workspace <span>/</span> <strong>Overview</strong></div>
          <div className="topbar-right"><span className="live-dot" /> Live API connection</div>
        </header>

        <section className="page-heading">
          <div>
            <div className="eyebrow"><span className="eyebrow-line" /> ENERGY MARKET ANALYTICS</div>
            <h1>Wind forecast <span>intelligence.</span></h1>
            <p className="subtitle">Evaluate day-ahead wind generation forecasts against observed output.</p>
          </div>
          <div className="controls">
            <label htmlFor="month"><CalendarDays size={16} /> Decision month</label>
            <input
              id="month"
              type="month"
              value={month}
              onChange={(event) => setMonth(event.target.value)}
              max="2026-12"
            />
            <button onClick={() => loadData()} disabled={loading} aria-label="Refresh analysis">
              <RefreshCw size={16} className={loading ? "spin" : ""} />
              Refresh
            </button>
          </div>
        </section>

        {error && (
          <div className="error-banner">
            <strong>Unable to load analysis.</strong>
            <span>{error}</span>
            <button onClick={() => loadData()}>Try again</button>
          </div>
        )}

        <section className="section-head">
          <div><h2>Performance overview</h2><p>Forecast errors for the selected decision cohort</p></div>
          <div className="period-pill"><Clock3 size={14} /> Cutoff: {data?.cutoff || "23:59"} UK time</div>
        </section>

        <section className="metric-grid">
          {metricCards.map(({ key, label, unit, icon: Icon, digits }) => {
            const value = metrics?.[key];
            const positiveBias = key === "bias_mw" && Number(value) > 0;
            return (
              <article className="metric-card" key={key}>
                <div className="metric-top">
                  <span>{label}</span>
                  <div className="metric-icon"><Icon size={17} /></div>
                </div>
                <div className="metric-value">
                  {loading ? "…" : fmt(value, digits)}
                  <small>{unit}</small>
                </div>
                <div className="metric-foot">
                  {key === "bias_mw" ? (
                    <><ArrowUpRight size={14} className={positiveBias ? "warm" : ""} /> {positiveBias ? "Over-forecast on average" : "Average signed error"}</>
                  ) : key === "wape_pct" ? (
                    <>Error relative to total actual output</>
                  ) : key === "mae_mw" ? (
                    <>Average absolute deviation</>
                  ) : (
                    <>Penalises larger forecast errors</>
                  )}
                </div>
              </article>
            );
          })}
        </section>

        <section className="content-grid">
          <article className="panel chart-panel">
            <div className="panel-heading">
              <div><h2>Forecast vs actual</h2><p>Generation output · MW · UK local time</p></div>
              <div className="chart-legend"><span className="legend-forecast" /> Forecast <span className="legend-actual" /> Actual</div>
            </div>
            {loading ? <div className="empty-state">Loading generation data…</div> :
              chartData.length ? (
                <div className="chart-wrap">
                  <ResponsiveContainer width="100%" height={310}>
                    <LineChart data={chartData} margin={{ top: 12, right: 10, left: 4, bottom: 2 }}>
                      <CartesianGrid strokeDasharray="3 5" stroke="#e8edf3" vertical={false} />
                      <XAxis dataKey="time" tick={{ fontSize: 10, fill: "#7c8798" }} tickLine={false} axisLine={false} interval={Math.max(0, Math.floor(chartData.length / 8) - 1)} />
                      <YAxis tick={{ fontSize: 11, fill: "#7c8798" }} tickLine={false} axisLine={false} width={62} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
                      <Tooltip
                        contentStyle={{ border: "1px solid #e4e9f0", borderRadius: 12, fontSize: 12 }}
                        formatter={(value, name) => [`${fmt(value, 1)} MW`, name === "forecast_mw" ? "Forecast" : "Actual"]}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="forecast_mw" name="Forecast" stroke="#5367e8" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                      <Line type="monotone" dataKey="actual_mw" name="Actual" stroke="#14a58b" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : <div className="empty-state">No matched periods available for this month.</div>}
            <div className="chart-footer">
              <span><span className="footer-dot forecast-dot" /> Latest eligible day-ahead forecast</span>
              <span><span className="footer-dot actual-dot" /> Observed WIND generation</span>
            </div>
          </article>

          <article className="panel quality-panel">
            <div className="panel-heading">
              <div><h2>Data integrity</h2><p>Coverage and source diagnostics</p></div>
              <Database size={18} className="heading-icon" />
            </div>
            <div className="quality-status">
              <CheckCircle2 size={18} />
              <div><strong>{quality ? "Coverage checked" : "Awaiting data"}</strong><small>Expected timestamps compared with source records</small></div>
            </div>
            <div className="quality-list">
              <QualityRow label="Expected hourly periods" value={quality?.expected_periods_by_calendar_convention} />
              <QualityRow label="Matched periods" value={quality?.matched_periods} />
              <QualityRow label="Missing forecast timestamps" value={quality?.missing_forecast_periods} warning={quality?.missing_forecast_periods > 0} />
              <QualityRow label="Missing actual timestamps" value={quality?.missing_actual_periods} warning={quality?.missing_actual_periods > 0} />
              <QualityRow label="Forecast records received" value={quality?.forecast_records_received} />
              <QualityRow label="Eligible forecast records" value={quality?.eligible_forecast_records} />
              <QualityRow label="WIND actual records" value={quality?.actual_wind_records} />
            </div>
            <div className="quality-note">A complete timestamp match indicates coverage, not necessarily source completeness or compliance with official market deadlines.</div>
          </article>
        </section>

        <section className="panel table-panel">
          <div className="panel-heading">
            <div><h2>Evaluation periods</h2><p>Selected forecast and actual values for each matched interval</p></div>
            <span className="row-count">{fmt(metrics?.matched_periods)} periods</span>
          </div>
          <div className="table-scroll">
            <table>
              <thead><tr><th>Delivery start</th><th>Decision date</th><th>Published (UTC)</th><th>Forecast (MW)</th><th>Actual (MW)</th><th>Error (MW)</th></tr></thead>
              <tbody>
                {chartData.slice(0, 100).map((row) => (
                  <tr key={row.start_time}>
                    <td>{new Date(row.start_time).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "Europe/London" })}</td>
                    <td>{row.decision_date}</td>
                    <td>{new Date(row.publish_time).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" })}</td>
                    <td>{fmt(row.forecast_mw, 1)}</td>
                    <td>{fmt(row.actual_mw, 1)}</td>
                    <td className={row.error_mw > 0 ? "error-positive" : row.error_mw < 0 ? "error-negative" : ""}>
                      {row.error_mw > 0 ? <ArrowUpRight size={13} /> : row.error_mw < 0 ? <ArrowDownRight size={13} /> : null}
                      {fmt(row.error_mw, 1)}
                    </td>
                  </tr>
                ))}
                {!loading && chartData.length === 0 && <tr><td colSpan="6" className="empty-cell">No data to display.</td></tr>}
              </tbody>
            </table>
          </div>
          {chartData.length > 100 && <div className="table-footnote">Showing the first 100 of {fmt(chartData.length)} matched periods.</div>}
        </section>

        <footer className="footer">
          <div><span className="footer-brand">WINDIQ</span> · Decision-support prototype</div>
          <div>Source: Elexon BMRS · FUELHH & WINDFOR</div>
          <div>Method: forecast − actual · {data?.timezone || "Europe/London"}</div>
        </footer>
      </main>
    </div>
  );
}

function QualityRow({ label, value, warning = false }) {
  return (
    <div className="quality-row">
      <span>{label}</span>
      <strong className={warning ? "warning-text" : ""}>{value == null ? "—" : fmt(value)}</strong>
    </div>
  );
}
