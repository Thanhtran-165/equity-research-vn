"use client";

import { useEffect, useState } from "react";

/**
 * Chart theme — Fintech Neon palette.
 * Inspired by _viz-shared/tokens.css chart palette.
 */
export function useChartTheme() {
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const el = document.documentElement;
    const update = () => setIsDark(!el.classList.contains("light"));
    update();
    const obs = new MutationObserver(update);
    obs.observe(el, { attributes: true, attributeFilter: ["class"] });
    return () => obs.disconnect();
  }, []);

  return {
    isDark,
    grid: isDark ? "rgba(139,92,246,0.06)" : "rgba(139,92,246,0.1)",
    axis: "#8b8ba7",
    text: "#8b8ba7",
    tooltipBg: isDark ? "rgba(28,28,48,0.95)" : "#ffffff",
    tooltipBorder: isDark ? "rgba(139,92,246,0.3)" : "#e2e8f0",
    // Neon palette
    colors: {
      purple: "#a855f7",
      pink: "#ec4899",
      cyan: "#06b6d4",
      green: "#10d98a",
      red: "#ff4d6d",
      amber: "#fbbf24",
      purple2: "#8b5cf6",
    },
    // Sequential palette for multi-series charts
    palette: [
      "#a855f7", // purple
      "#ec4899", // pink
      "#06b6d4", // cyan
      "#10d98a", // green
      "#fbbf24", // amber
      "#8b5cf6", // purple2
      "#ff4d6d", // red
      "#6366f1", // indigo
    ],
  };
}

export function formatNumber(n: number, digits = 0): string {
  if (Math.abs(n) >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (Math.abs(n) >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return n.toLocaleString("vi-VN", { maximumFractionDigits: digits });
}

export function formatPercent(n: number, digits = 2): string {
  return `${(n * 100).toFixed(digits)}%`;
}
