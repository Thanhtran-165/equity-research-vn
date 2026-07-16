"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useChartTheme, formatNumber } from "./chartTheme";

interface Row {
  label: string;
  reactions?: number;
  comments?: number;
  shares?: number;
}

interface Props {
  data: Row[];
  height?: number;
}

export default function EngagementTrendChart({ data, height = 240 }: Props) {
  const t = useChartTheme();
  if (!data || data.length < 2) return null;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={t.grid} vertical={false} />
        <XAxis
          dataKey="label"
          stroke={t.axis}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          minTickGap={20}
        />
        <YAxis
          stroke={t.axis}
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={40}
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
          formatter={(v: any, n: any) => [formatNumber(v), n]}
        />
        <Line
          type="monotone"
          dataKey="reactions"
          name="Reactions"
          stroke={t.colors.purple}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 3 }}
        />
        <Line
          type="monotone"
          dataKey="comments"
          name="Comments"
          stroke={t.colors.amber}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 3 }}
        />
        <Line
          type="monotone"
          dataKey="shares"
          name="Shares"
          stroke={t.colors.green}
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
