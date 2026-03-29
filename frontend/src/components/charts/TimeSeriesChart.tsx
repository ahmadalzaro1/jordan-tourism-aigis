"use client";

import { useMemo } from "react";
import { THEME } from "@/lib/constants";

interface TimeSeriesChartProps {
  data: Array<{ year: number; month: number; total: number }>;
  title: string;
  color?: string;
  height?: number;
  showForecast?: boolean;
  forecastData?: Array<{ date: string; predicted: number; lower_bound?: number; upper_bound?: number }>;
}

export default function TimeSeriesChart({
  data,
  title,
  color = THEME.accent,
  height = 150,
  showForecast = false,
  forecastData = [],
}: TimeSeriesChartProps) {
  const { points, labels, maxVal, forecastPoints, forecastLabels } = useMemo(() => {
    const pts = data.map(d => d.total);
    const lbls = data.map(d => `${d.year}-${String(d.month).padStart(2, "0")}`);
    const max = Math.max(...pts, 1);

    let fPts: number[] = [];
    let fLbls: string[] = [];
    if (showForecast && forecastData.length > 0) {
      fPts = forecastData.map(f => f.predicted);
      fLbls = forecastData.map(f => f.date.slice(0, 7));
    }

    return { points: pts, labels: lbls, maxVal: max, forecastPoints: fPts, forecastLabels: fLbls };
  }, [data, forecastData, showForecast]);

  const w = 360;
  const h = height;
  const pad = { top: 25, right: 10, bottom: 30, left: 50 };
  const chartW = w - pad.left - pad.right;
  const chartH = h - pad.top - pad.bottom;

  const allPoints = [...points, ...forecastPoints];
  const allMax = Math.max(...allPoints, 1);

  // Historical line
  const histLine = points.map((v, i) => {
    const x = pad.left + (i / Math.max(points.length - 1, 1)) * chartW;
    const y = pad.top + chartH - (v / allMax) * chartH;
    return `${x},${y}`;
  }).join(" ");

  // Forecast line (continues from last historical point)
  const lastHistX = pad.left + chartW;
  const lastHistY = points.length > 0 ? pad.top + chartH - (points[points.length - 1] / allMax) * chartH : pad.top;
  const forecastLine = forecastPoints.map((v, i) => {
    const x = lastHistX + ((i + 1) / forecastPoints.length) * (chartW * 0.3);
    const y = pad.top + chartH - (v / allMax) * chartH;
    return `${x},${y}`;
  }).join(" ");

  // X-axis labels (show every Nth)
  const labelStep = Math.max(1, Math.floor(labels.length / 6));
  const xLabels = labels.filter((_, i) => i % labelStep === 0);

  // Y-axis ticks
  const yTicks = [0, 0.25, 0.5, 0.75, 1].map(pct => ({
    y: pad.top + chartH - pct * chartH,
    label: formatNum(allMax * pct),
  }));

  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 11, color: THEME.textMuted, marginBottom: 4, textTransform: "uppercase" }}>
        {title}
      </div>
      <svg width={w} height={h} style={{ display: "block" }}>
        {/* Grid lines */}
        {yTicks.map((t, i) => (
          <g key={i}>
            <line x1={pad.left} y1={t.y} x2={w - pad.right} y2={t.y} stroke={THEME.border} strokeWidth={0.5} />
            <text x={pad.left - 5} y={t.y + 3} fill={THEME.textMuted} fontSize={8} textAnchor="end">{t.label}</text>
          </g>
        ))}

        {/* Historical line */}
        <polyline
          points={histLine}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* Historical dots */}
        {points.map((v, i) => {
          const x = pad.left + (i / Math.max(points.length - 1, 1)) * chartW;
          const y = pad.top + chartH - (v / allMax) * chartH;
          return <circle key={i} cx={x} cy={y} r={2.5} fill={color} />;
        })}

        {/* Forecast line (dashed) */}
        {showForecast && forecastLine && (
          <polyline
            points={`${lastHistX},${lastHistY} ${forecastLine}`}
            fill="none"
            stroke="#22c55e"
            strokeWidth={2}
            strokeDasharray="4,3"
            strokeLinejoin="round"
          />
        )}

        {/* X-axis labels */}
        {xLabels.map((lbl, i) => {
          const idx = labels.indexOf(lbl);
          const x = pad.left + (idx / Math.max(points.length - 1, 1)) * chartW;
          return (
            <text key={i} x={x} y={h - 5} fill={THEME.textMuted} fontSize={7} textAnchor="middle">
              {lbl.slice(2)}
            </text>
          );
        })}

        {/* Forecast label */}
        {showForecast && forecastData.length > 0 && (
          <text x={lastHistX + chartW * 0.15} y={pad.top - 8} fill="#22c55e" fontSize={8} textAnchor="middle">
            FORECAST
          </text>
        )}
      </svg>
    </div>
  );
}

function formatNum(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(0)}K`;
  return Math.round(n).toString();
}
