import React from "react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

interface Props {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  delta?: number | null;
  /** Hiện màu xanh/đỏ theo delta (mặc định true) */
  colorDelta?: boolean;
  /** Hiện mũi tên theo delta */
  showArrow?: boolean;
  icon?: React.ReactNode;
  loading?: boolean;
  /** Sparkline data (số liệu mini) */
  spark?: number[];
  /** Badge hiển thị bên cạnh label (vd: "proxy") */
  badge?: React.ReactNode;
}

function deltaColor(d: number): string {
  if (d > 0) return "text-success-600 dark:text-success-500";
  if (d < 0) return "text-danger-600 dark:text-danger-500";
  return "text-slate-500";
}

function Sparkline({ data, className = "" }: { data: number[]; className?: string }) {
  if (!data || data.length < 2) return null;
  const w = 80;
  const h = 24;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const last = data[data.length - 1];
  const first = data[0];
  const up = last >= first;
  const stroke = up ? "#10b981" : "#ef4444";
  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      width={w}
      height={h}
      preserveAspectRatio="none"
      className={className}
    >
      <polyline
        points={pts}
        fill="none"
        stroke={stroke}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle
        cx={w}
        cy={h - ((last - min) / range) * h}
        r="1.6"
        fill={stroke}
      />
    </svg>
  );
}

export default function KpiCard({
  label,
  value,
  hint,
  delta,
  colorDelta = true,
  showArrow = true,
  icon,
  loading,
  spark,
  badge,
}: Props) {
  const hasDelta = typeof delta === "number";
  return (
    <div className="card p-4 flex flex-col gap-2 animate-fade-in">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          <span className="text-xs font-medium uppercase tracking-wide text-muted truncate">
            {label}
          </span>
          {badge}
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {icon && <span className="text-muted">{icon}</span>}
          {spark && <Sparkline data={spark} />}
        </div>
      </div>

      <div className="text-2xl font-semibold tabular-nums tracking-tight">
        {loading ? (
          <div className="skeleton h-7 w-20" />
        ) : (
          value
        )}
      </div>

      <div className="flex items-center gap-2 text-xs min-h-[16px]">
        {hasDelta && (
          <span
            className={`inline-flex items-center gap-0.5 font-medium ${
              colorDelta ? deltaColor(delta as number) : "text-muted"
            }`}
          >
            {showArrow && (delta as number) > 0 && <ArrowUpRight className="w-3 h-3" />}
            {showArrow && (delta as number) < 0 && <ArrowDownRight className="w-3 h-3" />}
            {(delta as number) > 0 ? "+" : ""}
            {(delta as number).toLocaleString("vi-VN")}
          </span>
        )}
        {hint && <span className="text-muted truncate">{hint}</span>}
      </div>
    </div>
  );
}
