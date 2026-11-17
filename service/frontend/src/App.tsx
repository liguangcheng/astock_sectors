import { useCallback, useEffect, useState } from 'react';
import { api } from './api';
import type { VersionInfo } from './types';
import Overview from './pages/Overview';
import Industry from './pages/Industry';

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

type Route = { page: 'overview' } | { page: 'industry'; code: string };

function parseHash(): Route {
  const h = window.location.hash.replace(/^#\/?/, '');
  const m = h.match(/^industry\/(\d{6})(?:\?[^\s]*)?$/);
  return m ? { page: 'industry', code: m[1] } : { page: 'overview' };
}

export default function App() {
  const [route, setRoute] = useState<Route>(parseHash);
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const onHash = () => setRoute(parseHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  const go = useCallback((code: string) => {
    window.location.hash = `#/industry/${code}`;
  }, []);
  const back = useCallback(() => {
    window.location.hash = '#/';
  }, []);

  const loadVersion = useCallback(async () => {
    try {
      const v = await api.version();
      setVersion(v);
      return v;
    } catch {
      return null;
    }
  }, []);

  const runSync = useCallback(
    async (trigger: 'page' | 'manual') => {
      setSyncing(true);
      setSyncMsg(trigger === 'page' ? '检测到新交易日，正在同步…' : '正在同步最新数据…');
      try {
        const { jobId } = await api.sync();
        for (let i = 0; i < 160; i += 1) {
          await sleep(1500);
          const job = await api.syncJob(jobId);
          if (job.status === 'done') {
            setSyncMsg(`同步完成：新增 ${job.addedRows ?? 0} 行${job.rebuilt ? `，重建 ${job.rebuilt} 只` : ''}`);
            setRefreshKey((k) => k + 1);
            break;
          }
          if (job.status === 'failed') {
            setSyncMsg(`同步失败：${job.error ?? job.message ?? '未知错误'}`);
            break;
          }
          if (job.total) setSyncMsg(`同步中 ${job.done ?? 0}/${job.total} 只…`);
        }
      } catch (e) {
        setSyncMsg(`同步失败：${String(e)}`);
      } finally {
        setSyncing(false);
        await loadVersion();
      }
    },
    [loadVersion],
  );

  useEffect(() => {
    let alive = true;
    (async () => {
      const v = await loadVersion();
      if (!alive || !v) return;
      // 页面刷新时：若有新交易日且本会话未自动同步过，自动补数
      if (v.needsRefresh && !sessionStorage.getItem('astock-auto-sync')) {
        sessionStorage.setItem('astock-auto-sync', '1');
        await runSync('page');
      }
    })();
    return () => {
      alive = false;
    };
  }, [loadVersion, runSync]);

  useEffect(() => {
    const onFocus = () => {
      loadVersion();
    };
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [loadVersion]);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand" onClick={back} role="button" tabIndex={0}>
          <span className="dot" />
          A股行业龙头 · 月度股价
        </div>
        <div className="top-right">
          <span className="meta">
            数据截至 <b>{version?.lastTradeDate ?? '—'}</b>
            {version?.lastSyncAt ? <span className="muted"> · 上次同步 {version.lastSyncAt.slice(5, 16)}</span> : null}
          </span>
          <button className="btn" disabled={syncing} onClick={() => runSync('manual')}>
            {syncing ? '同步中…' : '同步最新数据'}
          </button>
        </div>
      </header>

      {syncMsg ? <div className={`banner ${syncing ? '' : 'done'}`}>{syncMsg}</div> : null}

      <main>
        {route.page === 'overview' ? (
          <Overview refreshKey={refreshKey} onOpen={go} />
        ) : (
          <Industry code={route.code} refreshKey={refreshKey} onBack={back} />
        )}
      </main>

      <footer className="footer">
        数据来源：申万宏源研究所（行业分类与权重）· baostock（前复权日线）　|　
        本地服务 127.0.0.1:3999　|　仅供研究参考，不构成投资建议
      </footer>
    </div>
  );
}
