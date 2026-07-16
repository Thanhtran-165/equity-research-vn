"use client";

import React from "react";

export interface SegmentedOption<T extends string> {
  value: T;
  label: React.ReactNode;
}

interface Props<T extends string> {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (v: T) => void;
  size?: "sm" | "md";
  className?: string;
}

export default function Segmented<T extends string>({
  options,
  value,
  onChange,
  size = "md",
  className = "",
}: Props<T>) {
  return (
    <div
      className={`inline-flex items-center bg-slate-100 dark:bg-slate-800 rounded-lg p-0.5 ${className}`}
    >
      {options.map((opt) => {
        const active = opt.value === value;
        return (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={`
              ${size === "sm" ? "px-2 py-1 text-xs" : "px-3 py-1.5 text-sm"}
              rounded-md font-medium transition-colors whitespace-nowrap
              ${active
                ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 shadow-sm"
                : "text-muted hover:text-slate-700 dark:hover:text-slate-200"
              }
            `}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
