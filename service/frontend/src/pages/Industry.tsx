import { useEffect, useMemo, useState } from 'react';
import { api } from '../api';
import type { IndustryDetailResponse, PricedSeries } from '../types';
import LineChart from '../components/LineChart';

interface Props {
  code: string;
  refreshKey: number;
  onBack: () => void;
}

const pct = (v: number | null) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`);
const num = (v: number | null | undefined, d = 2) => (v == null ? '—' : v.toFixed(d));

export default function Industry({ code, refreshKey, onBack }: Props) {
  const [data, setData] = useState<IndustryDetailResponse | null>(null);
  const [mode, setMode] = useState<'price' | 'norm'>(() =>
    window.location.hash.includes('norm=1') ? 'norm' : 'price',
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setData(null);
    setError(null);
    api
      .industry(code)
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(String(e)));
    return () => {
      alive = false;
    };
  }, [code, refreshKey]);

  const chartSeries: PricedSeries[] = useMemo(() => {
    if (!data) return [];
    const stocks: PricedSeries[] = data.leaders.map((l) => ({
      code: l.code,
      name: l.name,
      isBenchmark: false,
      weight: l.weight,
      metrics: l.metrics,
      series: l.series,
    }));
    const bench: PricedSeries = {
      code: '000300',
      name: data.benchmark.name,
      isBenchmark: true,
      weight: null,
      metrics: data.benchmark.metrics,
      series: data.benchmark.series,
    };
    return [...stocks, bench];
  }, [data]);

  const months = useMemo(
    () => (chartSeries[0]?.series ?? []).map((p) => p.month),
    [chartSeries],
  );

  if (error) return <div className="error">加载失败：{error}</div>;
  if (!data) return <div className="loading">加载中…</div>;

  const benchCum = data.benchmark.metrics.cum_return;
  const rel = data.avgCumReturn == null || benchCum == null ? null : data.avgCumReturn - benchCum;

  return (
    <div className="page">
      <button className="back" onClick={onBack}>
        ← 返回总览
      </button>

      <section className="card">
        <div className="card-head">
          <div>
            <h2>
              {data.name} <span className="muted">（{data.code} · {data.stockCount} 只成分股）</span>
            </h2>
            <p className="muted small">
              龙头前五等权平均 {pct(data.avgCumReturn)}，沪深300 {pct(benchCum)}，
              {rel == null ? '' : rel >= 0 ? `跑赢 ${rel.toFixed(1)} 个百分点` : `跑输 ${Math.abs(rel).toFixed(1)} 个百分点`}
              {mode === 'price' ? '　·　绝对价格模式下不叠加沪深300（量级不同）' : ''}
            </p>
          </div>
          <div className="seg">
            <button className={mode === 'price' ? 'active' : ''} onClick={() => setMode('price')}>
              绝对价格
            </button>
            <button className={mode === 'norm' ? 'active' : ''} onClick={() => setMode('norm')}>
              归一化（{data.baseMonth}=100）
            </button>
          </div>
        </div>
        <LineChart months={months} series={chartSeries} mode={mode} />
      </section>

      <section className="card">
        <div className="card-head">
          <h2>龙头指标</h2>
          <span className="muted">基期 {data.baseMonth} 月末 · 最新 {data.benchmark.metrics.last_month}</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>排名</th>
                <th>股票</th>
                <th>申万权重</th>
                <th>基期价</th>
                <th>最新价</th>
                <th>区间涨跌</th>
                <th>年化收益</th>
                <th>最大回撤</th>
                <th>年化波动</th>
                <th>最佳月</th>
                <th>最差月</th>
              </tr>
            </thead>
            <tbody>
              {data.leaders.map((l, i) => (
                <tr key={l.code}>
                  <td>{i === 0 ? <span className="tag">龙头</span> : `No.${i + 1}`}</td>
                  <td className="name">
                    {l.name} <span className="muted">{l.code}</span>
                  </td>
                  <td>{l.weight.toFixed(2)}%</td>
                  <td>{num(l.metrics.base_close)}</td>
                  <td>{num(l.metrics.last_close)}</td>
                  <td className={(l.metrics.cum_return ?? 0) >= 0 ? 'up' : 'down'}>{pct(l.metrics.cum_return)}</td>
                  <td>{pct(l.metrics.cagr)}</td>
                  <td className="down">{num(l.metrics.mdd, 1)}%</td>
                  <td>{num(l.metrics.annual_vol, 1)}%</td>
                  <td>
                    {l.metrics.best ? `${l.metrics.best.month.slice(2)} ${pct(l.metrics.best.ret)}` : '—'}
                  </td>
                  <td>
                    {l.metrics.worst ? `${l.metrics.worst.month.slice(2)} ${pct(l.metrics.worst.ret)}` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
