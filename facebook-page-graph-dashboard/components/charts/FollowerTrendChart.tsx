"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useChartTheme, formatNumber } from "./chartTheme";

interface DataPoint {
  date: string;
  followers: number;
  delta?: number | null;
}

interface Props {
  data: DataPoint[];
  height?: number;
}

export default function FollowerTrendChart({ data, height = 240 }: Props) {
  const t = useChartTheme();
  if (!data || data.length < 2) return null;

  const formatted = data.map((d) => ({
    ...d,
    label: d.date.slice(5), // MM-DD
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={formatted} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="gradFollowers" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={t.colors.purple} stopOpacity={0.25} />
            <stop offset="95%" stopColor={t.colors.purple} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={t.grid} vertical={false} />
        <XAxis
          dataKey="label"
          stroke={t.axis}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          minTickGap={24}
        />
        <YAxis
          stroke={t.axis}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={48}
          tickFormatter={(v) => formatNumber(v)}
        />
        <Tooltip
          contentStyle={{
            background: t.tooltipBg,
            border: `1px solid ${t.tooltipBorder}`,
            borderRadius: 8,
            fontSize: 12,
            color: t.text,
          }}
          labelStyle={{ color: t.text, fontWeight: 500 }}
          formatter={(v: any) => [formatNumber(v) + " followers", ""]}
          labelFormatter={(l: any) => `Ngày ${l}`}
        />
        <Area
          type="monotone"
          dataKey="followers"
          stroke={t.colors.purple}
          strokeWidth={2}
          fill="url(#gradFollowers)"
          dot={false}
          activeDot={{ r: 4, fill: t.colors.purple }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
