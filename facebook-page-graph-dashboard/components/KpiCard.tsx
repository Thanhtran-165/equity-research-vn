import React from "react";

interface Props {
  label: string;
  value: React.ReactNode;
  hint?: React.ReactNode;
  delta?: number | null;
  icon?: React.ReactNode;
  loading?: boolean;
}

function formatDelta(d: number): { text: string; cls: string } {
  const sign = d > 0 ? "+" : "";
  return {
    text: `${sign}${d.toLocaleString("vi-VN")}`,
    cls: d > 0 ? "text-green-600" : d < 0 ? "text-red-600" : "text-gray-500",
  };
}

export default function KpiCard({ label, value, hint, delta, icon, loading }: Props) {
  const d = typeof delta === "number" ? formatDelta(delta) : null;
  return (
    <div className="card p-4 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wide text-gray-500">{label}</span>
        {icon && <span className="text-gray-400">{icon}</span>}
      </div>
      <div className="text-2xl font-semibold">
        {loading ? (
          <span className="inline-block w-20 h-7 rounded bg-gray-200 animate-pulse" />
        ) : (
          value
        )}
      </div>
      <div className="text-xs text-gray-500 flex items-center gap-2">
        {d && <span className={`font-medium ${d.cls}`}>{d.text}</span>}
        {hint && <span>{hint}</span>}
      </div>
    </div>
  );
}
