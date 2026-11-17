import { useEffect, useState } from 'react';
import { api } from '../api';
import type { OverviewResponse } from '../types';
import OverviewBar from '../components/OverviewBar';

interface Props {
  refreshKey: number;
  onOpen: (code: string) => void;
}

const pct = (v: number | null) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`);

export default function Overview({ refreshKey, onOpen }: Props) {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setError(null);
    api
      .overview()
      .then((d) => alive && setData(d))
      .catch((e) => alive && setError(String(e)));
    return () => {
      alive = false;
    };
  }, [refreshKey]);

  if (error) return <div className="error">加载失败：{error}</div>;
  if (!data) return <div className="loading">加载中…</div>;

  const items = [...data.industries].sort(
    (a, b) => (b.leaderCumReturn ?? -999) - (a.leaderCumReturn ?? -999),
  );
  const best = items[0];
  const worst = items[items.length - 1];

  return (
    <div className="page">
      <section className="kpis">
        <div className="kpi">
          <div className="kpi-label">行业板块</div>
          <div className="kpi-value">{data.industries.length}</div>
          <div className="kpi-sub">申万一级行业</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">龙头股</div>
          <div className="kpi-value">{data.industries.length * 5}</div>
          <div className="kpi-sub">每行业权重前五</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">同期沪深300</div>
          <div className={`kpi-value ${(data.benchmark.cumReturn ?? 0) >= 0 ? 'up' : 'down'}`}>
            {pct(data.benchmark.cumReturn)}
          </div>
          <div className="kpi-sub">{data.baseMonth} 末 → 最新</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">最强 / 最弱板块</div>
          <div className="kpi-value small">
            {best?.name} {pct(best?.leaderCumReturn ?? null)}
          </div>
          <div className="kpi-sub">
            {worst?.name} {pct(worst?.leaderCumReturn ?? null)}
          </div>
        </div>
      </section>

      <section className="card">
        <div className="card-head">
          <h2>行业龙头区间累计涨跌幅</h2>
          <span className="muted">点击柱状图或下方卡片查看该行业五只龙头月度走势</span>
        </div>
        <OverviewBar items={data.industries} benchmark={data.benchmark.cumReturn} onSelect={onOpen} />
      </section>

      <section className="grid">
        {items.map((x) => (
          <button className="ind-card" key={x.code} onClick={() => onOpen(x.code)}>
            <div className="ind-card-top">
              <span className="ind-name">{x.name}</span>
              <span className="ind-count">{x.stockCount} 只</span>
            </div>
            <div className="ind-leader">
              <span>{x.leader?.name ?? '—'}</span>
              <span className="ind-weight">{x.leader ? `${x.leader.weight.toFixed(1)}%` : ''}</span>
            </div>
            <div className="ind-nums">
              <span className={((x.leaderCumReturn ?? 0) >= 0 ? 'up' : 'down')}>{pct(x.leaderCumReturn)}</span>
              <span className="muted">前五均值 {pct(x.avgCumReturn)}</span>
            </div>
          </button>
        ))}
      </section>
    </div>
  );
}
