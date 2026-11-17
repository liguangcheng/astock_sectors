import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import type { PricedSeries } from '../types';

export const SERIES_COLORS = ['#C0392B', '#2471A3', '#1E8449', '#B7950B', '#6C3483'];

interface Props {
  months: string[];
  series: PricedSeries[];
  mode: 'price' | 'norm';
  height?: number;
  onSelect?: (code: string) => void;
}

export default function LineChart({ months, series, mode, height = 460, onSelect }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current, undefined, { renderer: 'canvas' });
    chartRef.current = chart;
    const onResize = () => chart.resize();
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;
    const stocks = series.filter((s) => !s.isBenchmark);
    const bench = series.find((s) => s.isBenchmark);
    const colorOf = (code: string) => SERIES_COLORS[stocks.findIndex((s) => s.code === code) % SERIES_COLORS.length];

    const seriesOption: echarts.SeriesOption[] = stocks.map((s, idx) => ({
      name: s.name,
      type: 'line' as const,
      data: s.series.map((p) => (mode === 'price' ? p.close : p.norm)),
      smooth: false,
      showSymbol: false,
      symbolSize: 5,
      lineStyle: { width: idx === 0 ? 2.8 : 1.8, color: colorOf(s.code) },
      itemStyle: { color: colorOf(s.code) },
      emphasis: { focus: 'series' as const },
      connectNulls: true,
      z: 3,
    }));

    if (bench && mode === 'norm') {
      seriesOption.push({
        name: bench.name,
        type: 'line',
        data: bench.series.map((p) => p.norm),
        smooth: false,
        showSymbol: false,
        lineStyle: { width: 1.6, type: 'dashed', color: '#7F8C8D' },
        itemStyle: { color: '#7F8C8D' },
        connectNulls: true,
        z: 2,
      } as echarts.SeriesOption);
    }

    chart.setOption(
      {
        animationDuration: 300,
        color: [...SERIES_COLORS, '#7F8C8D'],
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(255,255,255,0.96)',
          borderColor: '#D5D8DC',
          textStyle: { color: '#2C3E50', fontSize: 12 },
          valueFormatter: (v: unknown) => (v == null ? '—' : mode === 'price' ? `${Number(v).toFixed(2)} 元` : `${Number(v).toFixed(1)}`),
        },
        legend: {
          top: 4,
          left: 0,
          itemWidth: 18,
          itemHeight: 8,
          textStyle: { color: '#34495E', fontSize: 12 },
        },
        grid: { left: 86, right: 28, top: 58, bottom: 58 },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: months,
          axisLine: { lineStyle: { color: '#AAB7B8' } },
          axisLabel: { color: '#5D6D7E', fontSize: 11, hideOverlap: true },
          axisTick: { show: false },
        },
        yAxis: {
          type: 'value',
          name: mode === 'price' ? '月末收盘价（元）' : '2023-12 = 100',
          nameGap: 16,
          nameTextStyle: { color: '#7B7D7D', fontSize: 11, align: 'left', padding: [0, 0, 8, -60] },
          splitLine: { lineStyle: { color: '#E5E8E8' } },
          axisLabel: { color: '#5D6D7E', fontSize: 11 },
        },
        dataZoom: [
          { type: 'inside', start: 0, end: 100 },
          { type: 'slider', height: 18, bottom: 14, borderColor: '#D5D8DC', fillerColor: 'rgba(36,113,163,0.12)' },
        ],
        series: seriesOption,
      },
      { notMerge: true },
    );

    chart.off('click');
    chart.on('click', (params: { componentType?: string; seriesName?: string }) => {
      if (params.componentType !== 'series' || !onSelect) return;
      const hit = stocks.find((s) => s.name === params.seriesName);
      if (hit) onSelect(hit.code);
    });
  }, [months, series, mode, onSelect]);

  return <div ref={ref} style={{ width: '100%', height }} />;
}
