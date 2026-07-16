"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Moon, Sun, Menu } from "lucide-react";

interface Props {
  onSync?: () => void;
  syncing?: boolean;
  lastSyncLabel?: string | null;
  onOpenMobileNav?: () => void;
}

export default function Topbar({ onSync, syncing, lastSyncLabel, onOpenMobileNav }: Props) {
  const [isDark, setIsDark] = useState(false);

  // Init theme from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const dark = stored === "dark" || (!stored && prefersDark);
    setIsDark(dark);
    document.documentElement.classList.toggle("dark", dark);
  }, []);

  function toggleTheme() {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("theme", next ? "dark" : "light");
  }

  return (
    <header className="h-14 sticky top-0 z-30 bg-bg-1/60 backdrop-blur-xl border-b flex items-center gap-3 px-4 md:px-6" style={{ borderColor: "var(--border-soft)" }}>
      <button
        className="md:hidden btn-icon"
        onClick={onOpenMobileNav}
        aria-label="Mở menu"
      >
        <Menu className="w-5 h-5" />
      </button>

      <div className="flex-1" />

      {lastSyncLabel && (
        <span className="hidden sm:inline text-xs" style={{ color: "var(--text-faint)" }}>
          {lastSyncLabel}
        </span>
      )}

      {onSync && (
        <button
          onClick={onSync}
          disabled={syncing}
          className="btn-primary"
          title="Đồng bộ dữ liệu Facebook"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? "animate-spin" : ""}`} />
          <span className="hidden sm:inline">{syncing ? "Đang sync…" : "Sync"}</span>
        </button>
      )}

      <button
        onClick={toggleTheme}
        className="btn-icon"
        aria-label="Đổi theme"
        title="Dark / Light mode"
      >
        {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </button>
    </header>
  );
}
