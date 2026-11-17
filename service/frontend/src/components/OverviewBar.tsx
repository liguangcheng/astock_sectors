import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { OverviewItem } from '../types';

interface Props {
  items: OverviewItem[];
  benchmark: number | null;
  height?: number;
  onSelect?: (code: string) => void;
}

export default function OverviewBar({ items, benchmark, height = 420, onSelect }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    const sorted = [...items].sort((a, b) => (b.leaderCumReturn ?? -999) - (a.leaderCumReturn ?? -999));
    chart.setOption({
      animationDuration: 300,
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        backgroundColor: 'rgba(255,255,255,0.96)',
        borderColor: '#D5D8DC',
        textStyle: { color: '#2C3E50', fontSize: 12 },
      },
      legend: { top: 0, textStyle: { color: '#34495E', fontSize: 12 } },
      grid: { left: 56, right: 24, top: 40, bottom: 86 },
      xAxis: {
        type: 'category',
        data: sorted.map((x) => x.name),
        axisLabel: { rotate: 42, color: '#5D6D7E', fontSize: 11 },
        axisLine: { lineStyle: { color: '#AAB7B8' } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        name: '区间累计涨跌 %',
        nameTextStyle: { color: '#7B7D7D', fontSize: 11 },
        splitLine: { lineStyle: { color: '#E5E8E8' } },
        axisLabel: { color: '#5D6D7E', fontSize: 11 },
      },
      series: [
        {
          name: '板块龙头',
          type: 'bar',
          data: sorted.map((x) => x.leaderCumReturn),
          itemStyle: { color: '#C0392B', borderRadius: [3, 3, 0, 0] },
          barMaxWidth: 18,
          markLine: benchmark == null ? undefined : {
            symbol: 'none',
            silent: true,
            label: {
              formatter: `沪深300 ${benchmark.toFixed(1)}%`,
              position: 'insideEndTop',
              color: '#34495E',
              fontSize: 11,
              backgroundColor: 'rgba(255,255,255,0.88)',
              padding: [2, 5],
              borderRadius: 3,
            },
            lineStyle: { color: '#34495E', type: 'dashed' },
            data: [{ yAxis: benchmark }],
          },
        },
        {
          name: '前五等权',
          type: 'bar',
          data: sorted.map((x) => x.avgCumReturn),
          itemStyle: { color: '#5DADE2', borderRadius: [3, 3, 0, 0] },
          barMaxWidth: 18,
        },
      ],
    });

    const handleClick = (params: { componentType?: string; name?: string }) => {
      if (params.componentType !== 'series' || !onSelect) return;
      const hit = sorted.find((x) => x.name === params.name);
      if (hit) onSelect(hit.code);
    };
    chart.on('click', handleClick);
    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
    };
  }, [items, benchmark, onSelect]);

  return <div ref={ref} style={{ width: '100%', height }} />;
}
