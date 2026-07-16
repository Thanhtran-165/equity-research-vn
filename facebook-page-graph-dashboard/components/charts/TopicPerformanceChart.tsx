"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useChartTheme, formatNumber } from "./chartTheme";

interface Row {
  topic: string;
  topicLabel: string;
  reachTotal?: number | null;
  commentsTotal?: number | null;
  sharesTotal?: number | null;
  postsCount?: number;
}

interface Props {
  data: Row[];
  metric?: "reach" | "comments" | "shares";
  height?: number;
}

export default function TopicPerformanceChart({
  data,
  metric = "reach",
  height = 260,
}: Props) {
  const t = useChartTheme();
  if (!data || data.length === 0) return null;

  const dataKey =
    metric === "reach" ? "reachTotal" : metric === "comments" ? "commentsTotal" : "sharesTotal";
  const labelMap = { reach: "Reach", comments: "Comments", shares: "Shares" };

  const formatted = data
    .filter((d) => (d as any)[dataKey] != null)
    .map((d) => ({
      ...d,
      value: (d as any)[dataKey] ?? 0,
    }))
    .sort((a, b) => b.value - a.value);

  if (formatted.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={formatted}
        layout="vertical"
        margin={{ top: 4, right: 12, left: 4, bottom: 4 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={t.grid} horizontal={false} />
        <XAxis
          type="number"
          stroke={t.axis}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => formatNumber(v)}
        />
        <YAxis
          type="category"
          dataKey="topicLabel"
          stroke={t.axis}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={92}
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
          formatter={(v: any) => [formatNumber(v), labelMap[metric]]}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={26}>
          {formatted.map((_, i) => (
            <Cell key={i} fill={t.palette[i % t.palette.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
