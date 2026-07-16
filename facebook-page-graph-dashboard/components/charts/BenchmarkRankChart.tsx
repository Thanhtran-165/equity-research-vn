"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useChartTheme, formatNumber } from "./chartTheme";

interface Row {
  pageName: string;
  score: number | null;
  isOwn?: boolean;
}

interface Props {
  data: Row[];
  height?: number;
}

export default function BenchmarkRankChart({ data, height = 300 }: Props) {
  const t = useChartTheme();
  if (!data || data.length === 0) return null;

  const formatted = data
    .map((d) => ({
      ...d,
      pageNameShort: d.pageName.length > 20 ? d.pageName.slice(0, 19) + "…" : d.pageName,
      scoreValue: d.score ?? 0,
    }))
    .sort((a, b) => a.scoreValue - b.scoreValue); // nhỏ dưới, lớn trên

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={formatted}
        layout="vertical"
        margin={{ top: 4, right: 16, left: 4, bottom: 4 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={t.grid} horizontal={false} />
        <XAxis
          type="number"
          domain={[0, 100]}
          stroke={t.axis}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${v}`}
        />
        <YAxis
          type="category"
          dataKey="pageNameShort"
          stroke={t.axis}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={110}
        />
        <Tooltip
          contentStyle={{
            background: t.tooltipBg,
            border: `1px solid ${t.tooltipBorder}`,
            borderRadius: 8,
            fontSize: 12,
            color: t.text,
          }}
          cursor={{ fill: t.grid, opacity: 0.3 }}
          formatter={(v: any) => [`${formatNumber(v, 1)} / 100`, "Benchmark score"]}
        />
        <ReferenceLine x={50} stroke={t.axis} strokeDasharray="4 4" />
        <Bar dataKey="scoreValue" radius={[0, 4, 4, 0]} maxBarSize={22}>
          {formatted.map((d, i) => (
            <Cell
              key={i}
              fill={d.isOwn ? t.colors.purple : d.scoreValue >= 75 ? t.colors.green : d.scoreValue >= 50 ? t.colors.cyan : t.colors.amber}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
