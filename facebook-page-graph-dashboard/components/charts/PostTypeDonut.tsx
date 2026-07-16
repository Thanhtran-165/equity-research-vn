"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { useChartTheme, formatNumber } from "./chartTheme";

interface Row {
  name: string;
  value: number;
}

interface Props {
  data: Row[];
  height?: number;
}

const TYPE_LABELS_VI: Record<string, string> = {
  text: "Text",
  photo: "Photo",
  video_or_reel: "Video / Reel",
  link: "Link",
  unknown: "Khác",
};

export default function PostTypeDonut({ data, height = 220 }: Props) {
  const t = useChartTheme();
  if (!data || data.length === 0) return null;

  const total = data.reduce((s, d) => s + d.value, 0);
  if (total === 0) return null;

  const formatted = data.map((d) => ({
    ...d,
    label: TYPE_LABELS_VI[d.name] ?? d.name,
  }));

  return (
    <div className="relative" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={formatted}
            dataKey="value"
            nameKey="label"
            cx="50%"
            cy="50%"
            innerRadius="58%"
            outerRadius="90%"
            paddingAngle={2}
            stroke="none"
          >
            {formatted.map((_, i) => (
              <Cell key={i} fill={t.palette[i % t.palette.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: t.tooltipBg,
              border: `1px solid ${t.tooltipBorder}`,
              borderRadius: 8,
              fontSize: 12,
              color: t.text,
            }}
            formatter={(v: any, n: any) => [
              `${formatNumber(v)} bài (${((v / total) * 100).toFixed(1)}%)`,
              n,
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
      {/* Center label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-2xl font-semibold tabular-nums">{total}</div>
        <div className="text-xs text-muted">bài viết</div>
      </div>
    </div>
  );
}
