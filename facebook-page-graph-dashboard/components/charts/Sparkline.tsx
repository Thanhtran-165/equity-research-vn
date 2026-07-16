"use client";

import React from "react";

interface Props {
  data: number[];
  width?: number;
  height?: number;
  className?: string;
  /** màu stroke tự xác định */
  color?: string;
  /** hiển thị dot ở điểm cuối */
  showDot?: boolean;
}

/**
 * Mini sparkline SVG thuần (không recharts) — nhẹ, dùng trong KPI cards.
 */
export default function Sparkline({
  data,
  width = 80,
  height = 24,
  className = "",
  color,
  showDot = true,
}: Props) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((v - min) / range) * (height - 4) - 2;
    return { x, y };
  });

  const path = pts
    .map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
    .join(" ");

  const last = pts[pts.length - 1];
  const first = pts[0];
  const isUp = data[data.length - 1] >= data[0];
  const strokeColor = color ?? (isUp ? "#10b981" : "#ef4444");
  const gradId = `spark-${Math.round(last.x)}-${Math.round(last.y)}-${data.length}`;

  const areaPath = `${path} L${width},${height} L0,${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      preserveAspectRatio="none"
      className={className}
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={strokeColor} stopOpacity="0.25" />
          <stop offset="100%" stopColor={strokeColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#${gradId})`} stroke="none" />
      <path
        d={path}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {showDot && (
        <circle cx={last.x} cy={last.y} r="1.5" fill={strokeColor} />
      )}
    </svg>
  );
}
